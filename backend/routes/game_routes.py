"""
Game API Routes
Handles game creation, moves, observations, and state queries
"""
from fastapi import APIRouter, HTTPException, Depends
from backend.models.game_models import (
    MoveRequest, MoveResponse, ObserveRequest, ObserveResponse,
    GameState, ValidMovesResponse, QuantumEvent,
    ObserverMoveRequest, ObserverMoveResponse, ObservationZoneResponse,
    ObserverStatsResponse, AffectedPiece, CollapsedPieceInfo
)
from backend.core.quantum_engine import QuantumEngine
from backend.core.chess_rules import ChessRules
from backend.core.game_state import GameStateManager
from backend.core.observer_engine import ObserverEngine
from backend.db.neo4j_client import Neo4jClient
from backend.config import settings
from backend.utils.logger_factory import get_module_logger, log_game_event, log_error_with_analysis, debug_trace
from backend.utils.exceptions import (
    GameNotFoundError, PieceNotFoundError, InvalidMoveError, 
    QuantumStateError, TurnOrderError, ObservationError, GameStateError
)
from typing import List, Dict, Any
import logging

logger = get_module_logger()

router = APIRouter(prefix="/game", tags=["game"])

# Dependency injection for database and engines
def get_db():
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    try:
        yield db
    finally:
        db.close()


@router.post("/new", response_model=dict)
async def create_game(
    queue_id: str = None,
    queue_name: str = None,
    white_player: str = "White",
    black_player: str = "Black",
    db: Neo4jClient = Depends(get_db)
):
    """
    Create a new quantum chess game

    Args:
        queue_id: Optional existing queue ID. If not provided, creates new queue.
        queue_name: Optional name for new queue (ignored if queue_id provided)
        white_player: Name of white player
        black_player: Name of black player

    Returns:
        {
          "game_id": "uuid",
          "queue_id": "uuid",
          "message": "New game created",
          "initial_state": GameState
        }
    """
    try:
        debug_trace(f"Starting game creation in queue {queue_id}")

        game_state_manager = GameStateManager(db)

        # Create game in specified or new queue
        game_id = game_state_manager.initialize_board(queue_id, white_player, black_player)

        # Get queue ID (either provided or newly created)
        if not queue_id:
            # Find the queue that contains this game
            queue_query = """
            MATCH (q:GameQueue)-[:CONTAINS_GAME]->(g:Game {id: $game_id})
            RETURN q.id as queue_id, q.name as queue_name
            """
            queue_result = db.execute_query(queue_query, {'game_id': game_id})
            if queue_result:
                queue_id = queue_result[0]['queue_id']
                queue_name = queue_result[0]['queue_name']

        initial_state = game_state_manager.get_board_state(game_id)

        log_game_event(logger, "game_created", f"New game initialized with ID {game_id} in queue {queue_id}",
                     game_id=game_id, queue_id=queue_id)
        logger.info(f"Game created successfully: {game_id} in queue {queue_id}")

        return {
            "game_id": game_id,
            "queue_id": queue_id,
            "queue_name": queue_name,
            "message": "New game created successfully",
            "initial_state": initial_state.model_dump() if initial_state else None
        }
    except Exception as e:
        log_error_with_analysis(
            logger,
            f"Failed to create game: {e}",
            "Database connection issue or board initialization failure",
            "Check Neo4j connection and retry game creation"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{game_id}", response_model=GameState)
async def get_state(game_id: str, db: Neo4jClient = Depends(get_db)):
    """
    Get current game state
    
    Returns complete game state including all pieces and quantum states
    """
    try:
        game_state_manager = GameStateManager(db)
        state = game_state_manager.get_board_state(game_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get game state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move", response_model=MoveResponse)
async def make_move(move: MoveRequest, db: Neo4jClient = Depends(get_db)):
    """
    Make a chess move (may trigger quantum effects)

    Processes move validation, quantum mechanics, and state updates
    """
    try:
        debug_trace(f"Processing move request: {move.from_square} -> {move.to_square} by {move.player}")
        quantum_engine = QuantumEngine(db)
        chess_rules = ChessRules(db)
        game_state_manager = GameStateManager(db)

        # Validate game exists
        game_info = game_state_manager.get_game_info(move.game_id)
        if not game_info:
            log_error_with_analysis(
                logger,
                f"Move failed: Game {move.game_id} not found",
                "Game ID does not exist in database",
                "Verify game ID and ensure game was created properly"
            )
            raise GameNotFoundError(move.game_id)

        # Validate it's the player's turn
        if game_info.active_player != move.player:
            raise TurnOrderError(move.game_id, game_info.active_player, move.player)

        # Get piece at from_square
        from_query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece)-[:BELONGS_TO]->(g)
        WHERE p.captured = false AND p.color = $player
        MATCH (p)-[:OCCUPIES]->(pos:Position {square: $from_square, is_ghost: false})
        RETURN p.id AS piece_id, p.type AS piece_type, p.quantum_ability AS quantum_ability
        """

        from_results = db.execute_query(from_query, {
            'game_id': move.game_id,
            'from_square': move.from_square,
            'player': move.player
        })

        if not from_results:
            log_error_with_analysis(
                logger,
                f"Move failed: No {move.player} piece at {move.from_square}",
                "Requested square is empty or occupied by opponent piece",
                "Select a valid piece to move"
            )
            raise HTTPException(
                status_code=400,
                detail=f"No {move.player} piece at {move.from_square}"
            )

        piece_id = from_results[0]['piece_id']
        piece_type = from_results[0]['piece_type']
        quantum_ability = from_results[0]['quantum_ability']

        logger.info(f"Move validation: {piece_type} {piece_id} ({move.from_square} -> {move.to_square})")

        # Validate move legality
        is_valid, error = chess_rules.is_valid_move(
            move.game_id,
            piece_id,
            move.from_square,
            move.to_square
        )

        if not is_valid:
            log_error_with_analysis(
                logger,
                f"Move validation failed: {error}",
                f"Invalid {piece_type} move pattern or path obstruction",
                "Choose a different destination square"
            )
            raise HTTPException(status_code=400, detail=error)

        quantum_events: List[QuantumEvent] = []
        move_type = "classical"

        # Check if move triggers superposition
        if quantum_ability and quantum_engine.should_trigger_superposition(
            piece_type,
            move.from_square,
            move.to_square
        ):
            logger.info(f"Quantum superposition triggered for {piece_id}")
            # Create superposition
            superposition_event = quantum_engine.create_superposition(
                piece_id,
                move.from_square,
                move.to_square,
                move.game_id
            )
            quantum_events.append(QuantumEvent(**superposition_event))
            move_type = "quantum_split"
        else:
            # Classical move
            logger.debug(f"Classical move for {piece_id}")
            # Check for capture
            to_query = """
            MATCH (g:Game {id: $game_id})
            MATCH (p:Piece)-[:BELONGS_TO]->(g)
            WHERE p.captured = false
            MATCH (p)-[:OCCUPIES]->(pos:Position {square: $to_square, is_ghost: false})
            RETURN p.id AS captured_piece_id, p.color AS captured_color
            """

            to_results = db.execute_query(to_query, {
                'game_id': move.game_id,
                'to_square': move.to_square
            })

            if to_results:
                # Capture
                captured_id = to_results[0]['captured_piece_id']
                game_state_manager.capture_piece(captured_id, piece_id, move.game_id)
                move_type = "capture"
                logger.info(f"Piece capture: {piece_id} captured {captured_id}")

            # Update position
            game_state_manager.update_piece_position(
                piece_id,
                move.from_square,
                move.to_square,
                move.game_id
            )

        # Check for new entanglements
        entanglement_events = quantum_engine.check_for_entanglement(move.game_id)
        quantum_events.extend([QuantumEvent(**e) for e in entanglement_events])

        # Check for auto-collapses
        auto_collapse_events = quantum_engine.check_auto_collapses(move.game_id)
        quantum_events.extend([QuantumEvent(**e) for e in auto_collapse_events])

        # Advance turn
        game_state_manager.advance_turn(move.game_id)

        # Get new state
        new_state = game_state_manager.get_board_state(move.game_id)

        log_game_event(
            logger,
            "move_executed",
            f"{move.player} moved {piece_type} {move.from_square} -> {move.to_square}",
            move_type=move_type,
            quantum_events=len(quantum_events),
            game_id=move.game_id
        )

        # Record move in storage system
        try:
            from backend.core.game_storage import GameStorageManager
            storage = GameStorageManager(db)

            move_data = {
                'from_square': move.from_square,
                'to_square': move.to_square,
                'player': move.player,
                'piece_type': piece_type,
                'move_type': move_type,
                'quantum_events': [event.model_dump() for event in quantum_events],
                'turn_number': game_info.current_turn if game_info else 1,
                'board_state': new_state.model_dump() if new_state else None
            }

            storage.add_move_to_game(move.game_id, move_data)
            logger.debug(f"Move recorded in storage system for game {move.game_id}")

        except Exception as storage_error:
            logger.warning(f"Failed to record move in storage system: {storage_error}")
            # Don't fail the move if storage recording fails

        return MoveResponse(
            success=True,
            move_type=move_type,
            new_state=new_state,
            quantum_events=quantum_events,
            message=f"Move executed: {move.from_square} -> {move.to_square}"
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error_with_analysis(
            logger,
            f"Move execution failed: {e}",
            "Unexpected error during move processing",
            "Check server logs and retry the move"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/observe", response_model=ObserveResponse)
async def observe_piece(observe_req: ObserveRequest, db: Neo4jClient = Depends(get_db)):
    """
    Observe (collapse) a quantum piece

    Uses one observation token and collapses superposition
    """
    try:
        debug_trace(f"Processing observation request for piece {observe_req.piece_id} by {observe_req.player}")
        quantum_engine = QuantumEngine(db)
        game_state_manager = GameStateManager(db)

        # Check observation tokens
        game_info = game_state_manager.get_game_info(observe_req.game_id)
        if not game_info:
            log_error_with_analysis(
                logger,
                f"Observation failed: Game {observe_req.game_id} not found",
                "Game ID does not exist in database",
                "Verify game ID and ensure game was created properly"
            )
            raise HTTPException(status_code=404, detail="Game not found")

        obs_remaining = (game_info.white_observations_left
                        if observe_req.player == 'white'
                        else game_info.black_observations_left)

        if obs_remaining <= 0:
            log_error_with_analysis(
                logger,
                f"Observation failed: No observations remaining for {observe_req.player}",
                "Player has exhausted observation tokens for this turn",
                "Wait for next turn to get new observation tokens"
            )
            raise HTTPException(
                status_code=400,
                detail="No observations remaining this turn"
            )

        logger.info(f"Observation attempt: {observe_req.player} observing {observe_req.piece_id}")

        # Collapse superposition
        collapsed_pos, cascade_events = quantum_engine.collapse_superposition(
            observe_req.piece_id,
            observe_req.game_id
        )

        # Decrement observation token
        game_state_manager.decrement_observation(observe_req.game_id, observe_req.player)

        # Get new state
        new_state = game_state_manager.get_board_state(observe_req.game_id)

        log_game_event(
            logger,
            "observation_executed",
            f"{observe_req.player} observed {observe_req.piece_id}, collapsed to {collapsed_pos}",
            cascade_events=len(cascade_events),
            game_id=observe_req.game_id
        )

        return ObserveResponse(
            success=True,
            collapsed_position=collapsed_pos,
            new_state=new_state,
            cascade_events=[QuantumEvent(**e) for e in cascade_events]
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error_with_analysis(
            logger,
            f"Observation failed: {e}",
            "Piece may not be in superposition state or database error occurred",
            "Ensure piece is in superposition before attempting observation"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/valid-moves/{game_id}/{piece_id}", response_model=ValidMovesResponse)
async def get_valid_moves(
    game_id: str,
    piece_id: str,
    db: Neo4jClient = Depends(get_db)
):
    """
    Get all valid moves for a piece
    
    Returns regular moves, quantum-triggering moves, and capture moves
    """
    try:
        chess_rules = ChessRules(db)
        moves = chess_rules.get_valid_moves(game_id, piece_id)
        
        return ValidMovesResponse(
            piece_id=piece_id,
            valid_moves=moves['valid_moves'],
            quantum_moves=moves['quantum_moves'],
            capture_moves=moves['capture_moves']
        )
        
    except Exception as e:
        logger.error(f"Failed to get valid moves: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== OBSERVER ENDPOINTS ====================

@router.post("/move/observer", response_model=ObserverMoveResponse)
async def move_observer(
    move_req: ObserverMoveRequest,
    db: Neo4jClient = Depends(get_db)
):
    """
    Move Observer piece and trigger automatic observation
    
    Request body:
        {
          "game_id": "uuid",
          "observer_id": "observer-w-1",
          "to_square": "e5"
        }
    
    Returns:
        {
          "success": true,
          "new_position": "e5",
          "observed_pieces": ["knight-w-1", "pawn-b-3"],
          "collapsed_states": [
            {
              "piece_id": "knight-w-1",
              "from_state": "superposed",
              "to_position": "d4"
            },
            {
              "piece_id": "pawn-b-3",
              "from_state": "entangled",
              "to_state": "classical"
            }
          ],
          "new_state": { ... }
        }
    """
    try:
        observer_engine = ObserverEngine(db)
        game_state_manager = GameStateManager(db)
        
        # Validate Observer exists
        observer_pos = observer_engine.get_observer_current_position(move_req.observer_id)
        if not observer_pos:
            raise HTTPException(status_code=404, detail="Observer not found")
        
        # Validate move is legal
        valid_moves = observer_engine.get_valid_moves(move_req.observer_id, move_req.game_id)
        if move_req.to_square not in valid_moves:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid move. Valid moves: {valid_moves}"
            )
        
        # Execute move and observation
        result = observer_engine.move_observer(
            move_req.observer_id,
            move_req.to_square,
            move_req.game_id
        )
        
        # Get updated game state
        new_state = game_state_manager.get_board_state(move_req.game_id)
        
        # Advance turn
        game_state_manager.advance_turn(move_req.game_id)
        
        return ObserverMoveResponse(
            success=result['success'],
            new_position=result['new_position'],
            observed_pieces=result['observed_pieces'],
            collapsed_states=[CollapsedPieceInfo(**cs) for cs in result['collapsed_states']],
            new_state=new_state
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Observer move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/observer/{observer_id}/zone", response_model=ObservationZoneResponse)
async def get_observation_zone(
    observer_id: str,
    game_id: str,
    db: Neo4jClient = Depends(get_db)
):
    """
    Get list of squares in Observer's current observation zone
    
    Query params:
        game_id: Current game ID
    
    Returns:
        {
          "observer_id": "observer-w-1",
          "current_position": "e4",
          "zone_squares": ["d3", "d4", "d5", "e3", "e4", "e5", "f3", "f4", "f5"],
          "affected_pieces": [
            {
              "piece_id": "knight-w-1",
              "current_state": "superposed",
              "will_collapse": true,
              "position": "d4"
            }
          ]
        }
    """
    try:
        observer_engine = ObserverEngine(db)
        
        # Get Observer position
        current_pos = observer_engine.get_observer_current_position(observer_id)
        if not current_pos:
            raise HTTPException(status_code=404, detail="Observer not found")
        
        # Get observation zone
        zone_squares = observer_engine.get_observation_zone_preview(observer_id, game_id)
        
        # Get affected pieces
        affected_pieces = observer_engine.get_affected_pieces_in_zone(observer_id, game_id)
        
        return ObservationZoneResponse(
            observer_id=observer_id,
            current_position=current_pos,
            zone_squares=zone_squares,
            affected_pieces=[AffectedPiece(**ap) for ap in affected_pieces]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get observation zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Game Storage Management Endpoints

@router.post("/queue/new", response_model=dict)
async def create_game_queue(
    name: str = None,
    metadata: Dict[str, Any] = None,
    db: Neo4jClient = Depends(get_db)
):
    """
    Create a new game queue (session/tournament)

    Args:
        name: Optional name for the queue
        metadata: Additional metadata for the queue

    Returns:
        {
          "queue_id": "uuid",
          "queue_name": "string",
          "message": "Queue created successfully"
        }
    """
    try:
        debug_trace(f"Creating game queue: {name}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        queue_id = storage.create_game_queue(name, metadata)

        # Get queue info
        queue_query = """
        MATCH (q:GameQueue {id: $queue_id})
        RETURN q.name as queue_name
        """
        result = db.execute_query(queue_query, {'queue_id': queue_id})
        queue_name = result[0]['queue_name'] if result else name

        logger.info(f"Game queue created: {queue_id}")
        return {
            "queue_id": queue_id,
            "queue_name": queue_name,
            "message": "Game queue created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create game queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/{queue_id}/games", response_model=List[Dict[str, Any]])
async def get_games_in_queue(queue_id: str, db: Neo4jClient = Depends(get_db)):
    """
    Get all games in a specific queue

    Returns:
        List of game data with metadata
    """
    try:
        debug_trace(f"Retrieving games in queue {queue_id}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        games = storage.get_games_in_queue(queue_id)

        logger.debug(f"Retrieved {len(games)} games from queue {queue_id}")
        return games
    except Exception as e:
        logger.error(f"Failed to get games in queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/{game_id}/moves", response_model=List[Dict[str, Any]])
async def get_moves_in_game(game_id: str, db: Neo4jClient = Depends(get_db)):
    """
    Get all moves in a specific game, ordered by sequence

    Returns:
        List of move data with full metadata
    """
    try:
        debug_trace(f"Retrieving moves in game {game_id}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        moves = storage.get_moves_in_game(game_id)

        logger.debug(f"Retrieved {len(moves)} moves from game {game_id}")
        return moves
    except Exception as e:
        logger.error(f"Failed to get moves in game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/player/{player_name}/games", response_model=List[Dict[str, Any]])
async def get_player_games(
    player_name: str,
    limit: int = 50,
    db: Neo4jClient = Depends(get_db)
):
    """
    Get all games for a specific player across all queues

    Args:
        player_name: Player name to search for
        limit: Maximum number of games to return (default: 50)

    Returns:
        List of game data with queue information
    """
    try:
        debug_trace(f"Retrieving games for player {player_name}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        games = storage.get_player_games(player_name, limit)

        logger.debug(f"Retrieved {len(games)} games for player {player_name}")
        return games
    except Exception as e:
        logger.error(f"Failed to get player games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/{queue_id}/stats", response_model=Dict[str, Any])
async def get_queue_stats(queue_id: str, db: Neo4jClient = Depends(get_db)):
    """
    Get comprehensive statistics for a queue

    Returns:
        Dictionary with queue statistics including game counts, move counts, etc.
    """
    try:
        debug_trace(f"Getting stats for queue {queue_id}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        stats = storage.get_queue_stats(queue_id)

        logger.debug(f"Retrieved stats for queue {queue_id}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/game/{game_id}/end", response_model=dict)
async def end_game(
    game_id: str,
    outcome: str,
    winner: str = None,
    end_reason: str = "normal",
    db: Neo4jClient = Depends(get_db)
):
    """
    Mark a game as completed

    Args:
        game_id: Game to end
        outcome: 'checkmate', 'resignation', 'stalemate', 'timeout', etc.
        winner: Winning player ('white', 'black', or None for draw)
        end_reason: Reason for game end

    Returns:
        {
          "success": true,
          "message": "Game ended successfully"
        }
    """
    try:
        debug_trace(f"Ending game {game_id} with outcome: {outcome}")

        from backend.core.game_storage import GameStorageManager
        storage = GameStorageManager(db)

        success = storage.end_game(game_id, outcome, winner, end_reason)

        if success:
            log_game_event(logger, "game_ended", f"Game {game_id} ended with {outcome}",
                         game_id=game_id, outcome=outcome, winner=winner)
            logger.info(f"Game {game_id} ended successfully")
            return {
                "success": True,
                "message": "Game ended successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Game not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/observer/{observer_id}/stats", response_model=ObserverStatsResponse)
async def get_observer_stats(
    observer_id: str,
    db: Neo4jClient = Depends(get_db)
):
    """
    Get Observer statistics
    
    Returns:
        {
          "observations_made": 15,
          "total_pieces_affected": 12,
          "observation_history": [
            {
              "piece_id": "knight-w-1",
              "turn": 5,
              "state": "superposed"
            }
          ]
        }
    """
    try:
        observer_engine = ObserverEngine(db)
        stats = observer_engine.get_observer_stats(observer_id)
        
        return ObserverStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get observer stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

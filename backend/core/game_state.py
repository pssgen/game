"""
Game State Manager
Handles game initialization, board state queries, and turn management
"""
from typing import Dict, List, Optional
from backend.db.neo4j_client import Neo4jClient
from backend.models.game_models import GameState, GameInfo, PieceData, PositionData
from backend.core.game_storage import GameStorageManager
from datetime import datetime
import uuid
from backend.utils.logger_factory import get_module_logger, debug_trace, log_game_event

logger = get_module_logger()


class GameStateManager:
    """Manages complete game state and board initialization"""

    def __init__(self, db: Neo4jClient):
        self.db = db
        self.storage = GameStorageManager(db)
        logger.info("GameStateManager initialized with GameStorageManager")

    def initialize_board(self, queue_id: str = None, white_player: str = "White",
                        black_player: str = "Black") -> str:
        """
        Create a new game with all pieces in starting positions

        Args:
            queue_id: Optional queue ID. If None, creates a default queue.
            white_player: Name of white player
            black_player: Name of black player

        Returns:
            game_id: UUID of created game
        """
        debug_trace(f"Initializing new game board in queue {queue_id}")

        # Create default queue if none provided
        if not queue_id:
            queue_id = self.storage.create_game_queue("Default Session")
            logger.info(f"Created default queue: {queue_id}")

        # Create game in the queue
        game_id = self.storage.create_game_in_queue(queue_id, white_player, black_player)

        # Create all 64 squares as position nodes
        self._create_position_nodes()
        
        # Create all 32 pieces
        self._create_pieces(game_id)
        
        log_game_event(
            logger,
            "game_initialized",
            f"New game {game_id} initialized with standard chess setup",
            game_id=game_id
        )
        
        return game_id
    
    def _create_position_nodes(self):
        """Create all 64 chess board positions"""
        debug_trace("Creating position nodes for chess board")
        
        squares = []
        for file in 'abcdefgh':
            for rank in range(1, 9):
                squares.append(f"{file}{rank}")
        
        query = """
        UNWIND $squares AS square
        MERGE (pos:Position {square: square})
        ON CREATE SET pos.probability = 1.0,
                      pos.is_ghost = false,
                      pos.turn_created = 0
        """
        
        self.db.execute_write(query, {'squares': squares})
        logger.debug(f"Created {len(squares)} position nodes")
    
    def _create_pieces(self, game_id: str):
        """Create all 32 pieces in starting positions (with Observers replacing e2/e7 pawns)"""
        debug_trace(f"Creating pieces for game {game_id}")
        
        pieces_config = [
            # White pieces
            ('rook-w-1', 'rook', 'white', 'a1', False),
            ('knight-w-1', 'knight', 'white', 'b1', True),
            ('bishop-w-1', 'bishop', 'white', 'c1', False),
            ('queen-w-1', 'queen', 'white', 'd1', False),
            ('king-w-1', 'king', 'white', 'e1', False),
            ('bishop-w-2', 'bishop', 'white', 'f1', False),
            ('knight-w-2', 'knight', 'white', 'g1', True),
            ('rook-w-2', 'rook', 'white', 'h1', False),
            # White pawns (e2 replaced by Observer)
            ('pawn-w-1', 'pawn', 'white', 'a2', True),
            ('pawn-w-2', 'pawn', 'white', 'b2', True),
            ('pawn-w-3', 'pawn', 'white', 'c2', True),
            ('pawn-w-4', 'pawn', 'white', 'd2', True),
            ('observer-w-1', 'observer', 'white', 'e2', False),  # Observer replaces e2 pawn
            ('pawn-w-6', 'pawn', 'white', 'f2', True),
            ('pawn-w-7', 'pawn', 'white', 'g2', True),
            ('pawn-w-8', 'pawn', 'white', 'h2', True),
            
            # Black pieces
            ('rook-b-1', 'rook', 'black', 'a8', False),
            ('knight-b-1', 'knight', 'black', 'b8', True),
            ('knight-b-2', 'knight', 'black', 'g8', True),
            ('bishop-b-1', 'bishop', 'black', 'c8', False),
            ('queen-b-1', 'queen', 'black', 'd8', False),
            ('king-b-1', 'king', 'black', 'e8', False),
            ('bishop-b-2', 'bishop', 'black', 'f8', False),
            ('rook-b-2', 'rook', 'black', 'h8', False),
            # Black pawns (e7 replaced by Observer)
            ('pawn-b-1', 'pawn', 'black', 'a7', True),
            ('pawn-b-2', 'pawn', 'black', 'b7', True),
            ('pawn-b-3', 'pawn', 'black', 'c7', True),
            ('pawn-b-4', 'pawn', 'black', 'd7', True),
            ('observer-b-1', 'observer', 'black', 'e7', False),  # Observer replaces e7 pawn
            ('pawn-b-6', 'pawn', 'black', 'f7', True),
            ('pawn-b-7', 'pawn', 'black', 'g7', True),
            ('pawn-b-8', 'pawn', 'black', 'h7', True),
        ]
        
        query = """
        MATCH (g:Game {id: $game_id})
        UNWIND $pieces AS piece_data
        
        CREATE (p:Piece {
          id: piece_data.id,
          type: piece_data.type,
          color: piece_data.color,
          quantum_ability: piece_data.quantum_ability,
          quantum_state: 'classical',
          captured: false,
          move_count: 0,
          created_turn: 0,
          observations_made: CASE WHEN piece_data.type = 'observer' THEN 0 ELSE null END,
          observation_range: CASE WHEN piece_data.type = 'observer' THEN 1 ELSE null END
        })
        
        CREATE (p)-[:BELONGS_TO]->(g)
        
        WITH p, piece_data
        MATCH (pos:Position {square: piece_data.start_square})
        CREATE (p)-[:OCCUPIES {since_turn: 0}]->(pos)
        """
        
        pieces_list = [
            {
                'id': pid,
                'type': ptype,
                'color': color,
                'start_square': square,
                'quantum_ability': quantum
            }
            for pid, ptype, color, square, quantum in pieces_config
        ]
        
        self.db.execute_write(query, {
            'game_id': game_id,
            'pieces': pieces_list
        })
        
        logger.info(f"Created 32 pieces for game {game_id} (including 2 observers)")
    
    def get_board_state(self, game_id: str) -> Optional[GameState]:
        """
        Get complete game state including all pieces and positions
        
        Returns:
            GameState object or None if game not found
        """
        debug_trace(f"Retrieving board state for game {game_id}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece)-[:BELONGS_TO]->(g)
        WHERE p.captured = false
        
        OPTIONAL MATCH (p)-[:OCCUPIES]->(pos:Position)
        OPTIONAL MATCH (p)-[:ENTANGLED_WITH]-(partner:Piece)
        
        RETURN g, p, collect(DISTINCT pos) AS positions, collect(DISTINCT partner.id) AS entangled_ids
        """
        
        results = self.db.execute_query(query, {'game_id': game_id})
        
        if not results:
            logger.warning(f"Game {game_id} not found")
            return None
        
        logger.debug(f"Retrieved board state with {len(results)} pieces")
        
        # Extract game info from first result
        game_data = dict(results[0]['g'])
        game_info = GameInfo(
            id=game_data['id'],
            current_turn=game_data['current_turn'],
            active_player=game_data['active_player'],
            status=game_data['status'],
            white_observations_left=game_data['white_observations_left'],
            black_observations_left=game_data['black_observations_left'],
            created_at=game_data.get('created_at')
        )
        
        # Extract pieces
        pieces = []
        for record in results:
            piece_dict = dict(record['p'])
            positions_list = [
                PositionData(
                    square=dict(pos)['square'],
                    probability=dict(pos).get('probability', 1.0),
                    is_ghost=dict(pos).get('is_ghost', False)
                )
                for pos in record['positions']
            ]
            
            piece = PieceData(
                id=piece_dict['id'],
                type=piece_dict['type'],
                color=piece_dict['color'],
                quantum_ability=piece_dict['quantum_ability'],
                quantum_state=piece_dict['quantum_state'],
                captured=piece_dict['captured'],
                move_count=piece_dict['move_count'],
                positions=positions_list,
                entangled_with=[eid for eid in record['entangled_ids'] if eid]
            )
            pieces.append(piece)
        
        return GameState(game=game_info, pieces=pieces)
    
    def advance_turn(self, game_id: str):
        """Advance to next turn and switch active player"""
        debug_trace(f"Advancing turn for game {game_id}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        SET g.current_turn = g.current_turn + 1,
            g.active_player = CASE g.active_player 
                WHEN 'white' THEN 'black'
                ELSE 'white'
            END,
            g.white_observations_left = CASE g.active_player
                WHEN 'black' THEN 1
                ELSE g.white_observations_left
            END,
            g.black_observations_left = CASE g.active_player
                WHEN 'white' THEN 1
                ELSE g.black_observations_left
            END
        RETURN g
        """
        
        self.db.execute_write(query, {'game_id': game_id})
        logger.info(f"Advanced turn for game {game_id}")
        
        log_game_event(
            logger,
            "turn_advanced",
            f"Turn advanced in game {game_id}",
            game_id=game_id
        )
    
    def decrement_observation(self, game_id: str, player: str):
        """Decrease observation token count for player"""
        debug_trace(f"Decrementing observation for {player} in game {game_id}")
        
        field = f"{player}_observations_left"
        
        query = f"""
        MATCH (g:Game {{id: $game_id}})
        SET g.{field} = g.{field} - 1
        RETURN g
        """
        
        self.db.execute_write(query, {'game_id': game_id})
        logger.info(f"Decremented observation count for {player} in game {game_id}")
        
        log_game_event(
            logger,
            "observation_used",
            f"Player {player} used an observation in game {game_id}",
            game_id=game_id,
            player=player
        )
    
    def update_piece_position(
        self,
        piece_id: str,
        from_square: str,
        to_square: str,
        game_id: str
    ):
        """Update piece position (classical move)"""
        debug_trace(f"Updating position for {piece_id}: {from_square} -> {to_square}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece {id: $piece_id})-[old_occ:OCCUPIES]->(:Position {square: $from_square})
        MATCH (new_pos:Position {square: $to_square})
        
        DELETE old_occ
        CREATE (p)-[:OCCUPIES {since_turn: g.current_turn}]->(new_pos)
        
        SET p.move_count = p.move_count + 1
        
        RETURN p
        """
        
        self.db.execute_write(query, {
            'game_id': game_id,
            'piece_id': piece_id,
            'from_square': from_square,
            'to_square': to_square
        })
        
        logger.info(f"Updated position for {piece_id}: {from_square} -> {to_square}")
        
        log_game_event(
            logger,
            "piece_moved",
            f"Piece {piece_id} moved from {from_square} to {to_square}",
            game_id=game_id,
            piece_id=piece_id,
            from_square=from_square,
            to_square=to_square
        )
    
    def capture_piece(self, piece_id: str, captured_by: str, game_id: str):
        """Mark piece as captured"""
        debug_trace(f"Processing capture: {piece_id} captured by {captured_by}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (victim:Piece {id: $piece_id})
        MATCH (attacker:Piece {id: $captured_by})
        MATCH (victim)-[occ:OCCUPIES]->(pos:Position)
        
        SET victim.captured = true
        DELETE occ
        
        CREATE (attacker)-[:CAPTURED {
          turn: g.current_turn,
          square: pos.square,
          was_quantum: victim.quantum_state <> 'classical'
        }]->(victim)
        
        RETURN victim
        """
        
        self.db.execute_write(query, {
            'game_id': game_id,
            'piece_id': piece_id,
            'captured_by': captured_by
        })
        
        logger.info(f"Piece {piece_id} captured by {captured_by}")
        
        log_game_event(
            logger,
            "piece_captured",
            f"Piece {piece_id} captured by {captured_by}",
            game_id=game_id,
            piece_id=piece_id,
            captured_by=captured_by
        )
    
    def get_game_info(self, game_id: str) -> Optional[GameInfo]:
        """Get game metadata without pieces"""
        debug_trace(f"Retrieving game info for {game_id}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        RETURN g
        """
        
        results = self.db.execute_query(query, {'game_id': game_id})
        
        if results:
            game_data = dict(results[0]['g'])
            logger.debug(f"Retrieved game info for {game_id}")
            return GameInfo(
                id=game_data['id'],
                current_turn=game_data['current_turn'],
                active_player=game_data['active_player'],
                status=game_data['status'],
                white_observations_left=game_data['white_observations_left'],
                black_observations_left=game_data['black_observations_left'],
                created_at=game_data.get('created_at')
            )
        
        logger.warning(f"Game {game_id} not found")
        return None

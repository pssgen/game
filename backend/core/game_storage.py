"""
Game Storage Manager
Handles GameQueue -> Game -> Move hierarchy for Quantum Chess
Provides comprehensive game storage with metadata and efficient querying
"""
from typing import Dict, List, Optional, Any
from backend.db.neo4j_client import Neo4jClient
from backend.models.game_models import GameState, MoveRequest
from datetime import datetime
import uuid
import json
from backend.utils.logger_factory import get_module_logger, debug_trace, log_game_event, log_error_with_analysis

logger = get_module_logger()


class GameStorageManager:
    """
    Manages the complete game storage hierarchy:
    GameQueue -> Game -> Move relationships with full metadata
    """

    def __init__(self, db: Neo4jClient):
        self.db = db
        logger.info("GameStorageManager initialized")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for efficient querying"""
        debug_trace("Ensuring database indexes for game storage")

        indexes = [
            "CREATE INDEX game_queue_id IF NOT EXISTS FOR (q:GameQueue) ON (q.id)",
            "CREATE INDEX game_id IF NOT EXISTS FOR (g:Game) ON (g.id)",
            "CREATE INDEX move_id IF NOT EXISTS FOR (m:Move) ON (m.id)",
            "CREATE INDEX game_created_at IF NOT EXISTS FOR (g:Game) ON (g.created_at)",
            "CREATE INDEX move_sequence IF NOT EXISTS FOR (m:Move) ON (m.sequence_number)",
        ]

        try:
            with self.db.driver.session() as session:
                for index_query in indexes:
                    try:
                        session.run(index_query)
                    except Exception as e:
                        logger.warning(f"Index creation failed (may already exist): {e}")
            logger.debug("Database indexes ensured")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def create_game_queue(self, queue_name: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new game queue (session/tournament)

        Args:
            queue_name: Optional name for the queue
            metadata: Additional metadata (tournament info, etc.)

        Returns:
            queue_id: Unique identifier for the queue
        """
        debug_trace(f"Creating new game queue: {queue_name}")

        queue_id = f"queue-{uuid.uuid4()}"
        queue_name = queue_name or f"Queue-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        metadata = metadata or {}
        metadata.update({
            'created_at': datetime.now().isoformat(),
            'total_games': 0,
            'active_games': 0,
            'completed_games': 0
        })

        query = """
        CREATE (q:GameQueue {
          id: $queue_id,
          name: $queue_name,
          created_at: datetime(),
          total_games: 0,
          active_games: 0,
          completed_games: 0
        })
        """

        # Add additional metadata properties if provided
        if metadata:
            for key, value in metadata.items():
                if key not in ['created_at', 'total_games', 'active_games', 'completed_games']:
                    query = query.replace("})", f", {key}: ${key}}})")

        query += " RETURN q"

        try:
            parameters = {
                'queue_id': queue_id,
                'queue_name': queue_name
            }

            # Add metadata parameters
            if metadata:
                for key, value in metadata.items():
                    if key not in ['created_at', 'total_games', 'active_games', 'completed_games']:
                        parameters[key] = value

            self.db.execute_write(query, parameters)

            log_game_event(logger, "queue_created", f"Game queue created: {queue_name}", queue_id=queue_id)
            logger.info(f"Game queue created successfully: {queue_id} ({queue_name})")
            return queue_id

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to create game queue: {e}",
                "Database write operation failed",
                "Check Neo4j connection and retry"
            )
            raise

    def create_game_in_queue(self, queue_id: str, white_player: str = "White",
                           black_player: str = "Black", metadata: Dict[str, Any] = None) -> str:
        """
        Create a new game within a specific queue

        Args:
            queue_id: Parent queue ID
            white_player: White player name
            black_player: Black player name
            metadata: Additional game metadata

        Returns:
            game_id: Unique identifier for the game
        """
        debug_trace(f"Creating new game in queue {queue_id}")

        game_id = f"game-{uuid.uuid4()}"

        metadata = metadata or {}
        metadata.update({
            'created_at': datetime.now().isoformat(),
            'white_player': white_player,
            'black_player': black_player,
            'status': 'active',
            'current_turn': 1,
            'active_player': 'white',
            'white_observations_left': 1,
            'black_observations_left': 1,
            'total_moves': 0,
            'start_time': datetime.now().isoformat()
        })

        query = f"""
        MATCH (q:GameQueue {{id: $queue_id}})
        CREATE (q)-[:CONTAINS_GAME]->(g:Game {{
          id: $game_id,
          white_player: $white_player,
          black_player: $black_player,
          status: 'active',
          current_turn: 1,
          active_player: 'white',
          white_observations_left: 1,
          black_observations_left: 1,
          total_moves: 0,
          created_at: datetime(),
          start_time: datetime()
        }})
        SET q.total_games = COALESCE(q.total_games, 0) + 1,
            q.active_games = COALESCE(q.active_games, 0) + 1
        RETURN g
        """

        try:
            result = self.db.execute_write(query, {
                'queue_id': queue_id,
                'game_id': game_id,
                'white_player': white_player,
                'black_player': black_player
            })

            if not result:
                raise ValueError(f"Queue {queue_id} not found")

            log_game_event(logger, "game_created", f"Game created in queue {queue_id}",
                         game_id=game_id, queue_id=queue_id)
            logger.info(f"Game created successfully: {game_id} in queue {queue_id}")
            return game_id

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to create game in queue: {e}",
                "Queue not found or database write failed",
                "Verify queue exists and check Neo4j connection"
            )
            raise

    def add_move_to_game(self, game_id: str, move_data: Dict[str, Any]) -> str:
        """
        Add a move to an existing game

        Args:
            game_id: Game ID to add move to
            move_data: Move information including from_square, to_square, player, etc.

        Returns:
            move_id: Unique identifier for the move
        """
        debug_trace(f"Adding move to game {game_id}")

        move_id = f"move-{uuid.uuid4()}"

        # Get current move count for sequence number
        sequence_query = """
        MATCH (g:Game {id: $game_id})
        OPTIONAL MATCH (g)-[:HAS_MOVE]->(m:Move)
        RETURN COUNT(m) as move_count
        """

        try:
            sequence_result = self.db.execute_query(sequence_query, {'game_id': game_id})
            if not sequence_result:
                raise ValueError(f"Game {game_id} not found")

            sequence_number = sequence_result[0]['move_count'] + 1

            # Prepare move metadata
            move_metadata = {
                'id': move_id,
                'sequence_number': sequence_number,
                'timestamp': datetime.now().isoformat(),
                'move_type': move_data.get('move_type', 'standard'),
                'from_square': move_data.get('from_square'),
                'to_square': move_data.get('to_square'),
                'player': move_data.get('player'),
                'piece_type': move_data.get('piece_type'),
                'quantum_events': move_data.get('quantum_events', []),
                'board_state': move_data.get('board_state'),
                'turn_number': move_data.get('turn_number', sequence_number)
            }

            # Add move to game
            move_query = """
            MATCH (g:Game {id: $game_id})
            CREATE (g)-[:HAS_MOVE]->(m:Move {
              id: $move_id,
              sequence_number: $sequence_number,
              timestamp: datetime(),
              move_type: $move_type,
              from_square: $from_square,
              to_square: $to_square,
              player: $player,
              piece_type: $piece_type,
              quantum_events: $quantum_events,
              board_state: $board_state,
              turn_number: $turn_number
            })
            SET g.total_moves = COALESCE(g.total_moves, 0) + 1,
                g.last_move_at = datetime()
            RETURN m
            """

            self.db.execute_write(move_query, {
                'game_id': game_id,
                'move_id': move_id,
                'sequence_number': sequence_number,
                'move_type': move_data.get('move_type', 'standard'),
                'from_square': move_data.get('from_square'),
                'to_square': move_data.get('to_square'),
                'player': move_data.get('player'),
                'piece_type': move_data.get('piece_type'),
                'quantum_events': move_data.get('quantum_events', []),
                'board_state': move_data.get('board_state'),
                'turn_number': move_data.get('turn_number', sequence_number)
            })

            log_game_event(logger, "move_recorded", f"Move {sequence_number} recorded in game {game_id}",
                         game_id=game_id, move_id=move_id, sequence_number=sequence_number)
            logger.info(f"Move recorded: {move_id} (#{sequence_number}) in game {game_id}")
            return move_id

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to add move to game: {e}",
                "Game not found or invalid move data",
                "Verify game exists and move data is valid"
            )
            raise

    def end_game(self, game_id: str, outcome: str, winner: str = None,
                end_reason: str = "normal", metadata: Dict[str, Any] = None) -> bool:
        """
        Mark a game as completed

        Args:
            game_id: Game to end
            outcome: 'checkmate', 'resignation', 'stalemate', 'timeout', etc.
            winner: Winning player ('white', 'black', or None for draw)
            end_reason: Reason for game end
            metadata: Additional end-game metadata

        Returns:
            success: True if game ended successfully
        """
        debug_trace(f"Ending game {game_id} with outcome: {outcome}")

        end_metadata = metadata or {}
        end_metadata.update({
            'outcome': outcome,
            'winner': winner,
            'end_reason': end_reason,
            'end_time': datetime.now().isoformat(),
            'duration_minutes': None  # Could calculate from start_time
        })

        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (g)<-[:CONTAINS_GAME]-(q:GameQueue)
        SET g.status = 'completed',
            g.outcome = $outcome,
            g.winner = $winner,
            g.end_reason = $end_reason,
            g.completed_at = datetime()
        SET q.active_games = COALESCE(q.active_games, 0) - 1,
            q.completed_games = COALESCE(q.completed_games, 0) + 1
        RETURN g, q
        """

        try:
            result = self.db.execute_write(query, {
                'game_id': game_id,
                'outcome': outcome,
                'winner': winner,
                'end_reason': end_reason
            })

            if not result:
                raise ValueError(f"Game {game_id} not found")

            log_game_event(logger, "game_ended", f"Game {game_id} ended with {outcome}",
                         game_id=game_id, outcome=outcome, winner=winner)
            logger.info(f"Game {game_id} ended: {outcome} (winner: {winner})")
            return True

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to end game: {e}",
                "Game not found or invalid end data",
                "Verify game exists and end data is valid"
            )
            raise

    def get_games_in_queue(self, queue_id: str) -> List[Dict[str, Any]]:
        """
        Get all games in a specific queue

        Args:
            queue_id: Queue ID to query

        Returns:
            List of game data dictionaries
        """
        debug_trace(f"Retrieving games in queue {queue_id}")

        query = """
        MATCH (q:GameQueue {id: $queue_id})-[:CONTAINS_GAME]->(g:Game)
        OPTIONAL MATCH (g)-[:HAS_MOVE]->(m:Move)
        WITH g, COUNT(m) as move_count
        RETURN {
          id: g.id,
          metadata: {
            white_player: g.white_player,
            black_player: g.black_player,
            status: g.status,
            current_turn: g.current_turn,
            active_player: g.active_player,
            white_observations_left: g.white_observations_left,
            black_observations_left: g.black_observations_left,
            total_moves: g.total_moves,
            created_at: g.created_at,
            start_time: g.start_time
          },
          move_count: move_count
        } as game_data
        ORDER BY g.created_at DESC
        """

        try:
            result = self.db.execute_query(query, {'queue_id': queue_id})
            games = [record['game_data'] for record in result] if result else []

            logger.debug(f"Found {len(games)} games in queue {queue_id}")
            return games

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to get games in queue: {e}",
                "Queue not found or database query failed",
                "Verify queue exists and check Neo4j connection"
            )
            raise

    def get_moves_in_game(self, game_id: str) -> List[Dict[str, Any]]:
        """
        Get all moves in a specific game, ordered by sequence

        Args:
            game_id: Game ID to query

        Returns:
            List of move data dictionaries, ordered by sequence
        """
        debug_trace(f"Retrieving moves in game {game_id}")

        query = """
        MATCH (g:Game {id: $game_id})-[:HAS_MOVE]->(m:Move)
        RETURN {
          id: m.id,
          metadata: {
            sequence_number: m.sequence_number,
            timestamp: m.timestamp,
            move_type: m.move_type,
            from_square: m.from_square,
            to_square: m.to_square,
            player: m.player,
            piece_type: m.piece_type,
            quantum_events: m.quantum_events,
            board_state: m.board_state,
            turn_number: m.turn_number
          }
        } as move_data
        ORDER BY m.sequence_number ASC
        """

        try:
            result = self.db.execute_query(query, {'game_id': game_id})
            moves = [record['move_data'] for record in result] if result else []

            logger.debug(f"Found {len(moves)} moves in game {game_id}")
            return moves

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to get moves in game: {e}",
                "Game not found or database query failed",
                "Verify game exists and check Neo4j connection"
            )
            raise

    def get_player_games(self, player_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all games for a specific player across all queues

        Args:
            player_name: Player name to search for
            limit: Maximum number of games to return

        Returns:
            List of game data with queue information
        """
        debug_trace(f"Retrieving games for player {player_name}")

        query = """
        MATCH (q:GameQueue)-[:CONTAINS_GAME]->(g:Game)
        WHERE g.white_player = $player_name OR g.black_player = $player_name
        OPTIONAL MATCH (g)-[:HAS_MOVE]->(m:Move)
        WITH q, g, COUNT(m) as move_count
        RETURN {
          queue_id: q.id,
          queue_name: q.name,
          game_id: g.id,
          game_metadata: {
            white_player: g.white_player,
            black_player: g.black_player,
            status: g.status,
            current_turn: g.current_turn,
            active_player: g.active_player,
            white_observations_left: g.white_observations_left,
            black_observations_left: g.black_observations_left,
            total_moves: g.total_moves,
            created_at: g.created_at,
            start_time: g.start_time
          },
          move_count: move_count,
          player_role: CASE
            WHEN g.white_player = $player_name THEN 'white'
            ELSE 'black'
            END
        } as game_data
        ORDER BY g.created_at DESC
        LIMIT $limit
        """

        try:
            result = self.db.execute_query(query, {'player_name': player_name, 'limit': limit})
            games = [record['game_data'] for record in result] if result else []

            logger.debug(f"Found {len(games)} games for player {player_name}")
            return games

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to get player games: {e}",
                "Database query failed",
                "Check Neo4j connection and try again"
            )
            raise

    def get_queue_stats(self, queue_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a queue

        Args:
            queue_id: Queue ID to analyze

        Returns:
            Dictionary with queue statistics
        """
        debug_trace(f"Getting stats for queue {queue_id}")

        query = """
        MATCH (q:GameQueue {id: $queue_id})
        OPTIONAL MATCH (q)-[:CONTAINS_GAME]->(g:Game)
        WITH q, COUNT(DISTINCT g) as total_games,
             COUNT(DISTINCT CASE WHEN g.status = 'active' THEN g END) as active_games,
             COUNT(DISTINCT CASE WHEN g.status = 'completed' THEN g END) as completed_games
        OPTIONAL MATCH (q)-[:CONTAINS_GAME]->(g2:Game)-[:HAS_MOVE]->(m:Move)
        WITH q, total_games, active_games, completed_games, COUNT(DISTINCT m) as total_moves
        RETURN {
          queue_id: q.id,
          queue_name: q.name,
          total_games: total_games,
          active_games: active_games,
          completed_games: completed_games,
          total_moves: total_moves,
          average_moves_per_game: CASE WHEN total_games > 0 THEN toFloat(total_moves) / total_games ELSE 0 END,
          created_at: q.created_at
        } as stats
        """

        try:
            result = self.db.execute_query(query, {'queue_id': queue_id})
            stats = result[0]['stats'] if result else None

            if stats:
                logger.debug(f"Queue {queue_id} stats: {stats['total_games']} games, {stats['total_moves']} moves")
                return stats
            else:
                raise ValueError(f"Queue {queue_id} not found")

        except Exception as e:
            log_error_with_analysis(
                logger,
                f"Failed to get queue stats: {e}",
                "Queue not found or database query failed",
                "Verify queue exists and check Neo4j connection"
            )
            raise

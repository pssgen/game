"""
Observer Engine
Handles Observer piece movement (king-pattern), automatic observation,
quantum state collapse, and entanglement breaking.
"""
from typing import List, Dict, Tuple, Optional
from backend.db.neo4j_client import Neo4jClient
from backend.utils.logger_factory import get_module_logger, debug_trace, log_game_event

logger = get_module_logger()


class ObserverEngine:
    """
    Manages Observer piece mechanics:
    - King-pattern movement (1 square in 8 directions)
    - Automatic observation of quantum pieces in range
    - Collapse of superposed states
    - Breaking of entanglement relationships
    """
    
    def __init__(self, db: Neo4jClient):
        self.db = db
        self.observation_range = 1  # King-move radius (8 surrounding squares)
        logger.info("ObserverEngine initialized with observation range: 1 square")
    
    def get_valid_moves(self, observer_id: str, game_id: str) -> List[str]:
        """
        Get valid moves for Observer (king-pattern movement)
        
        Args:
            observer_id: ID of the Observer piece
            game_id: Current game ID
            
        Returns:
            List of valid square names (e.g., ['d3', 'd4', 'd5', ...])
        """
        debug_trace(f"Getting valid moves for observer {observer_id}")
        
        query = """
        MATCH (obs:Piece {id: $observer_id})-[:OCCUPIES]->(pos:Position)
        
        // Calculate all 8 surrounding squares
        WITH obs, pos,
          substring(pos.square, 0, 1) AS file,
          toInteger(substring(pos.square, 1, 1)) AS rank
        
        // Generate surrounding positions (king-pattern)
        UNWIND [
          {df: -1, dr: -1}, {df: -1, dr: 0}, {df: -1, dr: 1},
          {df: 0,  dr: -1},                  {df: 0,  dr: 1},
          {df: 1,  dr: -1}, {df: 1,  dr: 0}, {df: 1,  dr: 1}
        ] AS delta
        
        WITH obs, file, rank, delta,
          char(ascii(file) + delta.df) AS new_file,
          rank + delta.dr AS new_rank
        
        WHERE new_file >= 'a' AND new_file <= 'h'
          AND new_rank >= 1 AND new_rank <= 8
        
        WITH obs, new_file + toString(new_rank) AS target_square
        
        // Check if square is occupied by own piece
        OPTIONAL MATCH (blocker:Piece)-[:OCCUPIES]->(target_pos:Position {square: target_square})
        WHERE blocker.color = obs.color AND blocker.captured = false
        
        WITH target_square, blocker
        WHERE blocker IS NULL
        
        RETURN collect(target_square) AS valid_moves
        """
        
        result = self.db.execute_query(query, {
            'observer_id': observer_id,
            'game_id': game_id
        })
        
        valid_moves = result[0]['valid_moves'] if result else []
        logger.debug(f"Found {len(valid_moves)} valid moves for observer {observer_id}: {valid_moves}")
        
        return valid_moves
    
    def move_observer(self, observer_id: str, to_square: str, game_id: str) -> Dict:
        """
        Move Observer and trigger automatic observation
        
        Args:
            observer_id: ID of the Observer piece
            to_square: Destination square
            game_id: Current game ID
            
        Returns:
            {
              "success": True,
              "new_position": "e5",
              "observed_pieces": ["knight-w-1", "pawn-b-3"],
              "collapsed_states": [
                {"piece_id": "knight-w-1", "from_state": "superposed", "to_position": "d4"},
                {"piece_id": "pawn-b-3", "from_state": "entangled", "to_state": "classical"}
              ]
            }
        """
        debug_trace(f"Moving observer {observer_id} to {to_square}")
        
        # Get current turn
        turn_query = """
        MATCH (g:Game {id: $game_id})
        RETURN g.current_turn AS turn
        """
        turn_result = self.db.execute_query(turn_query, {'game_id': game_id})
        current_turn = turn_result[0]['turn'] if turn_result else 1
        
        # Move Observer
        move_query = """
        MATCH (obs:Piece {id: $observer_id})-[old_occ:OCCUPIES]->(old_pos:Position)
        MATCH (new_pos:Position {square: $to_square})
        
        DELETE old_occ
        CREATE (obs)-[:OCCUPIES {since_turn: $turn}]->(new_pos)
        
        SET obs.move_count = obs.move_count + 1
        
        RETURN obs
        """
        
        self.db.execute_write(move_query, {
            'observer_id': observer_id,
            'to_square': to_square,
            'turn': current_turn
        })
        
        logger.info(f"Observer {observer_id} moved to {to_square}")
        
        log_game_event(
            logger,
            "observer_moved",
            f"Observer {observer_id} moved to {to_square}",
            game_id=game_id,
            observer_id=observer_id,
            to_square=to_square
        )
        
        # Trigger automatic observation
        observation_result = self.observe_surrounding_area(observer_id, game_id)
        
        return {
            "success": True,
            "new_position": to_square,
            "observed_pieces": observation_result['observed_pieces'],
            "collapsed_states": observation_result['collapsed_states']
        }
    
    def observe_surrounding_area(self, observer_id: str, game_id: str) -> Dict:
        """
        Automatically observe all quantum pieces in 8-square radius
        
        Args:
            observer_id: ID of the Observer piece
            game_id: Current game ID
            
        Returns:
            {
              'observed_pieces': ["piece-1", "piece-2"],
              'collapsed_states': [...]
            }
        """
        debug_trace(f"Observer {observer_id} observing surrounding area")
        
        # Import here to avoid circular dependency
        from backend.core.quantum_engine import QuantumEngine
        quantum_engine = QuantumEngine(self.db)
        
        # Find nearby quantum pieces
        nearby_pieces = self._find_nearby_quantum_pieces(observer_id, game_id)
        
        collapsed_states = []
        observed_pieces = []
        
        logger.info(f"Observer {observer_id} found {len(nearby_pieces)} nearby quantum pieces")
        
        for piece_data in nearby_pieces:
            piece_id = piece_data['id']
            piece_state = piece_data['quantum_state']
            
            if piece_state == 'superposed':
                # Collapse superposition
                try:
                    collapsed_pos, cascade_events = quantum_engine.collapse_superposition(piece_id, game_id)
                    collapsed_states.append({
                        'piece_id': piece_id,
                        'from_state': 'superposed',
                        'to_position': collapsed_pos
                    })
                    observed_pieces.append(piece_id)
                    logger.info(f"Observer collapsed {piece_id} from superposition to {collapsed_pos}")
                    
                    # Log cascade effects
                    if cascade_events:
                        logger.info(f"Cascade effects from {piece_id} collapse: {len(cascade_events)} events")
                        
                except Exception as e:
                    logger.error(f"Failed to collapse {piece_id}: {e}")
            
            elif piece_state == 'entangled':
                # Break entanglement
                try:
                    partners = quantum_engine.get_entangled_partners(piece_id)
                    for partner_id in partners:
                        quantum_engine.break_entanglement(piece_id, partner_id)
                    
                    collapsed_states.append({
                        'piece_id': piece_id,
                        'from_state': 'entangled',
                        'to_state': 'classical'
                    })
                    observed_pieces.append(piece_id)
                    logger.info(f"Observer broke entanglement for {piece_id}")
                except Exception as e:
                    logger.error(f"Failed to break entanglement for {piece_id}: {e}")
        
        # Record observations in Neo4j
        if observed_pieces:
            self._record_observations(observer_id, observed_pieces, game_id)
            logger.info(f"Observer {observer_id} completed observation of {len(observed_pieces)} pieces")
            
            log_game_event(
                logger,
                "observation_completed",
                f"Observer {observer_id} observed {len(observed_pieces)} quantum pieces",
                game_id=game_id,
                observer_id=observer_id,
                observed_pieces=observed_pieces,
                collapsed_states=len(collapsed_states)
            )
        else:
            logger.debug(f"Observer {observer_id} found no quantum pieces to observe")
        
        return {
            'observed_pieces': observed_pieces,
            'collapsed_states': collapsed_states
        }
    
    def _find_nearby_quantum_pieces(self, observer_id: str, game_id: str) -> List[Dict]:
        """
        Query Neo4j for quantum pieces within observation range
        
        Returns:
            List of piece dictionaries with id and quantum_state
        """
        debug_trace(f"Finding quantum pieces near observer {observer_id}")
        
        query = """
        MATCH (obs:Piece {id: $observer_id})-[:OCCUPIES]->(obs_pos:Position)
        MATCH (target:Piece)-[:OCCUPIES]->(target_pos:Position)
        WHERE target.captured = false
          AND target.id <> obs.id
          AND target.quantum_state IN ['superposed', 'entangled']
        
        WITH obs, target, obs_pos, target_pos,
          abs(ascii(substring(obs_pos.square, 0, 1)) - 
              ascii(substring(target_pos.square, 0, 1))) AS file_dist,
          abs(toInteger(substring(obs_pos.square, 1, 1)) - 
              toInteger(substring(target_pos.square, 1, 1))) AS rank_dist
        
        WHERE file_dist <= 1 AND rank_dist <= 1
        
        RETURN target.id AS id, target.quantum_state AS quantum_state
        """
        
        result = self.db.execute_query(query, {
            'observer_id': observer_id,
            'game_id': game_id
        })
        
        pieces = result if result else []
        logger.debug(f"Found {len(pieces)} quantum pieces near observer {observer_id}")
        
        return pieces
    
    def _record_observations(self, observer_id: str, target_ids: List[str], game_id: str):
        """
        Create OBSERVED relationships in Neo4j
        """
        debug_trace(f"Recording observations by {observer_id} of {len(target_ids)} pieces")
        
        if not target_ids:
            return
        
        query = """
        MATCH (obs:Piece {id: $observer_id})
        MATCH (g:Game {id: $game_id})
        
        // Update observation count
        SET obs.observations_made = COALESCE(obs.observations_made, 0) + size($target_ids)
        
        WITH obs, g
        UNWIND $target_ids AS target_id
        MATCH (target:Piece {id: target_id})
        
        CREATE (obs)-[:OBSERVED {
          turn: g.current_turn,
          target_state: target.quantum_state,
          forced: true
        }]->(target)
        """
        
        self.db.execute_write(query, {
            'observer_id': observer_id,
            'target_ids': target_ids,
            'game_id': game_id
        })
        
        logger.debug(f"Recorded {len(target_ids)} observations by {observer_id}")
        
        logger.info(f"Recorded {len(target_ids)} observations for {observer_id}")
    
    def get_observation_zone_preview(self, observer_id: str, game_id: str) -> List[str]:
        """
        Get list of squares in Observer's current observation zone
        (for UI highlighting)
        
        Returns:
            List of square names including center square
        """
        debug_trace(f"Getting observation zone preview for observer {observer_id}")
        
        query = """
        MATCH (obs:Piece {id: $observer_id})-[:OCCUPIES]->(pos:Position)
        
        WITH pos,
          substring(pos.square, 0, 1) AS file,
          toInteger(substring(pos.square, 1, 1)) AS rank
        
        UNWIND [
          {df: -1, dr: -1}, {df: -1, dr: 0}, {df: -1, dr: 1},
          {df: 0,  dr: -1}, {df: 0,  dr: 0}, {df: 0,  dr: 1},
          {df: 1,  dr: -1}, {df: 1,  dr: 0}, {df: 1,  dr: 1}
        ] AS delta
        
        WITH file, rank, delta,
          char(ascii(file) + delta.df) AS new_file,
          rank + delta.dr AS new_rank
        
        WHERE new_file >= 'a' AND new_file <= 'h'
          AND new_rank >= 1 AND new_rank <= 8
        
        RETURN collect(new_file + toString(new_rank)) AS zone_squares
        """
        
        result = self.db.execute_query(query, {'observer_id': observer_id})
        zone_squares = result[0]['zone_squares'] if result else []
        
        logger.debug(f"Observer {observer_id} observation zone: {zone_squares}")
        return zone_squares
    
    def get_observer_current_position(self, observer_id: str) -> Optional[str]:
        """Get Observer's current position"""
        debug_trace(f"Getting current position for observer {observer_id}")
        
        query = """
        MATCH (obs:Piece {id: $observer_id})-[:OCCUPIES]->(pos:Position)
        RETURN pos.square AS square
        """
        result = self.db.execute_query(query, {'observer_id': observer_id})
        position = result[0]['square'] if result else None
        
        logger.debug(f"Observer {observer_id} current position: {position}")
        return position
    
    def get_affected_pieces_in_zone(self, observer_id: str, game_id: str) -> List[Dict]:
        """
        Get quantum pieces that would be affected by Observer's zone
        
        Returns:
            List of affected piece info
        """
        debug_trace(f"Getting affected pieces in zone for observer {observer_id}")
        
        nearby_pieces = self._find_nearby_quantum_pieces(observer_id, game_id)
        
        affected = []
        for piece_data in nearby_pieces:
            # Get piece position
            pos_query = """
            MATCH (p:Piece {id: $piece_id})-[:OCCUPIES]->(pos:Position)
            WHERE pos.is_ghost = false OR NOT exists(pos.is_ghost)
            RETURN pos.square AS square
            LIMIT 1
            """
            pos_result = self.db.execute_query(pos_query, {'piece_id': piece_data['id']})
            
            if pos_result:
                affected.append({
                    'piece_id': piece_data['id'],
                    'current_state': piece_data['quantum_state'],
                    'will_collapse': True,
                    'position': pos_result[0]['square']
                })
        
        logger.debug(f"Observer {observer_id} would affect {len(affected)} pieces: {[p['piece_id'] for p in affected]}")
        return affected
    
    def get_observer_stats(self, observer_id: str) -> Dict:
        """
        Get Observer statistics
        
        Returns:
            {
              "observations_made": 15,
              "total_pieces_affected": 12,
              "observation_history": [...]
            }
        """
        debug_trace(f"Getting stats for observer {observer_id}")
        
        query = """
        MATCH (obs:Piece {id: $observer_id})
        OPTIONAL MATCH (obs)-[observed:OBSERVED]->(target)
        
        WITH obs, 
             COALESCE(obs.observations_made, 0) AS total_observations,
             collect({
               piece_id: target.id,
               turn: observed.turn,
               state: observed.target_state
             }) AS observations
        
        RETURN {
          observations_made: total_observations,
          total_pieces_affected: size(observations),
          observation_history: observations
        } AS stats
        """
        
        result = self.db.execute_query(query, {'observer_id': observer_id})
        
        if result and result[0]['stats']:
            stats = result[0]['stats']
            logger.debug(f"Observer {observer_id} stats: {stats['observations_made']} observations, {stats['total_pieces_affected']} pieces affected")
            return stats
        
        default_stats = {
            'observations_made': 0,
            'total_pieces_affected': 0,
            'observation_history': []
        }
        logger.debug(f"Observer {observer_id} stats: no observations yet")
        return default_stats

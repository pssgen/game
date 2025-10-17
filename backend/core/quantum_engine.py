"""
Quantum Mechanics Engine for Quantum Chess
Handles superposition, entanglement, observation, and collapse
"""
import secrets
from typing import List, Tuple, Optional, Dict
from backend.db.neo4j_client import Neo4jClient
from backend.config import settings
from backend.utils.logger_factory import get_module_logger, debug_trace, log_game_event

logger = get_module_logger()


class QuantumEngine:
    """Quantum mechanics engine for chess pieces"""
    
    def __init__(self, db: Neo4jClient):
        self.db = db
        self.max_superposition_duration = settings.max_superposition_duration
        self.correlation_strength = settings.entanglement_correlation_strength
        self.max_distance = settings.entanglement_max_distance
        
        logger.info("QuantumEngine initialized with settings:")
        logger.info(f"  Max superposition duration: {self.max_superposition_duration} turns")
        logger.info(f"  Entanglement correlation strength: {self.correlation_strength}")
        logger.info(f"  Max entanglement distance: {self.max_distance} squares")
    
    def should_trigger_superposition(self, piece_type: str, from_sq: str, to_sq: str) -> bool:
        """
        Check if move triggers superposition
        
        Rules:
        - Knights: always superpose on legal moves
        - Pawns: superpose on forward moves (not captures)
        - Other pieces: never superpose
        """
        debug_trace(f"Checking superposition trigger for {piece_type}: {from_sq} -> {to_sq}")
        
        if piece_type not in ['knight', 'pawn']:
            logger.debug(f"No superposition for {piece_type}")
            return False
        
        if piece_type == 'knight':
            logger.debug(f"Superposition triggered for knight move")
            return True
        
        if piece_type == 'pawn':
            # Pawns superpose on forward moves, not captures
            from_file = from_sq[0]
            to_file = to_sq[0]
            is_forward = from_file == to_file  # Same file = forward move
            
            if is_forward:
                logger.debug(f"Superposition triggered for pawn forward move")
            else:
                logger.debug(f"No superposition for pawn capture")
            
            return is_forward
        
        return False
    
    def create_superposition(
        self,
        piece_id: str,
        from_square: str,
        to_square: str,
        game_id: str
    ) -> Dict:
        """
        Create quantum superposition in Neo4j
        
        Args:
            piece_id: ID of piece to superpose
            from_square: Origin square
            to_square: Destination square
            game_id: Current game ID
        
        Returns:
            Dictionary with superposition details
        """
        debug_trace(f"Creating superposition for {piece_id}: {from_square} | {to_square}")
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (piece:Piece {id: $piece_id})-[old_occ:OCCUPIES]->(old_pos:Position)
        
        // Create ghost position for original square
        CREATE (ghost_pos:Position {
          square: $from_square,
          probability: 0.5,
          is_ghost: true,
          turn_created: g.current_turn
        })
        
        // Create or get destination position
        MERGE (new_pos:Position {square: $to_square})
        ON CREATE SET new_pos.probability = 0.5, 
                      new_pos.is_ghost = true,
                      new_pos.turn_created = g.current_turn
        ON MATCH SET new_pos.probability = 0.5,
                     new_pos.is_ghost = true
        
        // Delete old relationship
        DELETE old_occ
        
        // Create new relationships to both positions
        CREATE (piece)-[:OCCUPIES {since_turn: g.current_turn}]->(ghost_pos)
        CREATE (piece)-[:OCCUPIES {since_turn: g.current_turn}]->(new_pos)
        
        // Update piece state
        SET piece.quantum_state = 'superposed'
        
        // Create superposition marker
        CREATE (piece)-[:IN_SUPERPOSITION {
          created_turn: g.current_turn,
          expires_turn: g.current_turn + $duration,
          collapse_probability: 0.5
        }]->(piece)
        
        RETURN piece, ghost_pos, new_pos, g.current_turn AS turn
        """
        
        result = self.db.execute_write(query, {
            'game_id': game_id,
            'piece_id': piece_id,
            'from_square': from_square,
            'to_square': to_square,
            'duration': self.max_superposition_duration
        })
        
        log_game_event(
            logger,
            "superposition_created",
            f"Piece {piece_id} entered superposition",
            positions=[from_square, to_square],
            game_id=game_id
        )
        
        return {
            'type': 'superposition_created',
            'piece_id': piece_id,
            'positions': [from_square, to_square]
        }
    
    def collapse_superposition(self, piece_id: str, game_id: str) -> Tuple[str, List[Dict]]:
        """
        Collapse superposition using cryptographically secure random
        
        Args:
            piece_id: ID of piece to collapse
            game_id: Current game ID
        
        Returns:
            (collapsed_position, cascade_events)
        """
        debug_trace(f"Collapsing superposition for {piece_id}")
        # Get both positions
        positions = self.db.get_superposition_positions(piece_id)
        
        if len(positions) != 2:
            logger.error(f"Piece {piece_id} not in valid superposition state")
            raise ValueError(f"Piece {piece_id} not in valid superposition state")
        
        # Secure random choice (50/50)
        collapsed_pos = secrets.choice(positions)
        other_pos = [p for p in positions if p != collapsed_pos][0]
        
        logger.info(f"Collapsing {piece_id}: chose {collapsed_pos} over {other_pos}")
        
        # Update Neo4j
        query = """
        MATCH (p:Piece {id: $piece_id})
        MATCH (p)-[r1:OCCUPIES]->(keep:Position {square: $keep_square})
        MATCH (p)-[r2:OCCUPIES]->(delete:Position {square: $delete_square})
        MATCH (p)-[s:IN_SUPERPOSITION]->(p)
        
        // Delete ghost position
        DELETE r2, s
        DETACH DELETE delete
        
        // Update kept position
        SET keep.probability = 1.0, keep.is_ghost = false
        
        // Update piece state (check if still entangled)
        SET p.quantum_state = CASE 
          WHEN EXISTS((p)-[:ENTANGLED_WITH]-()) THEN 'entangled'
          ELSE 'classical'
        END
        
        RETURN keep.square AS collapsed_square
        """
        
        self.db.execute_write(query, {
            'piece_id': piece_id,
            'keep_square': collapsed_pos,
            'delete_square': other_pos
        })
        
        log_game_event(
            logger,
            "superposition_collapsed",
            f"Piece {piece_id} collapsed to {collapsed_pos}",
            game_id=game_id
        )
        
        # Check for entanglement cascade
        cascade_events = self.cascade_entangled_collapses(piece_id, collapsed_pos)
        
        return collapsed_pos, cascade_events
    
    def cascade_entangled_collapses(
        self,
        piece_id: str,
        collapsed_position: str
    ) -> List[Dict]:
        """
        Cascade collapses through entangled partners with 70% correlation
        
        Args:
            piece_id: ID of piece that just collapsed
            collapsed_position: Where it collapsed to
        
        Returns:
            List of cascade events
        """
        debug_trace(f"Cascading collapses from {piece_id} at {collapsed_position}")
        
        cascade_events = []
        partners = self.db.get_entangled_partners(piece_id)
        
        logger.info(f"Cascading collapse for {piece_id}: checking {len(partners)} entangled partners")
        
        for partner_id in partners:
            partner_positions = self.db.get_superposition_positions(partner_id)
            
            if len(partner_positions) != 2:
                logger.debug(f"Partner {partner_id} already collapsed, skipping cascade")
                continue  # Partner already collapsed
            
            # Calculate correlated position
            correlated_pos = self._calculate_correlated_position(
                collapsed_position,
                partner_positions
            )
            
            # Weighted random: 70% correlated, 30% anti-correlated
            if secrets.randbelow(100) < int(self.correlation_strength * 100):
                chosen_pos = correlated_pos
                correlation_type = "correlated"
            else:
                chosen_pos = [p for p in partner_positions if p != correlated_pos][0]
                correlation_type = "anti-correlated"
            
            logger.info(f"Cascading {partner_id}: {correlation_type} collapse to {chosen_pos}")
            
            # Collapse partner to chosen position
            self._collapse_to_position(partner_id, chosen_pos)
            
            cascade_events.append({
                'type': 'cascade_collapse',
                'piece_id': partner_id,
                'collapsed_to': chosen_pos,
                'caused_by': piece_id,
                'correlation': correlation_type
            })
            
            # Break entanglement
            self.break_entanglement(piece_id, partner_id)
        
        if cascade_events:
            log_game_event(
                logger,
                "cascade_collapse_complete",
                f"Cascaded {len(cascade_events)} collapses from {piece_id}",
                piece_id=piece_id,
                cascades=len(cascade_events)
            )
        
        return cascade_events
    
    def _calculate_correlated_position(
        self,
        reference_pos: str,
        candidate_positions: List[str]
    ) -> str:
        """Calculate which position is 'correlated' (same relative direction)"""
        debug_trace(f"Calculating correlated position from {reference_pos} among {candidate_positions}")
        
        ref_file, ref_rank = ord(reference_pos[0]), int(reference_pos[1])
        
        scores = []
        for pos in candidate_positions:
            file, rank = ord(pos[0]), int(pos[1])
            # Prefer positions in same quadrant/direction
            score = abs(file - ref_file) + abs(rank - ref_rank)
            scores.append((pos, score))
        
        # Return position with highest correlation (lowest distance)
        correlated_pos = min(scores, key=lambda x: x[1])[0]
        logger.debug(f"Correlated position for {reference_pos}: {correlated_pos} (distance: {min(scores, key=lambda x: x[1])[1]})")
        
        return correlated_pos
    
    def _collapse_to_position(self, piece_id: str, position: str):
        """Collapse piece to specific position"""
        debug_trace(f"Collapsing {piece_id} to specific position {position}")
        
        other_positions = [
            p for p in self.db.get_superposition_positions(piece_id)
            if p != position
        ]
        
        logger.debug(f"Removing ghost positions for {piece_id}: {other_positions}")
        
        for other_pos in other_positions:
            query = """
            MATCH (p:Piece {id: $piece_id})-[r:OCCUPIES]->(delete:Position {square: $delete_square})
            DELETE r
            DETACH DELETE delete
            """
            self.db.execute_write(query, {
                'piece_id': piece_id,
                'delete_square': other_pos
            })
        
        # Update kept position and piece state
        query = """
        MATCH (p:Piece {id: $piece_id})-[:OCCUPIES]->(keep:Position {square: $keep_square})
        OPTIONAL MATCH (p)-[s:IN_SUPERPOSITION]->(p)
        
        SET keep.probability = 1.0, keep.is_ghost = false
        SET p.quantum_state = CASE 
          WHEN EXISTS((p)-[:ENTANGLED_WITH]-()) THEN 'entangled'
          ELSE 'classical'
        END
        
        DELETE s
        """
        self.db.execute_write(query, {
            'piece_id': piece_id,
            'keep_square': position
        })
        
        logger.debug(f"Successfully collapsed {piece_id} to {position}")
    
    def check_for_entanglement(self, game_id: str) -> List[Dict]:
        """Check if any superposed pieces overlap (triggers entanglement)"""
        debug_trace(f"Checking for entanglement overlaps in game {game_id}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p1:Piece)-[:BELONGS_TO]->(g)
        WHERE p1.quantum_state = 'superposed'
        MATCH (p1)-[:OCCUPIES]->(pos:Position)
        
        MATCH (p2:Piece)-[:BELONGS_TO]->(g)
        WHERE p2.quantum_state = 'superposed' AND p1.id < p2.id
        MATCH (p2)-[:OCCUPIES]->(pos)
        
        // Check if not already entangled
        WHERE NOT EXISTS((p1)-[:ENTANGLED_WITH]-(p2))
        
        RETURN p1.id AS piece1_id, p2.id AS piece2_id, pos.square AS overlap_square
        """
        
        overlaps = self.db.execute_query(query, {'game_id': game_id})
        
        entanglement_events = []
        for record in overlaps:
            logger.info(f"Entanglement overlap detected: {record['piece1_id']} and {record['piece2_id']} at {record['overlap_square']}")
            
            self.create_entanglement(
                record['piece1_id'],
                record['piece2_id'],
                game_id
            )
            entanglement_events.append({
                'type': 'entanglement_formed',
                'pieces': [record['piece1_id'], record['piece2_id']],
                'overlap_square': record['overlap_square']
            })
        
        if entanglement_events:
            log_game_event(
                logger,
                "entanglement_check_complete",
                f"Found {len(entanglement_events)} entanglement overlaps",
                game_id=game_id,
                overlaps=len(entanglement_events)
            )
        else:
            logger.debug(f"No entanglement overlaps found in game {game_id}")
        
        return entanglement_events
    
    def create_entanglement(self, piece1_id: str, piece2_id: str, game_id: str):
        """Create bidirectional entanglement"""
        debug_trace(f"Creating entanglement between {piece1_id} and {piece2_id}")
        
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p1:Piece {id: $piece1_id}), (p2:Piece {id: $piece2_id})
        
        CREATE (p1)-[:ENTANGLED_WITH {
          strength: $strength,
          created_turn: g.current_turn,
          correlation_type: 'spatial',
          max_distance: $max_distance
        }]->(p2)
        
        CREATE (p2)-[:ENTANGLED_WITH {
          strength: $strength,
          created_turn: g.current_turn,
          correlation_type: 'spatial',
          max_distance: $max_distance
        }]->(p1)
        
        SET p1.quantum_state = 'entangled', p2.quantum_state = 'entangled'
        
        RETURN p1, p2
        """
        
        self.db.execute_write(query, {
            'game_id': game_id,
            'piece1_id': piece1_id,
            'piece2_id': piece2_id,
            'strength': self.correlation_strength,
            'max_distance': self.max_distance
        })
        
        logger.info(f"Created entanglement: {piece1_id} <-> {piece2_id}")
        
        log_game_event(
            logger,
            "entanglement_created",
            f"Entangled pieces {piece1_id} and {piece2_id}",
            game_id=game_id,
            piece1_id=piece1_id,
            piece2_id=piece2_id,
            strength=self.correlation_strength
        )
    
    def break_entanglement(self, piece1_id: str, piece2_id: str):
        """Remove entanglement between two pieces"""
        debug_trace(f"Breaking entanglement between {piece1_id} and {piece2_id}")
        
        query = """
        MATCH (p1:Piece {id: $piece1_id})-[r:ENTANGLED_WITH]-(p2:Piece {id: $piece2_id})
        DELETE r
        
        // Update states if no other entanglements exist
        WITH p1, p2
        WHERE NOT EXISTS((p1)-[:ENTANGLED_WITH]-())
        SET p1.quantum_state = CASE 
          WHEN EXISTS((p1)-[:IN_SUPERPOSITION]->()) THEN 'superposed'
          ELSE 'classical'
        END
        
        WITH p2
        WHERE NOT EXISTS((p2)-[:ENTANGLED_WITH]-())
        SET p2.quantum_state = CASE 
          WHEN EXISTS((p2)-[:IN_SUPERPOSITION]->()) THEN 'superposed'
          ELSE 'classical'
        END
        """
        self.db.execute_write(query, {
            'piece1_id': piece1_id,
            'piece2_id': piece2_id
        })
        
        logger.info(f"Broke entanglement: {piece1_id} <-> {piece2_id}")
        
        log_game_event(
            logger,
            "entanglement_broken",
            f"Broken entanglement between {piece1_id} and {piece2_id}",
            piece1_id=piece1_id,
            piece2_id=piece2_id
        )
    
    def check_auto_collapses(self, game_id: str) -> List[Dict]:
        """
        Check for pieces that need auto-collapse
        
        Triggers:
        - Turn limit (3 turns)
        - Distance rule (>3 squares for entangled pieces)
        
        Returns:
            List of auto-collapse events
        """
        debug_trace(f"Checking for auto-collapses in game {game_id}")
        
        events = []
        
        # Turn-limit collapses
        query = """
        MATCH (g:Game {id: $game_id})
        MATCH (p:Piece)-[s:IN_SUPERPOSITION]->(p)
        WHERE s.expires_turn <= g.current_turn
        RETURN p.id AS piece_id
        """
        
        expired_pieces = self.db.execute_query(query, {'game_id': game_id})
        
        for record in expired_pieces:
            logger.info(f"Auto-collapsing expired superposition for {record['piece_id']}")
            
            collapsed_pos, cascades = self.collapse_superposition(
                record['piece_id'],
                game_id
            )
            events.append({
                'type': 'superposition_collapsed',
                'piece_id': record['piece_id'],
                'collapsed_to': collapsed_pos
            })
            events.extend(cascades)
        
        # Distance-based entanglement breaks
        query = """
        MATCH (p1:Piece)-[e:ENTANGLED_WITH]-(p2:Piece)
        WHERE p1.id < p2.id
        MATCH (p1)-[:OCCUPIES]->(pos1:Position {is_ghost: false})
        MATCH (p2)-[:OCCUPIES]->(pos2:Position {is_ghost: false})
        
        WITH p1, p2, e, pos1, pos2,
          CASE substring(pos1.square, 0, 1)
            WHEN 'a' THEN 1
            WHEN 'b' THEN 2
            WHEN 'c' THEN 3
            WHEN 'd' THEN 4
            WHEN 'e' THEN 5
            WHEN 'f' THEN 6
            WHEN 'g' THEN 7
            WHEN 'h' THEN 8
          END AS file1,
          CASE substring(pos2.square, 0, 1)
            WHEN 'a' THEN 1
            WHEN 'b' THEN 2
            WHEN 'c' THEN 3
            WHEN 'd' THEN 4
            WHEN 'e' THEN 5
            WHEN 'f' THEN 6
            WHEN 'g' THEN 7
            WHEN 'h' THEN 8
          END AS file2,
          toInteger(substring(pos1.square, 1, 1)) AS rank1,
          toInteger(substring(pos2.square, 1, 1)) AS rank2
        
        WITH p1, p2, e, abs(file1 - file2) + abs(rank1 - rank2) AS distance
        WHERE distance > e.max_distance
        RETURN p1.id AS piece1_id, p2.id AS piece2_id
        """
        
        broken_entanglements = self.db.execute_query(query, {})
        
        for record in broken_entanglements:
            logger.info(f"Breaking entanglement due to distance: {record['piece1_id']} <-> {record['piece2_id']}")
            
            self.break_entanglement(record['piece1_id'], record['piece2_id'])
            events.append({
                'type': 'entanglement_broken',
                'pieces': [record['piece1_id'], record['piece2_id']]
            })
        
        if events:
            log_game_event(
                logger,
                "auto_collapses_checked",
                f"Processed {len(events)} auto-collapse events",
                game_id=game_id,
                events=len(events)
            )
        else:
            logger.debug(f"No auto-collapse events found in game {game_id}")
        
        return events

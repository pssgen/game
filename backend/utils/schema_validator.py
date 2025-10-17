"""
Neo4j Schema Validator and Fixer for Quantum Chess
Ensures database consistency and proper relationship types
"""
from typing import Dict, List, Any
from backend.db.neo4j_client import Neo4jClient
from backend.utils.logger_factory import get_module_logger

logger = get_module_logger()


class SchemaValidator:
    """Validates and fixes Neo4j schema consistency"""
    
    def __init__(self, db: Neo4jClient):
        self.db = db
        
    def validate_and_fix_schema(self) -> Dict[str, Any]:
        """
        Comprehensive schema validation and fixes
        
        Returns:
            Summary of validations and fixes applied
        """
        logger.info("Starting comprehensive schema validation and fixes")
        
        results = {
            "constraints_created": [],
            "indexes_verified": [],
            "schema_issues_fixed": [],
            "relationship_types_verified": [],
            "node_properties_verified": []
        }
        
        # 1. Create essential constraints
        results["constraints_created"] = self._create_constraints()
        
        # 2. Verify all indexes exist
        results["indexes_verified"] = self._verify_indexes()
        
        # 3. Fix relationship type inconsistencies
        results["relationship_types_verified"] = self._verify_relationship_types()
        
        # 4. Verify node properties consistency
        results["node_properties_verified"] = self._verify_node_properties()
        
        # 5. Fix any orphaned nodes or relationships
        results["schema_issues_fixed"] = self._fix_orphaned_data()
        
        logger.info("Schema validation and fixes completed")
        return results
    
    def _create_constraints(self) -> List[str]:
        """Create essential uniqueness constraints"""
        constraints = [
            "CREATE CONSTRAINT piece_id_unique IF NOT EXISTS FOR (p:Piece) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.id IS UNIQUE",
            "CREATE CONSTRAINT queue_id_unique IF NOT EXISTS FOR (q:GameQueue) REQUIRE q.id IS UNIQUE",
            "CREATE CONSTRAINT position_square_unique IF NOT EXISTS FOR (pos:Position) REQUIRE pos.square IS UNIQUE",
            "CREATE CONSTRAINT move_id_unique IF NOT EXISTS FOR (m:Move) REQUIRE m.id IS UNIQUE"
        ]
        
        created = []
        
        try:
            with self.db.driver.session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                        created.append(constraint.split()[-1])  # Extract constraint name
                        logger.debug(f"Created constraint: {constraint}")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Constraint creation failed: {e}")
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")
            
        return created
    
    def _verify_indexes(self) -> List[str]:
        """Verify all necessary indexes exist"""
        required_indexes = [
            "piece_id", "piece_state", "position_square", "game_id", 
            "game_queue_id", "move_id", "game_created_at", "move_sequence"
        ]
        
        verified = []
        
        try:
            # Get existing indexes
            query = "SHOW INDEXES"
            existing_indexes = self.db.execute_query(query)
            existing_names = {idx.get('name', '') for idx in existing_indexes}
            
            for idx_name in required_indexes:
                if any(idx_name in name for name in existing_names):
                    verified.append(idx_name)
                    logger.debug(f"Index verified: {idx_name}")
                else:
                    logger.warning(f"Missing index: {idx_name}")
                    
        except Exception as e:
            logger.error(f"Failed to verify indexes: {e}")
            
        return verified
    
    def _verify_relationship_types(self) -> List[str]:
        """Verify all relationship types are consistent"""
        expected_relationships = [
            "BELONGS_TO",     # Piece -> Game
            "OCCUPIES",       # Piece -> Position
            "IN_SUPERPOSITION",  # Piece -> Piece (self-reference)
            "ENTANGLED_WITH", # Piece <-> Piece (bidirectional)
            "CONTAINS_GAME",  # GameQueue -> Game
            "HAS_MOVE",       # Game -> Move
            "FOLLOWS"         # Move -> Move (sequence)
        ]
        
        verified = []
        
        try:
            # Get all relationship types in database
            query = "CALL db.relationshipTypes()"
            result = self.db.execute_query(query)
            existing_types = {r['relationshipType'] for r in result}
            
            for rel_type in expected_relationships:
                if rel_type in existing_types:
                    verified.append(rel_type)
                    logger.debug(f"Relationship type verified: {rel_type}")
                else:
                    logger.warning(f"Missing relationship type: {rel_type}")
                    
        except Exception as e:
            logger.error(f"Failed to verify relationship types: {e}")
            
        return verified
    
    def _verify_node_properties(self) -> List[str]:
        """Verify essential node properties exist"""
        verifications = []
        
        try:
            # Verify Piece nodes have required properties
            piece_check = """
            MATCH (p:Piece)
            WHERE p.id IS NULL OR p.type IS NULL OR p.color IS NULL OR p.quantum_state IS NULL
            RETURN count(p) AS invalid_pieces
            """
            result = self.db.execute_query(piece_check)
            invalid_pieces = result[0]['invalid_pieces'] if result else 0
            
            if invalid_pieces == 0:
                verifications.append("Piece properties valid")
            else:
                logger.warning(f"Found {invalid_pieces} pieces with missing required properties")
            
            # Verify Game nodes have required properties
            game_check = """
            MATCH (g:Game)
            WHERE g.id IS NULL OR g.current_turn IS NULL OR g.active_player IS NULL
            RETURN count(g) AS invalid_games
            """
            result = self.db.execute_query(game_check)
            invalid_games = result[0]['invalid_games'] if result else 0
            
            if invalid_games == 0:
                verifications.append("Game properties valid")
            else:
                logger.warning(f"Found {invalid_games} games with missing required properties")
            
            # Verify Position nodes have square property
            position_check = """
            MATCH (pos:Position)
            WHERE pos.square IS NULL
            RETURN count(pos) AS invalid_positions
            """
            result = self.db.execute_query(position_check)
            invalid_positions = result[0]['invalid_positions'] if result else 0
            
            if invalid_positions == 0:
                verifications.append("Position properties valid")
            else:
                logger.warning(f"Found {invalid_positions} positions with missing square property")
                
        except Exception as e:
            logger.error(f"Failed to verify node properties: {e}")
            
        return verifications
    
    def _fix_orphaned_data(self) -> List[str]:
        """Fix orphaned nodes and relationships"""
        fixes = []
        
        try:
            # Remove pieces not belonging to any game
            orphaned_pieces_query = """
            MATCH (p:Piece)
            WHERE NOT (p)-[:BELONGS_TO]->(:Game)
            DELETE p
            RETURN count(p) AS deleted_pieces
            """
            result = self.db.execute_write(orphaned_pieces_query)
            deleted_pieces = result[0]['deleted_pieces'] if result else 0
            
            if deleted_pieces > 0:
                fixes.append(f"Deleted {deleted_pieces} orphaned pieces")
                logger.info(f"Cleaned up {deleted_pieces} orphaned pieces")
            
            # Remove positions not occupied by any piece
            orphaned_positions_query = """
            MATCH (pos:Position)
            WHERE NOT (pos)<-[:OCCUPIES]-(:Piece)
            AND pos.square NOT IN ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8',
                                   'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8',
                                   'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8',
                                   'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8',
                                   'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8',
                                   'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                                   'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8',
                                   'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8']
            DELETE pos
            RETURN count(pos) AS deleted_positions
            """
            result = self.db.execute_write(orphaned_positions_query)
            deleted_positions = result[0]['deleted_positions'] if result else 0
            
            if deleted_positions > 0:
                fixes.append(f"Deleted {deleted_positions} orphaned positions")
                logger.info(f"Cleaned up {deleted_positions} orphaned positions")
            
            # Fix broken superposition relationships (self-references)
            broken_superposition_query = """
            MATCH (p:Piece)-[s:IN_SUPERPOSITION]->(target:Piece)
            WHERE p.id <> target.id
            DELETE s
            RETURN count(s) AS fixed_superpositions
            """
            result = self.db.execute_write(broken_superposition_query)
            fixed_superpositions = result[0]['fixed_superpositions'] if result else 0
            
            if fixed_superpositions > 0:
                fixes.append(f"Fixed {fixed_superpositions} broken superposition relationships")
                logger.info(f"Fixed {fixed_superpositions} broken superposition relationships")
                
        except Exception as e:
            logger.error(f"Failed to fix orphaned data: {e}")
            
        return fixes

    def validate_quantum_state_consistency(self) -> Dict[str, Any]:
        """Validate quantum state consistency"""
        logger.info("Validating quantum state consistency")
        
        issues_found = []
        fixes_applied = []
        
        try:
            # Check for pieces in superposition without IN_SUPERPOSITION relationship
            superposition_check = """
            MATCH (p:Piece {quantum_state: 'superposed'})
            WHERE NOT (p)-[:IN_SUPERPOSITION]->(p)
            RETURN count(p) AS inconsistent_superposition
            """
            result = self.db.execute_query(superposition_check)
            inconsistent = result[0]['inconsistent_superposition'] if result else 0
            
            if inconsistent > 0:
                issues_found.append(f"{inconsistent} pieces marked as superposed without relationship")
                
                # Fix: Remove quantum_state or add relationship based on position count
                fix_query = """
                MATCH (p:Piece {quantum_state: 'superposed'})
                WHERE NOT (p)-[:IN_SUPERPOSITION]->(p)
                OPTIONAL MATCH (p)-[:OCCUPIES]->(pos:Position)
                WITH p, count(pos) AS position_count
                WHERE position_count <= 1
                SET p.quantum_state = 'classical'
                RETURN count(p) AS fixed_pieces
                """
                result = self.db.execute_write(fix_query)
                fixed = result[0]['fixed_pieces'] if result else 0
                if fixed > 0:
                    fixes_applied.append(f"Fixed {fixed} incorrectly marked superposed pieces")
            
            # Check for entangled pieces without ENTANGLED_WITH relationship
            entanglement_check = """
            MATCH (p:Piece {quantum_state: 'entangled'})
            WHERE NOT (p)-[:ENTANGLED_WITH]-()
            RETURN count(p) AS inconsistent_entanglement
            """
            result = self.db.execute_query(entanglement_check)
            inconsistent_entangled = result[0]['inconsistent_entanglement'] if result else 0
            
            if inconsistent_entangled > 0:
                issues_found.append(f"{inconsistent_entangled} pieces marked as entangled without relationship")
                
                # Fix: Set to classical if no entanglement relationship
                fix_entangled_query = """
                MATCH (p:Piece {quantum_state: 'entangled'})
                WHERE NOT (p)-[:ENTANGLED_WITH]-()
                SET p.quantum_state = 'classical'
                RETURN count(p) AS fixed_entangled
                """
                result = self.db.execute_write(fix_entangled_query)
                fixed_entangled = result[0]['fixed_entangled'] if result else 0
                if fixed_entangled > 0:
                    fixes_applied.append(f"Fixed {fixed_entangled} incorrectly marked entangled pieces")
            
        except Exception as e:
            logger.error(f"Failed to validate quantum state consistency: {e}")
            
        return {
            "issues_found": issues_found,
            "fixes_applied": fixes_applied
        }
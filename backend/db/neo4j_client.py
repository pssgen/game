"""
Neo4j Database Client for Quantum Chess
Handles all graph database operations
"""
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
from backend.utils.logger_factory import get_module_logger, debug_trace

logger = get_module_logger()


class Neo4jClient:
    """Neo4j database client with Quantum Chess specific methods"""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j bolt URI (e.g., bolt://localhost:7687)
            user: Database username
            password: Database password
        """
        debug_trace(f"Initializing Neo4j connection to {uri}")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connectivity before proceeding
            self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")
            self._create_indexes()
        except Exception as e:
            logger.error(f"Neo4j connection failed during initialization: {e}")
            self.driver = None
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
    
    def _create_indexes(self):
        """Create performance indexes on frequently queried properties"""
        if not self.driver:
            logger.error("Cannot create indexes: Neo4j driver not initialized.")
            return
        indexes = [
            "CREATE INDEX piece_id IF NOT EXISTS FOR (p:Piece) ON (p.id)",
            "CREATE INDEX piece_state IF NOT EXISTS FOR (p:Piece) ON (p.quantum_state)",
            "CREATE INDEX position_square IF NOT EXISTS FOR (pos:Position) ON (pos.square)",
            "CREATE INDEX game_id IF NOT EXISTS FOR (g:Game) ON (g.id)",
            # Game Storage System indexes
            "CREATE INDEX game_queue_id IF NOT EXISTS FOR (q:GameQueue) ON (q.id)",
            "CREATE INDEX move_id IF NOT EXISTS FOR (m:Move) ON (m.id)",
            "CREATE INDEX game_created_at IF NOT EXISTS FOR (g:Game) ON (g.created_at)",
            "CREATE INDEX move_sequence IF NOT EXISTS FOR (m:Move) ON (m.metadata.sequence_number)",
        ]
        try:
            with self.driver.session() as session:
                for index_query in indexes:
                    try:
                        session.run(index_query)
                    except Exception as e:
                        logger.warning(f"Index creation failed (may already exist): {e}")
        except Exception as e:
            logger.error(f"Failed to create indexes due to connection error: {e}")
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Query parameters dict
        
        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]
    
    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """
        Execute a write transaction
        
        Args:
            query: Cypher query string
            parameters: Query parameters dict
        
        Returns:
            List of result records
        """
        def _write_tx(tx, query, params):
            result = tx.run(query, params)
            return [dict(record) for record in result]
        
        parameters = parameters or {}
        
        with self.driver.session() as session:
            return session.execute_write(_write_tx, query, parameters)
    
    def get_piece_by_id(self, piece_id: str) -> Optional[Dict]:
        """Get piece node by ID"""
        query = """
        MATCH (p:Piece {id: $piece_id})
        OPTIONAL MATCH (p)-[:OCCUPIES]->(pos:Position)
        RETURN p, collect(pos) AS positions
        """
        
        results = self.execute_query(query, {'piece_id': piece_id})
        if results:
            return results[0]
        return None
    
    def get_superposition_positions(self, piece_id: str) -> List[str]:
        """Get both positions of a superposed piece"""
        query = """
        MATCH (p:Piece {id: $piece_id})-[:IN_SUPERPOSITION]->(p)
        MATCH (p)-[:OCCUPIES]->(pos:Position)
        RETURN pos.square AS square
        """
        
        results = self.execute_query(query, {'piece_id': piece_id})
        return [r['square'] for r in results]
    
    def get_entangled_partners(self, piece_id: str) -> List[str]:
        """Get IDs of all pieces entangled with given piece"""
        query = """
        MATCH (p:Piece {id: $piece_id})-[:ENTANGLED_WITH]-(partner:Piece)
        RETURN partner.id AS partner_id
        """
        
        results = self.execute_query(query, {'piece_id': piece_id})
        return [r['partner_id'] for r in results]
    
    def get_piece_state(self, piece_id: str) -> Optional[Dict]:
        """Get complete piece state including quantum properties"""
        query = """
        MATCH (p:Piece {id: $piece_id})
        OPTIONAL MATCH (p)-[:OCCUPIES]->(pos:Position)
        OPTIONAL MATCH (p)-[:ENTANGLED_WITH]-(partner:Piece)
        OPTIONAL MATCH (p)-[s:IN_SUPERPOSITION]->(p)
        
        WITH p, collect(DISTINCT pos) AS positions, collect(DISTINCT partner.id) AS entangled_partners, s.expires_turn AS superposition_expires
        
        RETURN p {
            .*,
            positions: [pos IN positions | pos {.*}],
            entangled_with: entangled_partners,
            superposition_expires: superposition_expires
        } AS piece_data
        """
        
        results = self.execute_query(query, {'piece_id': piece_id})
        if results and results[0].get('piece_data'):
            return results[0]['piece_data']
        return None
    
    def verify_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection verified")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False

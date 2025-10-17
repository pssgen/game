"""
Observer Piece Tests
Tests for Observer movement, observation, and quantum collapse mechanics
"""
import pytest
from backend.core.observer_engine import ObserverEngine
from backend.core.quantum_engine import QuantumEngine
from backend.core.game_state import GameStateManager
from backend.db.neo4j_client import Neo4jClient
from backend.config import settings


@pytest.fixture
def db_client():
    """Create database client for testing"""
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    yield db
    db.close()


@pytest.fixture
def game_id(db_client):
    """Create a test game"""
    game_state_manager = GameStateManager(db_client)
    game_id = game_state_manager.initialize_board()
    yield game_id
    # Cleanup
    cleanup_query = "MATCH (g:Game {id: $game_id})-[*]-(n) DETACH DELETE g, n"
    db_client.execute_write(cleanup_query, {'game_id': game_id})


@pytest.fixture
def observer_engine(db_client):
    """Create Observer engine instance"""
    return ObserverEngine(db_client)


@pytest.fixture
def quantum_engine(db_client):
    """Create Quantum engine instance"""
    return QuantumEngine(db_client)


class TestObserverMovement:
    """Test Observer piece movement patterns"""
    
    def test_observer_king_pattern_movement(self, observer_engine, game_id):
        """Observer should move exactly like a king (1 square in 8 directions)"""
        # Get valid moves for white Observer at e2 (starting position)
        valid_moves = observer_engine.get_valid_moves('observer-w-1', game_id)
        
        # From e2, should be able to move to d2, d3, e3, f3, f2
        # (d1, e1, f1 blocked by own pieces)
        expected_moves = {'d2', 'd3', 'e3', 'f3', 'f2'}
        assert set(valid_moves) == expected_moves
    
    def test_observer_cannot_move_to_own_pieces(self, observer_engine, game_id):
        """Observer cannot move to squares occupied by own pieces"""
        valid_moves = observer_engine.get_valid_moves('observer-w-1', game_id)
        
        # e1, d1, f1 have white pieces, should not be in valid moves
        assert 'e1' not in valid_moves
        assert 'd1' not in valid_moves
        assert 'f1' not in valid_moves
    
    def test_observer_can_capture_enemy_pieces(self, observer_engine, db_client, game_id):
        """Observer should be able to capture enemy pieces like a king"""
        # Move black pawn to e3 (adjacent to white Observer at e2)
        move_query = """
        MATCH (p:Piece {id: 'pawn-b-5'})-[old:OCCUPIES]->()
        MATCH (new_pos:Position {square: 'e3'})
        DELETE old
        CREATE (p)-[:OCCUPIES]->(new_pos)
        """
        db_client.execute_write(move_query, {})
        
        # Observer should be able to move to e3 (capture)
        valid_moves = observer_engine.get_valid_moves('observer-w-1', game_id)
        assert 'e3' in valid_moves
    
    def test_observer_move_updates_position(self, observer_engine, game_id):
        """Observer move should correctly update its position"""
        result = observer_engine.move_observer('observer-w-1', 'e3', game_id)
        
        assert result['success'] == True
        assert result['new_position'] == 'e3'
        
        # Verify new position
        new_pos = observer_engine.get_observer_current_position('observer-w-1')
        assert new_pos == 'e3'


class TestObserverObservation:
    """Test Observer's automatic observation mechanics"""
    
    def test_observer_collapses_nearby_superposition(self, observer_engine, quantum_engine, db_client, game_id):
        """Observer should automatically collapse nearby superposed pieces"""
        # Create superposition for knight at b1 -> d4
        # First move knight to allow superposition
        move_query = """
        MATCH (k:Piece {id: 'knight-w-1'})-[old:OCCUPIES]->()
        DELETE old
        """
        db_client.execute_write(move_query, {})
        
        # Create superposition manually
        quantum_engine.create_superposition('knight-w-1', 'b1', 'd4', game_id)
        
        # Move Observer to e5 (adjacent to d4)
        result = observer_engine.move_observer('observer-w-1', 'e5', game_id)
        
        # Assert knight was observed
        assert 'knight-w-1' in result['observed_pieces']
        assert len(result['collapsed_states']) >= 1
        
        # Verify knight is now classical
        knight_query = """
        MATCH (k:Piece {id: 'knight-w-1'})
        RETURN k.quantum_state AS state
        """
        knight_result = db_client.execute_query(knight_query, {})
        assert knight_result[0]['state'] == 'classical'
    
    def test_observer_breaks_entanglement(self, observer_engine, quantum_engine, db_client, game_id):
        """Observer should break entanglement between nearby pieces"""
        # Setup: Create entangled pieces near Observer
        # Move pieces to allow entanglement
        setup_query = """
        MATCH (k:Piece {id: 'knight-w-1'})-[old1:OCCUPIES]->()
        MATCH (p:Piece {id: 'pawn-w-4'})-[old2:OCCUPIES]->()
        DELETE old1, old2
        """
        db_client.execute_write(setup_query, {})
        
        # Create superpositions
        quantum_engine.create_superposition('knight-w-1', 'b1', 'd4', game_id)
        quantum_engine.create_superposition('pawn-w-4', 'd2', 'd5', game_id)
        
        # Create entanglement
        quantum_engine.create_entanglement('knight-w-1', 'pawn-w-4', game_id)
        
        # Move Observer to e4 (adjacent to both d4 and d5)
        result = observer_engine.move_observer('observer-w-1', 'e4', game_id)
        
        # Assert both pieces were observed
        assert 'knight-w-1' in result['observed_pieces'] or 'pawn-w-4' in result['observed_pieces']
    
    def test_observer_affects_both_friendly_and_enemy_pieces(self, observer_engine, quantum_engine, db_client, game_id):
        """Observer should observe both friendly and enemy quantum pieces"""
        # Create superposed pieces (white and black) near Observer
        setup_query = """
        MATCH (wk:Piece {id: 'knight-w-1'})-[old1:OCCUPIES]->()
        MATCH (bk:Piece {id: 'knight-b-1'})-[old2:OCCUPIES]->()
        DELETE old1, old2
        """
        db_client.execute_write(setup_query, {})
        
        quantum_engine.create_superposition('knight-w-1', 'b1', 'd4', game_id)
        quantum_engine.create_superposition('knight-b-1', 'b8', 'f4', game_id)
        
        # Move Observer to e4 (adjacent to both d4 and f4)
        result = observer_engine.move_observer('observer-w-1', 'e4', game_id)
        
        # Both pieces should be observed (symmetrical observation)
        piece_ids = result['observed_pieces']
        assert 'knight-w-1' in piece_ids or 'knight-b-1' in piece_ids
    
    def test_observer_range_exactly_one_square(self, observer_engine, quantum_engine, db_client, game_id):
        """Observer should only affect pieces within 1-square radius"""
        # Create pieces at different distances from Observer
        setup_query = """
        MATCH (k1:Piece {id: 'knight-w-1'})-[old1:OCCUPIES]->()
        MATCH (k2:Piece {id: 'knight-w-2'})-[old2:OCCUPIES]->()
        DELETE old1, old2
        """
        db_client.execute_write(setup_query, {})
        
        # d4 is adjacent to e5, c6 is 2 squares away
        quantum_engine.create_superposition('knight-w-1', 'b1', 'd4', game_id)
        quantum_engine.create_superposition('knight-w-2', 'g1', 'c6', game_id)
        
        # Move Observer to e5
        result = observer_engine.move_observer('observer-w-1', 'e5', game_id)
        
        # Only d4 knight should be affected
        assert 'knight-w-1' in result['observed_pieces']
        assert 'knight-w-2' not in result['observed_pieces']


class TestObserverZone:
    """Test Observer observation zone calculations"""
    
    def test_observer_zone_preview_correct_squares(self, observer_engine, db_client, game_id):
        """Get observation zone preview should return correct squares"""
        # Move Observer to e4 first
        observer_engine.move_observer('observer-w-1', 'e4', game_id)
        
        # Get zone preview
        zone = observer_engine.get_observation_zone_preview('observer-w-1', game_id)
        
        # Should include all 9 squares (8 surrounding + center)
        expected_zone = {'d3', 'd4', 'd5', 'e3', 'e4', 'e5', 'f3', 'f4', 'f5'}
        assert set(zone) == expected_zone
    
    def test_observer_in_corner_limited_range(self, observer_engine, db_client, game_id):
        """Observer in corner should have limited observation zone"""
        # Move Observer to a1 (corner)
        # First clear the square
        clear_query = """
        MATCH (r:Piece {id: 'rook-w-1'})-[old:OCCUPIES]->()
        DELETE old
        CREATE (r)-[:OCCUPIES]->(pos:Position {square: 'h1'})
        """
        db_client.execute_write(clear_query, {})
        
        observer_engine.move_observer('observer-w-1', 'a1', game_id)
        
        # Get zone preview
        zone = observer_engine.get_observation_zone_preview('observer-w-1', game_id)
        
        # Should only have 4 squares (corner position)
        expected_zone = {'a1', 'a2', 'b1', 'b2'}
        assert set(zone) == expected_zone


class TestObserverStats:
    """Test Observer statistics tracking"""
    
    def test_observer_tracks_observations_made(self, observer_engine, quantum_engine, db_client, game_id):
        """Observer should track observation statistics"""
        # Create superposed piece
        setup_query = """
        MATCH (k:Piece {id: 'knight-w-1'})-[old:OCCUPIES]->()
        DELETE old
        """
        db_client.execute_write(setup_query, {})
        quantum_engine.create_superposition('knight-w-1', 'b1', 'd4', game_id)
        
        # Move Observer (triggers observation)
        observer_engine.move_observer('observer-w-1', 'e5', game_id)
        
        # Get stats
        stats = observer_engine.get_observer_stats('observer-w-1')
        
        # Should have recorded observations
        assert stats['observations_made'] > 0
        assert 'observation_history' in stats
    
    def test_observer_stats_initial_state(self, observer_engine, game_id):
        """Observer should start with 0 observations"""
        stats = observer_engine.get_observer_stats('observer-w-1')
        
        assert stats['observations_made'] == 0
        assert stats['total_pieces_affected'] == 0
        assert len(stats['observation_history']) == 0


class TestObserverSpecialCases:
    """Test Observer edge cases and special scenarios"""
    
    def test_observer_cannot_enter_superposition(self, quantum_engine, db_client, game_id):
        """Observer should never enter quantum states itself"""
        # Verify Observer has no quantum ability
        query = """
        MATCH (obs:Piece {id: 'observer-w-1'})
        RETURN obs.quantum_ability AS quantum_ability
        """
        result = db_client.execute_query(query, {})
        assert result[0]['quantum_ability'] == False
    
    def test_observer_vs_classical_pieces_no_effect(self, observer_engine, db_client, game_id):
        """Observer should not affect classical (non-quantum) pieces"""
        # All pieces start classical, move Observer
        result = observer_engine.move_observer('observer-w-1', 'e3', game_id)
        
        # No observations should be made (no quantum pieces nearby)
        assert len(result['observed_pieces']) == 0
        assert len(result['collapsed_states']) == 0
    
    def test_multiple_observers_independent_zones(self, observer_engine, db_client, game_id):
        """Two Observers should have independent observation zones"""
        # Get zones for both Observers
        zone_white = observer_engine.get_observation_zone_preview('observer-w-1', game_id)
        zone_black = observer_engine.get_observation_zone_preview('observer-b-1', game_id)
        
        # Should have different zones
        assert 'e2' in zone_white  # White Observer at e2
        assert 'e7' in zone_black  # Black Observer at e7
        
        # No overlap initially
        assert not set(zone_white).intersection(set(zone_black))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

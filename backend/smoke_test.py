"""
Basic smoke test to validate the quantum chess system is working
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Test basic imports
def test_imports():
    """Test that we can import core modules"""
    try:
        import config
        print("✓ Config imported successfully")
        
        from models.game_models import GameState, MoveRequest
        print("✓ Game models imported successfully")
        
        from utils.exceptions import QuantumChessError
        print("✓ Exceptions imported successfully")
        
        print("✓ All core imports successful!")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without database"""
    try:
        from models.game_models import GameState, MoveRequest, GameInfo, PieceData
        
        # Test creating a game state
        game_info = GameInfo(
            id="test-game",
            current_turn=1,
            active_player="white",
            status="active"
        )
        
        game_state = GameState(
            game=game_info,
            pieces=[]
        )
        print("✓ GameState creation successful")
        
        # Test creating a move request
        move_request = MoveRequest(
            game_id="test-game",
            from_square="e2",
            to_square="e4",
            player="white"
        )
        print("✓ MoveRequest creation successful")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running Quantum Chess Smoke Tests...")
    print("=" * 50)
    
    import_success = test_imports()
    basic_success = test_basic_functionality()
    
    print("=" * 50)
    if import_success and basic_success:
        print("✓ All smoke tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)
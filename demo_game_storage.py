"""
Quantum Chess Game Storage System Demo
Demonstrates the full GameQueue -> Game -> Move hierarchy functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.neo4j_client import Neo4jClient
from backend.core.game_storage import GameStorageManager
from backend.core.game_state import GameStateManager
from backend.config import settings
from backend.utils.logger_factory import get_module_logger, debug_trace

logger = get_module_logger()


def demo_game_storage_system():
    """Complete demonstration of the game storage system"""

    print("🎯 Quantum Chess Game Storage System Demo")
    print("=" * 50)

    # Initialize database connection
    debug_trace("Initializing database connection")
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )

    if not db.verify_connection():
        print("❌ Database connection failed")
        return

    print("✅ Database connected successfully")

    # Initialize storage manager
    storage = GameStorageManager(db)
    game_state = GameStateManager(db)

    try:
        # 1. Create a game queue
        print("\n📁 Step 1: Creating Game Queue")
        queue_id = storage.create_game_queue("Demo Tournament 2025")
        print(f"✅ Created queue: {queue_id}")

        # 2. Create games in the queue
        print("\n🎮 Step 2: Creating Games in Queue")
        game1_id = storage.create_game_in_queue(queue_id, "Alice", "Bob")
        game2_id = storage.create_game_in_queue(queue_id, "Charlie", "Diana")
        print(f"✅ Created games: {game1_id}, {game2_id}")

        # 3. Initialize board for first game
        print("\n♟️ Step 3: Initializing Game Board")
        game_state.initialize_board(queue_id, "Alice", "Bob")
        print(f"✅ Initialized board for game: {game1_id}")

        # 4. Record some sample moves
        print("\n🔄 Step 4: Recording Moves")
        move1_data = {
            'from_square': 'e2',
            'to_square': 'e4',
            'player': 'white',
            'piece_type': 'pawn',
            'move_type': 'standard',
            'turn_number': 1,
            'quantum_events': []
        }
        move1_id = storage.add_move_to_game(game1_id, move1_data)
        print(f"✅ Recorded move 1: {move1_id}")

        move2_data = {
            'from_square': 'e7',
            'to_square': 'e5',
            'player': 'black',
            'piece_type': 'pawn',
            'move_type': 'standard',
            'turn_number': 2,
            'quantum_events': []
        }
        move2_id = storage.add_move_to_game(game1_id, move2_data)
        print(f"✅ Recorded move 2: {move2_id}")

        # 5. Query games in queue
        print("\n📊 Step 5: Querying Games in Queue")
        games = storage.get_games_in_queue(queue_id)
        print(f"✅ Found {len(games)} games in queue:")
        for game in games:
            print(f"   - {game['id']}: {game['metadata']['white_player']} vs {game['metadata']['black_player']} ({game['move_count']} moves)")

        # 6. Query moves in game
        print("\n📋 Step 6: Querying Moves in Game")
        moves = storage.get_moves_in_game(game1_id)
        print(f"✅ Found {len(moves)} moves in game {game1_id}:")
        for move in moves:
            meta = move['metadata']
            print(f"   - Move {meta['sequence_number']}: {meta['player']} {meta['piece_type']} {meta['from_square']}->{meta['to_square']}")

        # 7. Query player games
        print("\n👤 Step 7: Querying Player Games")
        alice_games = storage.get_player_games("Alice", limit=10)
        print(f"✅ Found {len(alice_games)} games for Alice:")
        for game in alice_games:
            print(f"   - {game['game_id']} in queue {game['queue_id']} (role: {game['player_role']})")

        # 8. Get queue statistics
        print("\n📈 Step 8: Queue Statistics")
        stats = storage.get_queue_stats(queue_id)
        print(f"✅ Queue {queue_id} statistics:")
        print(f"   - Total games: {stats['total_games']}")
        print(f"   - Active games: {stats['active_games']}")
        print(f"   - Completed games: {stats['completed_games']}")
        print(f"   - Total moves: {stats['total_moves']}")
        print(f"   - Average moves per game: {stats['average_moves_per_game']:.2f}")

        # 9. End a game
        print("\n🏁 Step 9: Ending Game")
        storage.end_game(game1_id, "checkmate", "Alice", "standard")
        print(f"✅ Ended game {game1_id} with checkmate (winner: Alice)")

        # 10. Verify updated statistics
        print("\n🔄 Step 10: Updated Statistics")
        updated_stats = storage.get_queue_stats(queue_id)
        print(f"✅ Updated queue statistics:")
        print(f"   - Active games: {updated_stats['active_games']} (was {stats['active_games']})")
        print(f"   - Completed games: {updated_stats['completed_games']} (was {stats['completed_games']})")

        print("\n🎉 Demo completed successfully!")
        print("\n📝 Key Features Demonstrated:")
        print("   ✅ GameQueue -> Game -> Move hierarchy")
        print("   ✅ Automatic metadata tracking")
        print("   ✅ Efficient querying by queue, game, and player")
        print("   ✅ Comprehensive statistics")
        print("   ✅ Game lifecycle management")
        print("   ✅ Integrated logging and error handling")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    demo_game_storage_system()
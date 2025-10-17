"""
Basic pytest configuration for Quantum Chess Backend
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from db.neo4j_client import Neo4jClient
from config import settings


@pytest.fixture
def db_client():
    """Create a test database client"""
    client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    yield client
    client.close()


@pytest.fixture
def sample_game_id():
    """Provide a sample game ID for testing"""
    return "test-game-123"

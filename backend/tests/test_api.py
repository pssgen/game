"""
Integration tests for API endpoints
"""
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Quantum Chess API"
    assert "features" in data


def test_create_game():
    """Test game creation"""
    response = client.post("/game/new")
    assert response.status_code == 200
    
    data = response.json()
    assert "game_id" in data
    assert "initial_state" in data
    assert data["initial_state"]["game"]["current_turn"] == 1

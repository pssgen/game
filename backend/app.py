"""
Quantum Chess Backend - Main Application
FastAPI server with WebSocket support for real-time quantum chess gameplay
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import game_router
from backend.db.neo4j_client import Neo4jClient
from backend.config import settings
from backend.utils.logger_factory import get_module_logger, log_game_event, log_error_with_analysis
from backend.utils.error_handlers import add_error_handlers
from typing import Dict, List
import logging
import json
from contextlib import asynccontextmanager

# Get logger for this module
logger = get_module_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    log_game_event(logger, "server_startup", "Starting Quantum Chess Backend")

    # Test database connection
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )

    db_ok = db.verify_connection()
    if db_ok:
        log_game_event(logger, "db_connection", "Neo4j connection established successfully")
    else:
        log_error_with_analysis(
            logger,
            "Neo4j connection failed during startup",
            "Database connection parameters are invalid or Neo4j service is not running",
            "Check Neo4j configuration and ensure service is running"
        )

    # Test quantum engine
    try:
        from backend.core.quantum_engine import QuantumEngine
        quantum_engine = QuantumEngine(db)
        quantum_ok = True
        logger.info("QuantumEngine initialized successfully")
    except Exception as e:
        quantum_ok = False
        logger.error(f"QuantumEngine initialization failed: {e}")

    # Count routes
    routes_count = len([route for route in app.routes if hasattr(route, 'methods')])

    # Startup summary
    components_status = []
    components_status.append("Neo4j OK" if db_ok else "Neo4j FAIL")
    components_status.append("QuantumEngine OK" if quantum_ok else "QuantumEngine FAIL")
    components_status.append(f"Routes Loaded: {routes_count}")

    status_emoji = "✅" if all([db_ok, quantum_ok]) else "⚠️"
    logger.info(f"{status_emoji} [STARTUP SUMMARY] {' | '.join(components_status)}")

    db.close()
    log_game_event(logger, "server_ready", "Quantum Chess Backend server ready")

    yield

    # Shutdown summary
    logger.info("🧱 [SHUTDOWN SUMMARY] All connections closed successfully")

# Create FastAPI app
app = FastAPI(
    title="Quantum Chess API",
    description="A chess game with quantum mechanics: superposition, entanglement, and observation",
    version="1.0.0",
    lifespan=lifespan
)

# Add error handlers
add_error_handlers(app)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game_router)


# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time game updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        logger.info(f"Client connected to game {game_id}")
    
    def disconnect(self, websocket: WebSocket, game_id: str):
        """Remove a disconnected client"""
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            logger.info(f"Client disconnected from game {game_id}")
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """Send message to all players in a game"""
        if game_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[game_id].remove(conn)


manager = ConnectionManager()


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Quantum Chess API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Quantum superposition (knights & pawns)",
            "Quantum entanglement",
            "Observer effect",
            "Real-time WebSocket updates"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    
    db_healthy = db.verify_connection()
    db.close()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected"
    }


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for real-time game updates
    
    Client sends:
        {
          "action": "move" | "observe" | "sync",
          "data": { ... }
        }
    
    Server broadcasts:
        {
          "event": "move_made" | "piece_observed" | "game_updated",
          "data": { ... }
        }
    """
    await manager.connect(websocket, game_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            action = data.get('action')
            
            logger.info(f"WebSocket action: {action} for game {game_id}")
            
            if action == 'move':
                # Broadcast move to all players
                await manager.broadcast_to_game(game_id, {
                    'event': 'move_made',
                    'data': data.get('data', {})
                })
            
            elif action == 'observe':
                # Broadcast observation to all players
                await manager.broadcast_to_game(game_id, {
                    'event': 'piece_observed',
                    'data': data.get('data', {})
                })
            
            elif action == 'sync':
                # Send sync response only to requesting client
                await websocket.send_json({
                    'event': 'sync_response',
                    'data': {'message': 'Sync request received'}
                })
            
            else:
                await websocket.send_json({
                    'event': 'error',
                    'data': {'message': f'Unknown action: {action}'}
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
        await manager.broadcast_to_game(game_id, {
            'event': 'player_disconnected',
            'data': {'message': 'A player has disconnected'}
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )

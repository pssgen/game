# 📁 Quantum Chess - Project Structure

```
d:\chess\
│
├── backend/                          # Python FastAPI Backend
│   ├── app.py                        # Main FastAPI application
│   ├── config.py                     # Configuration management
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend Docker image
│   ├── .env.example                  # Environment variables template
│   ├── .env                          # Environment variables (git-ignored)
│   ├── .gitignore                    # Backend git ignore rules
│   │
│   ├── core/                         # Core game logic
│   │   ├── __init__.py
│   │   ├── quantum_engine.py         # Quantum mechanics implementation
│   │   ├── chess_rules.py            # Chess move validation
│   │   └── game_state.py             # Game state management
│   │
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   └── neo4j_client.py           # Neo4j database client
│   │
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   └── game_models.py            # Pydantic models
│   │
│   ├── routes/                       # API routes
│   │   ├── __init__.py
│   │   └── game_routes.py            # Game API endpoints
│   │
│   └── tests/                        # Backend tests
│       ├── conftest.py               # Test configuration
│       ├── test_quantum_engine.py    # Quantum engine tests
│       └── test_api.py               # API integration tests
│
├── frontend/                         # React Frontend
│   ├── index.html                    # HTML entry point
│   ├── package.json                  # Node dependencies
│   ├── vite.config.js                # Vite configuration
│   ├── Dockerfile                    # Frontend Docker image
│   ├── .gitignore                    # Frontend git ignore rules
│   │
│   └── src/
│       ├── main.jsx                  # React entry point
│       ├── App.jsx                   # Main application component
│       │
│       ├── components/               # React components
│       │   ├── Board.jsx             # Chess board component
│       │   ├── Piece.jsx             # Chess piece component
│       │   ├── GameInfo.jsx          # Game info panel
│       │   └── QuantumOverlay.jsx    # Quantum UI overlay
│       │
│       ├── hooks/                    # Custom React hooks
│       │   ├── useGameState.js       # Game state management hook
│       │   └── useWebSocket.js       # WebSocket connection hook
│       │
│       ├── services/                 # API services
│       │   └── api.js                # Backend API client
│       │
│       └── styles/                   # CSS stylesheets
│           ├── index.css             # Global styles
│           ├── App.css               # App layout styles
│           ├── Board.css             # Board styles
│           ├── Piece.css             # Piece styles
│           ├── GameInfo.css          # Info panel styles
│           └── QuantumOverlay.css    # Quantum overlay styles
│
├── docker-compose.yml                # Docker Compose configuration
├── README.md                         # Project documentation
├── SETUP.md                          # Setup instructions
├── LICENSE                           # MIT License
└── PROJECT_STRUCTURE.md              # This file
```

## 🔍 File Descriptions

### Backend Files

#### Core Application

- **`app.py`**: FastAPI application with WebSocket support, CORS, and API routes
- **`config.py`**: Centralized configuration using Pydantic settings

#### Core Logic

- **`quantum_engine.py`**: Implements superposition, entanglement, collapse, and observation
- **`chess_rules.py`**: Classical chess move validation and rule checking
- **`game_state.py`**: Game initialization, board state queries, turn management

#### Database

- **`neo4j_client.py`**: Neo4j connection, queries, and graph operations

#### Models

- **`game_models.py`**: Pydantic models for API requests/responses

#### API Routes

- **`game_routes.py`**: REST endpoints for game operations

#### Tests

- **`test_quantum_engine.py`**: Unit tests for quantum mechanics
- **`test_api.py`**: Integration tests for API endpoints

### Frontend Files

#### React Components

- **`App.jsx`**: Main orchestrator component
- **`Board.jsx`**: 8x8 chess board grid with piece rendering
- **`Piece.jsx`**: Individual chess pieces with quantum indicators
- **`GameInfo.jsx`**: Turn info, observations, and game rules
- **`QuantumOverlay.jsx`**: Quantum state visualization and controls

#### Hooks

- **`useGameState.js`**: Manages game state and API calls
- **`useWebSocket.js`**: WebSocket connection and real-time updates

#### Services

- **`api.js`**: HTTP client for backend API

#### Styles

- **`index.css`**: Global CSS variables and reset
- **`App.css`**: App layout and structure
- **`Board.css`**: Chess board grid styling
- **`Piece.css`**: Piece appearance and quantum effects
- **`GameInfo.css`**: Info panel styling
- **`QuantumOverlay.css`**: Quantum overlay with animations

### Configuration Files

- **`docker-compose.yml`**: Multi-container Docker setup
- **`Dockerfile`** (backend): Python FastAPI container
- **`Dockerfile`** (frontend): Node/Vite container
- **`requirements.txt`**: Python package dependencies
- **`package.json`**: Node package dependencies
- **`.env.example`**: Environment variable template
- **`.gitignore`**: Git ignore patterns

### Documentation

- **`README.md`**: Complete project documentation
- **`SETUP.md`**: Step-by-step setup guide
- **`LICENSE`**: MIT license
- **`PROJECT_STRUCTURE.md`**: This file

## 🚀 Quick Navigation

### To Add New Features

**Backend:**

1. Add logic to `core/` modules
2. Create API endpoint in `routes/game_routes.py`
3. Add tests in `tests/`

**Frontend:**

1. Create component in `components/`
2. Add styles in `styles/`
3. Update `App.jsx` to use component

### To Modify Quantum Mechanics

Edit: `backend/core/quantum_engine.py`

Key methods:

- `should_trigger_superposition()`: Trigger conditions
- `create_superposition()`: Create superposed state
- `collapse_superposition()`: Collapse logic
- `cascade_entangled_collapses()`: Entanglement correlation

### To Change Chess Rules

Edit: `backend/core/chess_rules.py`

Key methods:

- `is_valid_move()`: Move validation
- `_is_valid_move_pattern()`: Piece-specific patterns
- `get_valid_moves()`: Generate valid moves list

### To Modify Database Schema

Edit: `backend/db/neo4j_client.py`

Add queries in relevant modules:

- Game initialization: `game_state.py`
- Quantum operations: `quantum_engine.py`
- Move execution: `chess_rules.py`

### To Update UI

Edit components:

- Board layout: `Board.jsx` + `Board.css`
- Piece appearance: `Piece.jsx` + `Piece.css`
- Quantum effects: `QuantumOverlay.jsx` + `QuantumOverlay.css`
- Game info: `GameInfo.jsx` + `GameInfo.css`

## 📊 Technology Stack

### Backend

- **FastAPI**: Modern Python web framework
- **Neo4j**: Graph database for quantum relationships
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **python-chess**: Chess logic utilities
- **pytest**: Testing framework

### Frontend

- **React 18**: UI library
- **Vite**: Build tool and dev server
- **WebSocket**: Real-time communication
- **CSS3**: Styling with animations

### Database

- **Neo4j 5**: Graph database
- **Cypher**: Query language

### DevOps

- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## 🔗 Key Relationships

```
App.jsx
  ├── useGameState() → api.js → Backend API
  ├── useWebSocket() → WebSocket → Backend WS
  ├── Board.jsx → Piece.jsx
  ├── GameInfo.jsx
  └── QuantumOverlay.jsx

Backend API
  ├── game_routes.py
  │     ├── quantum_engine.py → neo4j_client.py
  │     ├── chess_rules.py → neo4j_client.py
  │     └── game_state.py → neo4j_client.py
  └── WebSocket → ConnectionManager
```

## 📝 Notes

- All backend code uses async/await for Neo4j operations
- Frontend uses React hooks for state management
- WebSocket enables real-time multiplayer (future enhancement)
- Neo4j graph structure models quantum relationships naturally
- CSS uses CSS custom properties (variables) for theming

---

**Last Updated**: 2024
**Version**: 1.0.0

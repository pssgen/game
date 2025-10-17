# ⚛️ Quantum Chess(Work in Progress)

A revolutionary chess variant that incorporates quantum mechanics - featuring **superposition**, **entanglement**, and **observation effects**. Built with React, FastAPI, and Neo4j graph database.

![Quantum Chess](https://img.shields.io/badge/Status-MVP-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![React](https://img.shields.io/badge/React-18+-blue)
![Neo4j](https://img.shields.io/badge/Neo4j-5.x-green)

## 🎮 Features

### Quantum Mechanics

- **Superposition**: Knights and pawns can exist in two positions simultaneously
- **Entanglement**: Pieces become correlated when superpositions overlap
- **Observer Effect**: Collapse superpositions with observation tokens (1 per turn)
- **Auto-Collapse**: Superpositions automatically collapse after 3 turns

### Game Features

- Real-time multiplayer via WebSocket
- Beautiful quantum visualizations with glowing effects
- Classical chess rules with quantum extensions
- Graph database for complex quantum relationships

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 16+** and npm
- **Neo4j 5.x** (Community or Enterprise)

### Installation

#### 1. Clone Repository

```bash
cd d:\chess
```

#### 2. Start Neo4j Database

**Option A: Using Neo4j Desktop**

1. Download from https://neo4j.com/download/
2. Create a new database
3. Set password and start the database
4. Note the bolt URI (usually `bolt://localhost:7687`)

**Option B: Using Docker**

```powershell
docker run -d `
  --name neo4j-quantum-chess `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/your_password `
  neo4j:5-community
```

#### 3. Setup Backend

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env

# Edit .env with your Neo4j credentials
notepad .env
```

**Update `.env` with your settings:**

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

#### 4. Setup Frontend

```powershell
# Navigate to frontend directory (from root)
cd ..\frontend

# Install dependencies
npm install
```

### Running the Application

#### Terminal 1: Start Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

Backend will run on: **http://localhost:8000**

#### Terminal 2: Start Frontend

```powershell
cd frontend
npm run dev
```

Frontend will run on: **http://localhost:5173**

#### Access the Game

Open your browser and navigate to: **http://localhost:5173**

## 📖 How to Play

### Basic Rules

1. **Start a New Game**: Click "Start New Game" button
2. **Make Moves**: Click a piece, then click a valid destination square
3. **Quantum Moves**: Knights and pawns create superposition (50/50 split)
4. **Observation**: Click the ⚛️ icon on superposed pieces to collapse (1 per turn)
5. **Entanglement**: Overlapping superpositions create 🔗 entangled pieces
6. **Win Condition**: Standard checkmate rules apply

### Quantum Mechanics Guide

#### Superposition

- **Trigger**: Moving knights or pawns (forward for pawns)
- **Effect**: Piece exists at two squares simultaneously
- **Collapse**: Use observation token or wait 3 turns for auto-collapse
- **Visual**: Blue glow + 50% probability badges

#### Entanglement

- **Trigger**: Two superposed pieces overlap on same square
- **Effect**: 70% correlated collapse (same direction)
- **Visual**: Pink glow + 🔗 icon
- **Break**: Distance >3 squares or capture

#### Observation

- **Tokens**: 1 per turn, refreshes each turn
- **Action**: Click "Observe & Collapse" button
- **Result**: Superposition collapses to one position randomly
- **Cascade**: Entangled partners collapse together

## 🏗️ Architecture

### Backend (FastAPI + Python)

```
backend/
├── app.py                 # Main FastAPI application
├── config.py              # Configuration management
├── core/
│   ├── quantum_engine.py  # Quantum mechanics logic
│   ├── chess_rules.py     # Chess move validation
│   └── game_state.py      # Game state management
├── db/
│   └── neo4j_client.py    # Neo4j database client
├── models/
│   └── game_models.py     # Pydantic data models
└── routes/
    └── game_routes.py     # API endpoints
```

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── App.jsx            # Main application component
│   ├── components/
│   │   ├── Board.jsx      # Chess board grid
│   │   ├── Piece.jsx      # Individual pieces
│   │   ├── GameInfo.jsx   # Info panel
│   │   └── QuantumOverlay.jsx  # Quantum UI
│   ├── hooks/
│   │   ├── useGameState.js     # Game state hook
│   │   └── useWebSocket.js     # WebSocket hook
│   ├── services/
│   │   └── api.js         # API service
│   └── styles/            # CSS modules
└── package.json
```

### Database (Neo4j)

- **Nodes**: Game, Piece, Position
- **Relationships**: OCCUPIES, ENTANGLED_WITH, IN_SUPERPOSITION, BELONGS_TO
- **Indexes**: piece_id, position_square, game_id

## 🔌 API Endpoints

### REST API

| Method | Endpoint                                 | Description           |
| ------ | ---------------------------------------- | --------------------- |
| POST   | `/game/new`                              | Create new game       |
| GET    | `/game/state/{game_id}`                  | Get game state        |
| POST   | `/game/move`                             | Make a move           |
| POST   | `/game/observe`                          | Observe quantum piece |
| GET    | `/game/valid-moves/{game_id}/{piece_id}` | Get valid moves       |

### WebSocket

**Endpoint**: `ws://localhost:8000/ws/{game_id}`

**Client Messages**:

```json
{
  "action": "move" | "observe" | "sync",
  "data": { ... }
}
```

**Server Messages**:

```json
{
  "event": "move_made" | "piece_observed" | "game_updated",
  "data": { ... }
}
```

## 🧪 Testing

### Run Backend Tests

```powershell
cd backend
pytest tests/ -v
```

### Run Frontend Tests

```powershell
cd frontend
npm run test
```

### Manual Testing Checklist

- [ ] Create new game successfully
- [ ] Make classical moves (Queen, Rook, Bishop)
- [ ] Trigger superposition (Knight, Pawn)
- [ ] Observe superposed piece
- [ ] Create entanglement (overlapping superpositions)
- [ ] Verify cascade collapse (entangled pieces)
- [ ] Auto-collapse after 3 turns
- [ ] Check multiplayer WebSocket sync

## 🐳 Docker Deployment (Optional)

### Build Docker Images

```powershell
# Backend
cd backend
docker build -t quantum-chess-backend .

# Frontend
cd ../frontend
docker build -t quantum-chess-frontend .
```

### Run with Docker Compose

```powershell
docker-compose up -d
```

## 🛠️ Development

### Backend Development

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Run with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```powershell
cd frontend

# Run with HMR (Hot Module Replacement)
npm run dev
```

### Database Console

Access Neo4j Browser: **http://localhost:7474**

Query examples:

```cypher
// View all games
MATCH (g:Game) RETURN g;

// View all pieces in a game
MATCH (p:Piece)-[:BELONGS_TO]->(g:Game {id: 'game-id'})
RETURN p;

// View superposed pieces
MATCH (p:Piece {quantum_state: 'superposed'})-[:OCCUPIES]->(pos:Position)
RETURN p, pos;
```

## 📝 Configuration

### Backend Environment Variables

| Variable                            | Default                 | Description                |
| ----------------------------------- | ----------------------- | -------------------------- |
| `NEO4J_URI`                         | `bolt://localhost:7687` | Neo4j connection URI       |
| `NEO4J_USER`                        | `neo4j`                 | Database username          |
| `NEO4J_PASSWORD`                    | `password`              | Database password          |
| `API_PORT`                          | `8000`                  | Backend API port           |
| `CORS_ORIGINS`                      | `http://localhost:5173` | Allowed CORS origins       |
| `MAX_SUPERPOSITION_DURATION`        | `3`                     | Turns before auto-collapse |
| `ENTANGLEMENT_CORRELATION_STRENGTH` | `0.7`                   | Correlation probability    |

### Frontend Environment Variables

Create `frontend/.env`:

```env
VITE_API_BASE_URL=/game
VITE_WS_BASE_URL=ws://localhost:8000
```

## 🚧 Roadmap

### Phase 1: MVP (Current)

- [x] Basic chess rules
- [x] Superposition (knights & pawns)
- [x] Entanglement
- [x] Observation mechanics
- [x] Frontend visualization

### Phase 2: Enhanced Gameplay

- [ ] AI opponent (Stockfish + Quantum heuristics)
- [ ] Check/checkmate with quantum pieces
- [ ] Pawn promotion in superposition
- [ ] En passant with quantum mechanics
- [ ] Castling rules

### Phase 3: Multiplayer

- [ ] User authentication
- [ ] Matchmaking system
- [ ] Game history and replay
- [ ] Leaderboard
- [ ] Tournament mode

### Phase 4: Advanced Features

- [ ] Quantum teleportation (special move)
- [ ] Multiple superposition states (3+ positions)
- [ ] Weighted probabilities
- [ ] Custom quantum rules
- [ ] Mobile app

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


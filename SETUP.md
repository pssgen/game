# 🚀 Setup Instructions for Quantum Chess

## Windows Setup (PowerShell)

### 1. Install Prerequisites

#### Python 3.9+

Download from: https://www.python.org/downloads/

```powershell
# Verify installation
python --version
```

#### Node.js 16+

Download from: https://nodejs.org/

```powershell
# Verify installation
node --version
npm --version
```

#### Neo4j Database

**Option 1: Neo4j Desktop (Recommended for beginners)**

1. Download from: https://neo4j.com/download/
2. Install and launch Neo4j Desktop
3. Click "New" → "Create a Local DBMS"
4. Set name: `quantum-chess`
5. Set password: `quantum_chess_password`
6. Click "Create"
7. Click "Start" to start the database

**Option 2: Docker**

```powershell
docker run -d `
  --name neo4j-quantum-chess `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/quantum_chess_password `
  neo4j:5-community
```

### 2. Setup Backend

```powershell
# Navigate to project directory
cd d:\chess\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
Copy-Item .env.example .env

# Edit .env with your Neo4j credentials
notepad .env
```

**Update `.env` file:**

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=quantum_chess_password
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

### 3. Setup Frontend

```powershell
# Navigate to frontend directory
cd ..\frontend

# Install dependencies
npm install

# (Optional) Create .env file if you need custom settings
# The proxy in vite.config.js handles API routing by default
```

### 4. Run the Application

#### Terminal 1: Start Backend

```powershell
cd d:\chess\backend
.\venv\Scripts\Activate.ps1
python app.py
```

You should see:

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ Neo4j connection established
✓ Server ready
```

#### Terminal 2: Start Frontend

```powershell
cd d:\chess\frontend
npm run dev
```

You should see:

```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 5. Access the Game

Open your browser and go to: **http://localhost:5173**

## Verification Checklist

- [ ] Neo4j database is running (check http://localhost:7474)
- [ ] Backend API is running (check http://localhost:8000)
- [ ] Frontend is running (check http://localhost:5173)
- [ ] Can create a new game
- [ ] Can make moves
- [ ] Can see quantum effects (superposition)

## Troubleshooting

### Neo4j Connection Failed

```
Error: Failed to connect to Neo4j
```

**Solution:**

1. Verify Neo4j is running: http://localhost:7474
2. Check credentials in `.env` match Neo4j database
3. Try connecting via Neo4j Browser first

### Port Already in Use

```
Error: Address already in use: 8000
```

**Solution:**

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Virtual Environment Activation Error

```
Error: Execution policy prevents script execution
```

**Solution:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module Not Found Error

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Build Errors

```
Error: Cannot find module
```

**Solution:**

```powershell
# Delete node_modules and reinstall
Remove-Item -Recurse -Force node_modules
npm install
```

## Development Tips

### Run with Auto-Reload

**Backend:**

```powershell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```powershell
npm run dev
```

(Already has HMR enabled)

### Access Neo4j Browser

Go to: **http://localhost:7474**

Run queries:

```cypher
// View all games
MATCH (g:Game) RETURN g LIMIT 10;

// View all pieces
MATCH (p:Piece) RETURN p LIMIT 20;

// View superposed pieces
MATCH (p:Piece {quantum_state: 'superposed'})-[:OCCUPIES]->(pos)
RETURN p, pos;
```

### View API Documentation

Go to: **http://localhost:8000/docs**

(FastAPI auto-generates Swagger UI)

## Next Steps

1. Read the [README.md](../README.md) for detailed game rules
2. Try making moves and observing quantum effects
3. Check the [API documentation](http://localhost:8000/docs)
4. Explore the codebase and make modifications
5. Run tests: `pytest backend/tests/`

## Need Help?

- Check the [README.md](../README.md) for more information
- Review the code comments in source files
- Create an issue on GitHub
- Check Neo4j logs in Neo4j Desktop

---

**Happy Quantum Chess Playing! 🎮⚛️**

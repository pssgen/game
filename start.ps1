# Quantum Chess - Quick Start Script for Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "⚛️  QUANTUM CHESS - QUICK START" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Neo4j is running
Write-Host "Checking Neo4j connection..." -ForegroundColor Yellow
$neo4jRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7474" -TimeoutSec 2 -ErrorAction SilentlyContinue
    $neo4jRunning = $true
    Write-Host "✓ Neo4j is running" -ForegroundColor Green
}
catch {
    Write-Host "✗ Neo4j is not running" -ForegroundColor Red
    Write-Host "  Please start Neo4j first (see SETUP.md)" -ForegroundColor Yellow
}

Write-Host ""

# Backend Setup
Write-Host "Setting up Backend..." -ForegroundColor Yellow
Write-Host "Location: d:\chess\backend" -ForegroundColor Gray

if (!(Test-Path "backend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv backend\venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
else {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
}

if (!(Test-Path "backend\.env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✓ .env file created (please update with your settings)" -ForegroundColor Green
    Write-Host "  Edit backend\.env with your Neo4j password" -ForegroundColor Yellow
}
else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

Write-Host ""

# Frontend Setup
Write-Host "Setting up Frontend..." -ForegroundColor Yellow
Write-Host "Location: d:\chess\frontend" -ForegroundColor Gray

if (!(Test-Path "frontend\node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📋 NEXT STEPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (!$neo4jRunning) {
    Write-Host "1. Start Neo4j database:" -ForegroundColor White
    Write-Host "   - Neo4j Desktop: Open and click 'Start'" -ForegroundColor Gray
    Write-Host "   - Docker: docker run -d --name neo4j-quantum-chess -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/quantum_chess_password neo4j:5-community" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "2. Start Backend (Terminal 1):" -ForegroundColor White
Write-Host "   cd d:\chess\backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Start Frontend (Terminal 2):" -ForegroundColor White
Write-Host "   cd d:\chess\frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""

Write-Host "4. Open Browser:" -ForegroundColor White
Write-Host "   http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📚 DOCUMENTATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "- README.md         : Complete documentation" -ForegroundColor Gray
Write-Host "- SETUP.md          : Detailed setup guide" -ForegroundColor Gray
Write-Host "- PROJECT_STRUCTURE : Code organization" -ForegroundColor Gray
Write-Host ""

Write-Host "Need help? Check SETUP.md for troubleshooting" -ForegroundColor Yellow
Write-Host ""
Write-Host "Happy Quantum Chess Playing! 🎮⚛️♟️" -ForegroundColor Green

/**
 * Main App Component
 * Orchestrates the entire Quantum Chess game
 */
import React, { useState, useCallback, useEffect } from "react";
import Board from "./components/Board";
import GameInfo from "./components/GameInfo";
import QuantumOverlay from "./components/QuantumOverlay";
import { useGameState } from "./hooks/useGameState";
import { useWebSocket } from "./hooks/useWebSocket";
import "./styles/App.css";

function App() {
  const {
    gameId,
    boardState,
    selectedPiece,
    selectedSquare,
    validMoves,
    observationsLeft,
    loading,
    error,
    initGame,
    makeMove,
    observePiece,
    selectPiece,
    setError,
  } = useGameState();

  const { isConnected, lastMessage } = useWebSocket(gameId);
  const [quantumPieceInFocus, setQuantumPieceInFocus] = useState(null);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    console.log("Processing WebSocket message:", lastMessage);

    // Handle different event types
    if (lastMessage.event === "move_made") {
      // Refresh board state after opponent's move
      // In a real multiplayer game, you'd update state from the message
      console.log("Opponent made a move");
    } else if (lastMessage.event === "piece_observed") {
      console.log("Piece observed:", lastMessage.data);
    }
  }, [lastMessage]);

  // Handle square clicks
  const handleSquareClick = useCallback(
    async (square, piece = null) => {
      if (!boardState) return;

      // If a piece is clicked directly
      if (piece) {
        // Check if it's the current player's piece
        if (piece.color !== boardState.game.active_player) {
          setError("Not your piece!");
          return;
        }

        // If piece is superposed, show quantum overlay
        if (piece.quantum_state === "superposed") {
          setQuantumPieceInFocus(piece);
          return;
        }

        // Select the piece
        await selectPiece(piece, square);
        return;
      }

      // If a square is clicked and we have a selected piece
      if (selectedPiece && selectedSquare) {
        // Check if it's a valid move
        if (validMoves.includes(square)) {
          try {
            await makeMove(selectedSquare, square);
            setQuantumPieceInFocus(null);
          } catch (err) {
            console.error("Move error:", err);
          }
        } else {
          // Deselect if clicked elsewhere
          await selectPiece(null, null);
        }
      }
    },
    [
      boardState,
      selectedPiece,
      selectedSquare,
      validMoves,
      makeMove,
      selectPiece,
      setError,
    ]
  );

  // Handle observation
  const handleObserve = useCallback(
    async (pieceId) => {
      if (observationsLeft <= 0) {
        setError("No observations remaining this turn!");
        return;
      }

      try {
        await observePiece(pieceId);
        setQuantumPieceInFocus(null);
      } catch (err) {
        console.error("Observation error:", err);
      }
    },
    [observationsLeft, observePiece, setError]
  );

  // Start new game
  const handleNewGame = useCallback(() => {
    setQuantumPieceInFocus(null);
    initGame();
  }, [initGame]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>⚛️ Quantum Chess</h1>
        <div className="connection-status">
          <span
            className={`status-indicator ${
              isConnected ? "connected" : "disconnected"
            }`}
          >
            {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
          </span>
        </div>
      </header>

      <main className="app-main">
        <div className="game-container">
          <GameInfo
            gameState={boardState}
            observationsLeft={observationsLeft}
            onNewGame={handleNewGame}
          />

          <div className="board-container">
            {!gameId ? (
              <div className="welcome-screen">
                <h2>Welcome to Quantum Chess!</h2>
                <p>A chess variant with quantum mechanics</p>
                <button className="start-button" onClick={handleNewGame}>
                  ▶️ Start New Game
                </button>
              </div>
            ) : loading ? (
              <div className="loading-screen">
                <div className="spinner"></div>
                <p>Loading...</p>
              </div>
            ) : (
              <Board
                boardState={boardState}
                selectedSquare={selectedSquare}
                validMoves={validMoves}
                onSquareClick={handleSquareClick}
              />
            )}

            {error && (
              <div className="error-message">
                ⚠️ {error}
                <button onClick={() => setError(null)}>✕</button>
              </div>
            )}
          </div>

          {/* Quantum overlay for superposed/entangled pieces */}
          {quantumPieceInFocus && (
            <QuantumOverlay
              piece={quantumPieceInFocus}
              positions={quantumPieceInFocus.positions}
              entangledWith={quantumPieceInFocus.entangled_with}
              onObserve={handleObserve}
              canObserve={observationsLeft > 0}
            />
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Quantum Chess v1.0 | Built with React + FastAPI + Neo4j</p>
      </footer>
    </div>
  );
}

export default App;

/**
 * Game Info Panel Component
 * Displays turn info, observations, and game status
 */
import React from "react";
import "../styles/GameInfo.css";

function GameInfo({ gameState, observationsLeft, onNewGame }) {
  if (!gameState) {
    return (
      <div className="game-info">
        <h2>Quantum Chess</h2>
        <p>Click "New Game" to start</p>
      </div>
    );
  }

  const { game } = gameState;

  return (
    <div className="game-info">
      <h2>Quantum Chess</h2>

      <div className="info-section">
        <h3>Game Status</h3>
        <div className="info-row">
          <span className="label">Turn:</span>
          <span className="value">{game.current_turn}</span>
        </div>
        <div className="info-row">
          <span className="label">Active Player:</span>
          <span className={`value player-${game.active_player}`}>
            {game.active_player.charAt(0).toUpperCase() +
              game.active_player.slice(1)}
          </span>
        </div>
        <div className="info-row">
          <span className="label">Status:</span>
          <span className="value">{game.status}</span>
        </div>
      </div>

      <div className="info-section">
        <h3>Quantum Mechanics</h3>
        <div className="info-row">
          <span className="label">Observations Left:</span>
          <span className={`value ${observationsLeft === 0 ? "depleted" : ""}`}>
            {observationsLeft}
          </span>
        </div>

        <div className="quantum-legend">
          <h4>Quantum Abilities:</h4>
          <div className="legend-item">
            <span className="icon">⚛️</span>
            <span>Superposition (Knights & Pawns)</span>
          </div>
          <div className="legend-item">
            <span className="icon">🔗</span>
            <span>Entanglement (70% correlation)</span>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h3>Rules</h3>
        <ul className="rules-list">
          <li>Knights & Pawns can enter superposition</li>
          <li>Superposition auto-collapses after 3 turns</li>
          <li>1 observation per turn to collapse pieces</li>
          <li>Entangled pieces collapse together</li>
        </ul>
      </div>

      <button className="new-game-button" onClick={onNewGame}>
        🎮 New Game
      </button>
    </div>
  );
}

export default GameInfo;

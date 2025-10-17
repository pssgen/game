/**
 * Quantum Overlay Component
 * Shows quantum state information and observation controls
 */
import React from "react";
import "../styles/QuantumOverlay.css";

function QuantumOverlay({
  piece,
  positions,
  entangledWith,
  onObserve,
  canObserve,
}) {
  if (!piece) return null;

  const isSuperposed = piece.quantum_state === "superposed";
  const isEntangled = piece.quantum_state === "entangled";

  if (!isSuperposed && !isEntangled) return null;

  return (
    <div className="quantum-overlay">
      {/* Superposition indicator */}
      {isSuperposed && (
        <div className="superposition-indicator">
          <div className="quantum-badge">
            <span className="quantum-icon">⚛️</span>
            <span>Superposition</span>
          </div>

          <div className="probability-display">
            <p className="info-text">
              This piece exists in two states simultaneously:
            </p>
            {positions.map((pos, idx) => (
              <div key={pos.square} className="position-prob">
                <span className="square-name">{pos.square}</span>
                <span className="probability">
                  {Math.round(pos.probability * 100)}%
                </span>
              </div>
            ))}
          </div>

          <button
            className="observe-button"
            onClick={() => onObserve(piece.id)}
            disabled={!canObserve}
            title={
              !canObserve
                ? "No observations remaining this turn"
                : "Collapse superposition"
            }
          >
            🔍 Observe & Collapse
          </button>
        </div>
      )}

      {/* Entanglement indicator */}
      {isEntangled && (
        <div className="entanglement-indicator">
          <div className="quantum-badge entangled">
            <span className="quantum-icon">🔗</span>
            <span>Entangled with {entangledWith.length} piece(s)</span>
          </div>

          <p className="info-text">
            Entangled pieces collapse together with 70% correlation
          </p>

          <div className="entangled-pieces">
            {entangledWith.map((partnerId) => (
              <div key={partnerId} className="partner-piece">
                {partnerId}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Visual quantum particles effect */}
      {isSuperposed && (
        <div className="quantum-particles">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="particle"
              style={{
                "--delay": `${i * 0.2}s`,
                "--x": `${(i % 2 === 0 ? 1 : -1) * (10 + i * 5)}px`,
                "--y": `${-20 - i * 5}px`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default QuantumOverlay;

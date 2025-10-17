/**
 * Chess Piece Component
 * Displays individual pieces with quantum state indicators
 */
import React from "react";
import "../styles/Piece.css";

const PIECE_SYMBOLS = {
  king: { white: "♔", black: "♚" },
  queen: { white: "♕", black: "♛" },
  rook: { white: "♖", black: "♜" },
  bishop: { white: "♗", black: "♝" },
  knight: { white: "♘", black: "♞" },
  pawn: { white: "♙", black: "♟" },
  observer: { white: "👁️", black: "👁️" }, // Observer uses eye symbol
};

function Piece({ piece, position, isSelected, isGhost, onClick }) {
  if (!piece) return null;

  const symbol = PIECE_SYMBOLS[piece.type]?.[piece.color] || "?";

  const classNames = [
    "chess-piece",
    piece.color,
    piece.quantum_state,
    isSelected ? "selected" : "",
    isGhost ? "ghost" : "",
    piece.quantum_ability ? "quantum-enabled" : "",
    piece.type === "observer" ? "observer-piece-special" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const opacity = isGhost && position ? position.probability : 1;

  return (
    <div
      className={classNames}
      onClick={onClick}
      data-piece-id={piece.id}
      style={{ opacity }}
      title={`${piece.color} ${piece.type} (${piece.quantum_state})`}
    >
      <span className="piece-symbol">{symbol}</span>

      {piece.quantum_state !== "classical" && (
        <span className="quantum-indicator">
          {piece.quantum_state === "superposed" && "⚛️"}
          {piece.quantum_state === "entangled" && "🔗"}
        </span>
      )}

      {isGhost && position && (
        <div className="probability-badge">
          {Math.round(position.probability * 100)}%
        </div>
      )}

      {piece.type === "observer" && (
        <span className="observer-badge-inline">OBS</span>
      )}
    </div>
  );
}

export default Piece;

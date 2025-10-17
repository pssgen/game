import React from "react";
import "./ObservationZone.css";

function ObservationZone({ zoneSquares, affectedPieces }) {
  // Create a map of affected pieces by square for quick lookup
  const affectedBySquare = {};
  if (affectedPieces) {
    affectedPieces.forEach((piece) => {
      affectedBySquare[piece.position] = piece;
    });
  }

  return (
    <div className="observation-zone-overlay">
      {/* Highlight observation zone squares */}
      {zoneSquares &&
        zoneSquares.map((square) => {
          const isAffected = affectedBySquare[square];
          const [file, rank] = [square[0], square[1]];
          const fileIndex = file.charCodeAt(0) - 97; // a=0, b=1, ...
          const rankIndex = 8 - parseInt(rank); // 8=0, 7=1, ...

          return (
            <div
              key={square}
              className={`zone-square ${isAffected ? "has-affected" : ""}`}
              style={{
                gridColumn: fileIndex + 1,
                gridRow: rankIndex + 1,
              }}
            >
              <div className="zone-highlight" />
              {isAffected && (
                <div className="affected-indicator">
                  <span className="collapse-icon">⚡</span>
                </div>
              )}
            </div>
          );
        })}

      {/* Scanning effect */}
      <div className="scanner-line" />
    </div>
  );
}

export default ObservationZone;

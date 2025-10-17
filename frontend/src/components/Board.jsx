/**
 * Chess Board Component
 * Renders the 8x8 board with pieces and handles square clicks
 */
import React, { useMemo } from "react";
import Piece from "./Piece";
import "../styles/Board.css";

function Board({ boardState, selectedSquare, validMoves, onSquareClick }) {
  // Create 8x8 grid of squares
  const squares = useMemo(() => {
    const result = [];
    for (let rank = 8; rank >= 1; rank--) {
      for (let file of "abcdefgh") {
        const square = `${file}${rank}`;
        result.push(square);
      }
    }
    return result;
  }, []);

  // Get pieces at each square
  const squarePieces = useMemo(() => {
    if (!boardState?.pieces) return {};

    const map = {};

    boardState.pieces.forEach((piece) => {
      if (piece.captured) return;

      piece.positions.forEach((pos) => {
        if (!map[pos.square]) {
          map[pos.square] = [];
        }
        map[pos.square].push({ piece, position: pos });
      });
    });

    return map;
  }, [boardState]);

  const isValidMove = (square) => validMoves.includes(square);
  const isSelected = (square) => square === selectedSquare;

  const getSquareColor = (square) => {
    const file = square.charCodeAt(0) - 97; // a=0, b=1, ...
    const rank = parseInt(square[1]);
    return (file + rank) % 2 === 0 ? "dark" : "light";
  };

  return (
    <div className="chess-board">
      <div className="board-grid">
        {squares.map((square) => {
          const pieces = squarePieces[square] || [];
          const squareColor = getSquareColor(square);
          const isHighlighted = isValidMove(square);
          const isSelectedSquare = isSelected(square);

          const classNames = [
            "square",
            squareColor,
            isHighlighted ? "valid-move" : "",
            isSelectedSquare ? "selected" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <div
              key={square}
              className={classNames}
              data-square={square}
              onClick={() => onSquareClick(square)}
            >
              <span className="square-label">{square}</span>

              {/* Render all pieces at this square (classical + ghosts) */}
              {pieces.map(({ piece, position }, idx) => (
                <Piece
                  key={`${piece.id}-${idx}`}
                  piece={piece}
                  position={position}
                  isSelected={isSelectedSquare && !position.is_ghost}
                  isGhost={position.is_ghost}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSquareClick(square, piece);
                  }}
                />
              ))}

              {isHighlighted && <div className="move-indicator" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Board;

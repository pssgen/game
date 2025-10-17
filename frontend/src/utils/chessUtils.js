/**
 * Chess utility functions for common operations
 * Provides helper functions for square calculations, move validation,
 * game state conversions, and common chess operations
 */

/**
 * Convert algebraic notation to board coordinates
 * @param {string} square - Algebraic notation (e.g., 'a1', 'h8')
 * @returns {{row: number, col: number}} Board coordinates (0-7)
 */
export function squareToCoords(square) {
  if (!square || square.length !== 2) {
    throw new Error("Invalid square notation");
  }

  const file = square[0].toLowerCase();
  const rank = square[1];

  if (file < "a" || file > "h" || rank < "1" || rank > "8") {
    throw new Error("Square out of bounds");
  }

  return {
    row: 8 - parseInt(rank), // Convert to 0-based, top-to-bottom
    col: file.charCodeAt(0) - "a".charCodeAt(0), // Convert to 0-based
  };
}

/**
 * Convert board coordinates to algebraic notation
 * @param {number} row - Row index (0-7)
 * @param {number} col - Column index (0-7)
 * @returns {string} Algebraic notation (e.g., 'a1', 'h8')
 */
export function coordsToSquare(row, col) {
  if (row < 0 || row > 7 || col < 0 || col > 7) {
    throw new Error("Coordinates out of bounds");
  }

  const file = String.fromCharCode("a".charCodeAt(0) + col);
  const rank = String(8 - row);

  return file + rank;
}

/**
 * Check if a square is within board bounds
 * @param {string} square - Algebraic notation
 * @returns {boolean} True if square is valid
 */
export function isValidSquare(square) {
  if (!square || square.length !== 2) return false;

  const file = square[0].toLowerCase();
  const rank = square[1];

  return file >= "a" && file <= "h" && rank >= "1" && rank <= "8";
}

/**
 * Calculate distance between two squares
 * @param {string} square1 - First square
 * @param {string} square2 - Second square
 * @returns {number} Manhattan distance
 */
export function squareDistance(square1, square2) {
  const coords1 = squareToCoords(square1);
  const coords2 = squareToCoords(square2);

  return (
    Math.abs(coords1.row - coords2.row) + Math.abs(coords1.col - coords2.col)
  );
}

/**
 * Get all squares in a straight line between two squares
 * @param {string} from - Starting square
 * @param {string} to - Ending square
 * @returns {string[]} Array of squares in the path (excluding start and end)
 */
export function getSquaresBetween(from, to) {
  const fromCoords = squareToCoords(from);
  const toCoords = squareToCoords(to);

  const rowDiff = toCoords.row - fromCoords.row;
  const colDiff = toCoords.col - fromCoords.col;

  // Check if move is in a straight line (horizontal, vertical, or diagonal)
  if (
    rowDiff !== 0 &&
    colDiff !== 0 &&
    Math.abs(rowDiff) !== Math.abs(colDiff)
  ) {
    return []; // Not a straight line
  }

  const squares = [];
  const steps = Math.max(Math.abs(rowDiff), Math.abs(colDiff));

  if (steps <= 1) return squares; // Adjacent squares or same square

  const rowStep = rowDiff === 0 ? 0 : rowDiff / Math.abs(rowDiff);
  const colStep = colDiff === 0 ? 0 : colDiff / Math.abs(colDiff);

  for (let i = 1; i < steps; i++) {
    const row = fromCoords.row + i * rowStep;
    const col = fromCoords.col + i * colStep;
    squares.push(coordsToSquare(row, col));
  }

  return squares;
}

/**
 * Get all squares within a certain distance from a center square
 * @param {string} center - Center square
 * @param {number} distance - Maximum distance
 * @returns {string[]} Array of squares within distance
 */
export function getSquaresWithinDistance(center, distance) {
  const centerCoords = squareToCoords(center);
  const squares = [];

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const square = coordsToSquare(row, col);
      if (squareDistance(center, square) <= distance && square !== center) {
        squares.push(square);
      }
    }
  }

  return squares;
}

/**
 * Check if two squares are adjacent (including diagonally)
 * @param {string} square1 - First square
 * @param {string} square2 - Second square
 * @returns {boolean} True if squares are adjacent
 */
export function areSquaresAdjacent(square1, square2) {
  const coords1 = squareToCoords(square1);
  const coords2 = squareToCoords(square2);

  const rowDiff = Math.abs(coords1.row - coords2.row);
  const colDiff = Math.abs(coords1.col - coords2.col);

  return rowDiff <= 1 && colDiff <= 1 && (rowDiff > 0 || colDiff > 0);
}

/**
 * Get the color of a square on the chessboard
 * @param {string} square - Square in algebraic notation
 * @returns {'light'|'dark'} Square color
 */
export function getSquareColor(square) {
  const coords = squareToCoords(square);
  return (coords.row + coords.col) % 2 === 0 ? "dark" : "light";
}

/**
 * Parse move notation into from/to squares
 * @param {string} move - Move in various formats (e.g., 'e2e4', 'e2-e4', 'e4')
 * @returns {{from: string, to: string}|null} Parsed move or null if invalid
 */
export function parseMove(move) {
  if (!move || typeof move !== "string") return null;

  // Remove spaces and convert to lowercase
  move = move.replace(/\s+/g, "").toLowerCase();

  // Handle formats like 'e2e4' or 'e2-e4'
  const longFormat = move.match(/^([a-h][1-8])[-]?([a-h][1-8])$/);
  if (longFormat) {
    return {
      from: longFormat[1],
      to: longFormat[2],
    };
  }

  // Handle short format like 'e4' (would need additional context for from square)
  const shortFormat = move.match(/^([a-h][1-8])$/);
  if (shortFormat) {
    // This would need game state context to determine the from square
    return null;
  }

  return null;
}

/**
 * Format move for display
 * @param {{from: string, to: string}} move - Move object
 * @param {string} format - Display format ('short', 'long', 'algebraic')
 * @returns {string} Formatted move string
 */
export function formatMove(move, format = "long") {
  if (!move || !move.from || !move.to) return "";

  switch (format) {
    case "short":
      return move.to;
    case "algebraic":
      return `${move.from}-${move.to}`;
    case "long":
    default:
      return `${move.from} to ${move.to}`;
  }
}

/**
 * Check if a piece can potentially move to a square based on piece type
 * This is a basic check that doesn't consider board state or other pieces
 * @param {string} pieceType - Type of piece ('pawn', 'rook', 'knight', etc.)
 * @param {string} from - Starting square
 * @param {string} to - Target square
 * @param {string} color - Piece color ('white' or 'black')
 * @returns {boolean} True if move is theoretically possible for this piece type
 */
export function canPieceReachSquare(pieceType, from, to, color = "white") {
  if (from === to) return false;

  const fromCoords = squareToCoords(from);
  const toCoords = squareToCoords(to);
  const rowDiff = toCoords.row - fromCoords.row;
  const colDiff = toCoords.col - fromCoords.col;
  const absRowDiff = Math.abs(rowDiff);
  const absColDiff = Math.abs(colDiff);

  switch (pieceType.toLowerCase()) {
    case "pawn":
      const direction = color === "white" ? -1 : 1;
      const startRow = color === "white" ? 6 : 1;

      // Forward move
      if (colDiff === 0) {
        if (rowDiff === direction) return true; // One square forward
        if (fromCoords.row === startRow && rowDiff === 2 * direction)
          return true; // Two squares from start
      }
      // Diagonal capture
      if (absColDiff === 1 && rowDiff === direction) return true;
      return false;

    case "rook":
      return rowDiff === 0 || colDiff === 0;

    case "bishop":
      return absRowDiff === absColDiff;

    case "queen":
      return rowDiff === 0 || colDiff === 0 || absRowDiff === absColDiff;

    case "king":
      return absRowDiff <= 1 && absColDiff <= 1;

    case "knight":
      return (
        (absRowDiff === 2 && absColDiff === 1) ||
        (absRowDiff === 1 && absColDiff === 2)
      );

    case "observer":
      // Observer can move like a king but has special observation abilities
      return absRowDiff <= 1 && absColDiff <= 1;

    default:
      return false;
  }
}

/**
 * Generate all possible moves for a piece type from a given square
 * This is a basic generation that doesn't consider board state
 * @param {string} pieceType - Type of piece
 * @param {string} square - Starting square
 * @param {string} color - Piece color
 * @returns {string[]} Array of possible target squares
 */
export function generatePossibleMoves(pieceType, square, color = "white") {
  const moves = [];

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const targetSquare = coordsToSquare(row, col);
      if (canPieceReachSquare(pieceType, square, targetSquare, color)) {
        moves.push(targetSquare);
      }
    }
  }

  return moves;
}

/**
 * Validate that a game state object has required properties
 * @param {object} gameState - Game state object to validate
 * @returns {boolean} True if game state is valid
 */
export function isValidGameState(gameState) {
  if (!gameState || typeof gameState !== "object") return false;

  const requiredProps = ["board", "current_player", "game_id"];
  return requiredProps.every((prop) => gameState.hasOwnProperty(prop));
}

/**
 * Deep clone a game state object to prevent mutations
 * @param {object} gameState - Game state to clone
 * @returns {object} Cloned game state
 */
export function cloneGameState(gameState) {
  try {
    return JSON.parse(JSON.stringify(gameState));
  } catch (error) {
    console.error("Failed to clone game state:", error);
    return null;
  }
}

/**
 * Get all squares of a specific color
 * @param {'light'|'dark'} color - Square color
 * @returns {string[]} Array of squares with the specified color
 */
export function getSquaresByColor(color) {
  const squares = [];

  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const square = coordsToSquare(row, col);
      if (getSquareColor(square) === color) {
        squares.push(square);
      }
    }
  }

  return squares;
}

/**
 * Check if a move is a castling move
 * @param {{from: string, to: string}} move - Move to check
 * @returns {'kingside'|'queenside'|false} Castling type or false
 */
export function isCastlingMove(move) {
  if (!move || !move.from || !move.to) return false;

  // King moving two squares horizontally from starting position
  if (
    (move.from === "e1" && move.to === "g1") ||
    (move.from === "e8" && move.to === "g8")
  ) {
    return "kingside";
  }
  if (
    (move.from === "e1" && move.to === "c1") ||
    (move.from === "e8" && move.to === "c8")
  ) {
    return "queenside";
  }

  return false;
}

/**
 * Get file (column) letter from square
 * @param {string} square - Square in algebraic notation
 * @returns {string} File letter (a-h)
 */
export function getFile(square) {
  return square[0];
}

/**
 * Get rank (row) number from square
 * @param {string} square - Square in algebraic notation
 * @returns {string} Rank number (1-8)
 */
export function getRank(square) {
  return square[1];
}

/**
 * Check if a square is on the edge of the board
 * @param {string} square - Square to check
 * @returns {boolean} True if square is on board edge
 */
export function isEdgeSquare(square) {
  const file = getFile(square);
  const rank = getRank(square);

  return file === "a" || file === "h" || rank === "1" || rank === "8";
}

/**
 * Check if a square is a corner square
 * @param {string} square - Square to check
 * @returns {boolean} True if square is a corner
 */
export function isCornerSquare(square) {
  return ["a1", "a8", "h1", "h8"].includes(square);
}

/**
 * Get the center squares of the board
 * @returns {string[]} Array of center squares
 */
export function getCenterSquares() {
  return ["d4", "d5", "e4", "e5"];
}

/**
 * Check if a square is in the center of the board
 * @param {string} square - Square to check
 * @returns {boolean} True if square is in center
 */
export function isCenterSquare(square) {
  return getCenterSquares().includes(square);
}

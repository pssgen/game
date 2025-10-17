/**
 * Game state utility functions
 * Handles game state management, conversions, and validation
 */

/**
 * Create initial game state for a new game
 * @param {string} gameId - Unique game identifier
 * @param {string} player1 - First player identifier
 * @param {string} player2 - Second player identifier
 * @returns {object} Initial game state
 */
export function createInitialGameState(gameId, player1, player2) {
  return {
    game_id: gameId,
    players: {
      white: player1,
      black: player2,
    },
    current_player: "white",
    status: "active",
    board: createInitialBoard(),
    move_history: [],
    captured_pieces: {
      white: [],
      black: [],
    },
    special_flags: {
      white_can_castle_kingside: true,
      white_can_castle_queenside: true,
      black_can_castle_kingside: true,
      black_can_castle_queenside: true,
      en_passant_target: null,
    },
    quantum_state: {
      entangled_pairs: [],
      quantum_pieces: [],
    },
    observers: [],
    created_at: Date.now(),
    last_move_at: Date.now(),
  };
}

/**
 * Create initial chess board with standard piece placement
 * @returns {object} Initial board state
 */
function createInitialBoard() {
  const board = {};

  // Place pawns
  for (let file of "abcdefgh") {
    board[`${file}2`] = {
      type: "pawn",
      color: "white",
      id: `white-pawn-${file}`,
    };
    board[`${file}7`] = {
      type: "pawn",
      color: "black",
      id: `black-pawn-${file}`,
    };
  }

  // Place other pieces
  const pieceOrder = [
    "rook",
    "knight",
    "bishop",
    "queen",
    "king",
    "bishop",
    "knight",
    "rook",
  ];

  for (let i = 0; i < 8; i++) {
    const file = String.fromCharCode("a".charCodeAt(0) + i);
    const piece = pieceOrder[i];

    board[`${file}1`] = {
      type: piece,
      color: "white",
      id: `white-${piece}-${file}1`,
    };
    board[`${file}8`] = {
      type: piece,
      color: "black",
      id: `black-${piece}-${file}8`,
    };
  }

  return board;
}

/**
 * Get piece at a specific square
 * @param {object} gameState - Current game state
 * @param {string} square - Square to check
 * @returns {object|null} Piece at square or null if empty
 */
export function getPieceAt(gameState, square) {
  if (!gameState?.board || !square) return null;

  return gameState.board[square] || null;
}

/**
 * Check if a square is occupied
 * @param {object} gameState - Current game state
 * @param {string} square - Square to check
 * @returns {boolean} True if square is occupied
 */
export function isSquareOccupied(gameState, square) {
  return getPieceAt(gameState, square) !== null;
}

/**
 * Get all pieces of a specific color
 * @param {object} gameState - Current game state
 * @param {string} color - Piece color ('white' or 'black')
 * @returns {object[]} Array of pieces with their positions
 */
export function getPiecesByColor(gameState, color) {
  if (!gameState?.board) return [];

  const pieces = [];

  for (const [position, piece] of Object.entries(gameState.board)) {
    if (piece && piece.color === color) {
      pieces.push({
        ...piece,
        position,
      });
    }
  }

  return pieces;
}

/**
 * Find the king of a specific color
 * @param {object} gameState - Current game state
 * @param {string} color - King color
 * @returns {object|null} King piece with position or null if not found
 */
export function findKing(gameState, color) {
  const pieces = getPiecesByColor(gameState, color);
  return pieces.find((piece) => piece.type === "king") || null;
}

/**
 * Get all possible piece positions (handles quantum pieces)
 * @param {object} piece - Piece to get positions for
 * @returns {string[]} Array of possible positions
 */
export function getPiecePositions(piece) {
  if (!piece) return [];

  if (piece.is_quantum && piece.superposition_states) {
    return piece.superposition_states.map((state) => state.position);
  }

  return piece.position ? [piece.position] : [];
}

/**
 * Apply a move to the game state
 * @param {object} gameState - Current game state
 * @param {object} move - Move to apply
 * @returns {object} New game state after move
 */
export function applyMove(gameState, move) {
  const newState = JSON.parse(JSON.stringify(gameState)); // Deep clone

  if (!move.from || !move.to) {
    throw new Error("Invalid move: missing from or to position");
  }

  const piece = newState.board[move.from];
  if (!piece) {
    throw new Error(`No piece at ${move.from}`);
  }

  // Handle capture
  const capturedPiece = newState.board[move.to];
  if (capturedPiece) {
    const oppositeColor = piece.color === "white" ? "black" : "white";
    newState.captured_pieces[oppositeColor].push(capturedPiece);
  }

  // Move piece
  newState.board[move.to] = piece;
  delete newState.board[move.from];

  // Update move history
  newState.move_history.push({
    ...move,
    piece_type: piece.type,
    captured: capturedPiece ? capturedPiece.type : null,
    timestamp: Date.now(),
  });

  // Switch current player
  newState.current_player =
    newState.current_player === "white" ? "black" : "white";
  newState.last_move_at = Date.now();

  return newState;
}

/**
 * Undo the last move
 * @param {object} gameState - Current game state
 * @returns {object} Game state with last move undone
 */
export function undoLastMove(gameState) {
  if (!gameState.move_history || gameState.move_history.length === 0) {
    throw new Error("No moves to undo");
  }

  const newState = JSON.parse(JSON.stringify(gameState));
  const lastMove = newState.move_history.pop();

  // Move piece back
  const piece = newState.board[lastMove.to];
  newState.board[lastMove.from] = piece;

  // Restore captured piece if any
  if (lastMove.captured) {
    const capturedPieceColor = piece.color === "white" ? "black" : "white";
    const capturedPiece = newState.captured_pieces[capturedPieceColor].pop();
    if (capturedPiece) {
      newState.board[lastMove.to] = capturedPiece;
    } else {
      delete newState.board[lastMove.to];
    }
  } else {
    delete newState.board[lastMove.to];
  }

  // Switch current player back
  newState.current_player =
    newState.current_player === "white" ? "black" : "white";

  return newState;
}

/**
 * Check if the game is over
 * @param {object} gameState - Current game state
 * @returns {{isOver: boolean, reason: string, winner: string|null}} Game over status
 */
export function checkGameOver(gameState) {
  if (!gameState) {
    return { isOver: false, reason: "", winner: null };
  }

  // Check explicit game status
  if (gameState.status === "checkmate") {
    const winner = gameState.current_player === "white" ? "black" : "white";
    return { isOver: true, reason: "checkmate", winner };
  }

  if (gameState.status === "stalemate") {
    return { isOver: true, reason: "stalemate", winner: null };
  }

  if (gameState.status === "draw") {
    return { isOver: true, reason: "draw", winner: null };
  }

  // Check for insufficient material
  if (isInsufficientMaterial(gameState)) {
    return { isOver: true, reason: "insufficient_material", winner: null };
  }

  // Check for 50-move rule
  if (isFiftyMoveRule(gameState)) {
    return { isOver: true, reason: "fifty_move_rule", winner: null };
  }

  // Check for threefold repetition
  if (isThreefoldRepetition(gameState)) {
    return { isOver: true, reason: "threefold_repetition", winner: null };
  }

  return { isOver: false, reason: "", winner: null };
}

/**
 * Check for insufficient material to checkmate
 * @param {object} gameState - Current game state
 * @returns {boolean} True if insufficient material
 */
function isInsufficientMaterial(gameState) {
  const whitePieces = getPiecesByColor(gameState, "white");
  const blackPieces = getPiecesByColor(gameState, "black");

  const whiteMaterial = calculateMaterial(whitePieces);
  const blackMaterial = calculateMaterial(blackPieces);

  // King vs King
  if (whiteMaterial.total === 0 && blackMaterial.total === 0) return true;

  // King and Bishop vs King or King and Knight vs King
  if (
    whiteMaterial.total <= 3 &&
    whiteMaterial.pieces.length <= 1 &&
    blackMaterial.total === 0
  )
    return true;
  if (
    blackMaterial.total <= 3 &&
    blackMaterial.pieces.length <= 1 &&
    whiteMaterial.total === 0
  )
    return true;

  return false;
}

/**
 * Calculate material value for pieces
 * @param {object[]} pieces - Array of pieces
 * @returns {object} Material calculation
 */
function calculateMaterial(pieces) {
  const values = { pawn: 1, knight: 3, bishop: 3, rook: 5, queen: 9 };
  let total = 0;
  const pieceCounts = {};
  const pieceTypes = [];

  for (const piece of pieces) {
    if (piece.type !== "king") {
      const value = values[piece.type] || 0;
      total += value;
      pieceCounts[piece.type] = (pieceCounts[piece.type] || 0) + 1;
      pieceTypes.push(piece.type);
    }
  }

  return {
    total,
    pieces: pieceTypes,
    counts: pieceCounts,
  };
}

/**
 * Check for 50-move rule
 * @param {object} gameState - Current game state
 * @returns {boolean} True if 50-move rule applies
 */
function isFiftyMoveRule(gameState) {
  if (!gameState.move_history || gameState.move_history.length < 100)
    return false;

  // Check last 100 half-moves (50 full moves)
  const recentMoves = gameState.move_history.slice(-100);

  for (const move of recentMoves) {
    // Reset counter on pawn move or capture
    if (move.piece_type === "pawn" || move.captured) {
      return false;
    }
  }

  return true;
}

/**
 * Check for threefold repetition
 * @param {object} gameState - Current game state
 * @returns {boolean} True if position has occurred three times
 */
function isThreefoldRepetition(gameState) {
  // This is a simplified implementation
  // In practice, you'd need to track position hashes
  return false;
}

/**
 * Get valid moves for a piece at a specific position
 * @param {object} gameState - Current game state
 * @param {string} position - Position of piece
 * @returns {string[]} Array of valid move destinations
 */
export function getValidMoves(gameState, position) {
  const piece = getPieceAt(gameState, position);
  if (!piece) return [];

  // This is a basic implementation - in practice you'd need
  // full move generation logic for each piece type
  const moves = [];

  // Add basic move validation here
  // This would integrate with the chess rules engine

  return moves;
}

/**
 * Format game state for display
 * @param {object} gameState - Game state to format
 * @returns {object} Formatted game state
 */
export function formatGameStateForDisplay(gameState) {
  if (!gameState) return null;

  return {
    gameId: gameState.game_id,
    currentPlayer: gameState.current_player,
    status: gameState.status,
    moveCount: gameState.move_history?.length || 0,
    lastMove: gameState.move_history?.slice(-1)[0] || null,
    isGameOver: checkGameOver(gameState).isOver,
    players: gameState.players,
    captures: {
      white: gameState.captured_pieces?.white?.length || 0,
      black: gameState.captured_pieces?.black?.length || 0,
    },
  };
}

/**
 * Convert board state to FEN notation (simplified)
 * @param {object} gameState - Game state
 * @returns {string} FEN string
 */
export function toFEN(gameState) {
  if (!gameState?.board) return "";

  let fen = "";

  // Board position
  for (let rank = 8; rank >= 1; rank--) {
    let emptyCount = 0;
    let rankStr = "";

    for (
      let file = "a";
      file <= "h";
      file = String.fromCharCode(file.charCodeAt(0) + 1)
    ) {
      const square = file + rank;
      const piece = gameState.board[square];

      if (piece) {
        if (emptyCount > 0) {
          rankStr += emptyCount;
          emptyCount = 0;
        }

        let pieceChar = piece.type[0];
        if (piece.color === "white") {
          pieceChar = pieceChar.toUpperCase();
        }
        rankStr += pieceChar;
      } else {
        emptyCount++;
      }
    }

    if (emptyCount > 0) {
      rankStr += emptyCount;
    }

    fen += rankStr;
    if (rank > 1) fen += "/";
  }

  // Active color
  fen += ` ${gameState.current_player[0]}`;

  // TODO: Add castling, en passant, halfmove, fullmove
  fen += " - - 0 1";

  return fen;
}

/**
 * Get game statistics
 * @param {object} gameState - Game state
 * @returns {object} Game statistics
 */
export function getGameStatistics(gameState) {
  if (!gameState) return {};

  const stats = {
    totalMoves: gameState.move_history?.length || 0,
    captures: {
      white: gameState.captured_pieces?.white?.length || 0,
      black: gameState.captured_pieces?.black?.length || 0,
    },
    gameDuration: Date.now() - (gameState.created_at || Date.now()),
    quantumPieces: 0,
    entangledPairs: gameState.quantum_state?.entangled_pairs?.length || 0,
    observers: gameState.observers?.length || 0,
  };

  // Count quantum pieces
  if (gameState.board) {
    for (const piece of Object.values(gameState.board)) {
      if (piece?.is_quantum) {
        stats.quantumPieces++;
      }
    }
  }

  return stats;
}

/**
 * Validate game state structure
 * @param {object} gameState - Game state to validate
 * @returns {{valid: boolean, errors: string[]}} Validation result
 */
export function validateGameState(gameState) {
  const errors = [];

  if (!gameState) {
    return { valid: false, errors: ["Game state is null or undefined"] };
  }

  // Required fields
  if (!gameState.game_id) errors.push("Missing game_id");
  if (!gameState.current_player) errors.push("Missing current_player");
  if (!gameState.board) errors.push("Missing board");

  // Validate current player
  if (
    gameState.current_player &&
    !["white", "black"].includes(gameState.current_player)
  ) {
    errors.push("Invalid current_player value");
  }

  // Validate board structure
  if (gameState.board && typeof gameState.board !== "object") {
    errors.push("Board must be an object");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export default {
  createInitialGameState,
  getPieceAt,
  isSquareOccupied,
  getPiecesByColor,
  findKing,
  getPiecePositions,
  applyMove,
  undoLastMove,
  checkGameOver,
  getValidMoves,
  formatGameStateForDisplay,
  toFEN,
  getGameStatistics,
  validateGameState,
};

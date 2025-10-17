/**
 * Quantum mechanics utility functions
 * Handles quantum state calculations, probability distributions,
 * and quantum piece operations for the quantum chess game
 */

/**
 * Calculate the probability of a quantum piece being at a specific position
 * @param {object} quantumPiece - Quantum piece with superposition states
 * @param {string} position - Position to check
 * @returns {number} Probability (0-1)
 */
export function getProbabilityAtPosition(quantumPiece, position) {
  if (!quantumPiece || !quantumPiece.superposition_states) {
    return 0;
  }

  const state = quantumPiece.superposition_states.find(
    (s) => s.position === position
  );
  return state ? state.probability : 0;
}

/**
 * Get all positions where a quantum piece might exist
 * @param {object} quantumPiece - Quantum piece
 * @returns {string[]} Array of possible positions
 */
export function getPossiblePositions(quantumPiece) {
  if (!quantumPiece || !quantumPiece.superposition_states) {
    return [];
  }

  return quantumPiece.superposition_states.map((state) => state.position);
}

/**
 * Calculate the total probability mass for a quantum piece
 * Should always equal 1.0 for a valid quantum state
 * @param {object} quantumPiece - Quantum piece
 * @returns {number} Total probability
 */
export function getTotalProbability(quantumPiece) {
  if (!quantumPiece || !quantumPiece.superposition_states) {
    return 0;
  }

  return quantumPiece.superposition_states.reduce((total, state) => {
    return total + (state.probability || 0);
  }, 0);
}

/**
 * Check if a quantum piece is in a valid quantum state
 * @param {object} quantumPiece - Quantum piece to validate
 * @returns {boolean} True if state is valid
 */
export function isValidQuantumState(quantumPiece) {
  if (!quantumPiece) return false;

  // Classical pieces are always valid
  if (!quantumPiece.is_quantum || !quantumPiece.superposition_states) {
    return true;
  }

  // Check that probabilities sum to approximately 1.0
  const totalProb = getTotalProbability(quantumPiece);
  const tolerance = 0.0001;

  return Math.abs(totalProb - 1.0) < tolerance;
}

/**
 * Normalize quantum state probabilities to sum to 1.0
 * @param {object} quantumPiece - Quantum piece to normalize
 * @returns {object} Normalized quantum piece
 */
export function normalizeQuantumState(quantumPiece) {
  if (!quantumPiece || !quantumPiece.superposition_states) {
    return quantumPiece;
  }

  const totalProb = getTotalProbability(quantumPiece);

  if (totalProb === 0) {
    console.warn("Cannot normalize quantum state with zero probability");
    return quantumPiece;
  }

  const normalized = {
    ...quantumPiece,
    superposition_states: quantumPiece.superposition_states.map((state) => ({
      ...state,
      probability: state.probability / totalProb,
    })),
  };

  return normalized;
}

/**
 * Calculate entanglement strength between two quantum pieces
 * @param {object} piece1 - First quantum piece
 * @param {object} piece2 - Second quantum piece
 * @returns {number} Entanglement strength (0-1)
 */
export function calculateEntanglementStrength(piece1, piece2) {
  if (!piece1?.entangled_with || !piece2?.entangled_with) {
    return 0;
  }

  // Check if pieces are entangled with each other
  const piece1Entangled = piece1.entangled_with.includes(piece2.id);
  const piece2Entangled = piece2.entangled_with.includes(piece1.id);

  if (!piece1Entangled || !piece2Entangled) {
    return 0;
  }

  // Calculate based on shared positions and probability correlations
  const positions1 = getPossiblePositions(piece1);
  const positions2 = getPossiblePositions(piece2);
  const sharedPositions = positions1.filter((pos) => positions2.includes(pos));

  if (sharedPositions.length === 0) {
    return 0.1; // Minimal entanglement
  }

  // Calculate correlation strength
  let correlation = 0;
  for (const pos of sharedPositions) {
    const prob1 = getProbabilityAtPosition(piece1, pos);
    const prob2 = getProbabilityAtPosition(piece2, pos);
    correlation += prob1 * prob2;
  }

  return Math.min(correlation, 1.0);
}

/**
 * Check if two quantum pieces are entangled
 * @param {object} piece1 - First piece
 * @param {object} piece2 - Second piece
 * @returns {boolean} True if pieces are entangled
 */
export function areEntangled(piece1, piece2) {
  return calculateEntanglementStrength(piece1, piece2) > 0;
}

/**
 * Calculate the quantum coherence of a piece's superposition
 * Higher coherence means the piece is more "quantum-like"
 * @param {object} quantumPiece - Quantum piece
 * @returns {number} Coherence value (0-1)
 */
export function calculateCoherence(quantumPiece) {
  if (
    !quantumPiece?.superposition_states ||
    quantumPiece.superposition_states.length <= 1
  ) {
    return 0; // Classical piece or collapsed state
  }

  const states = quantumPiece.superposition_states;
  const n = states.length;

  // Calculate entropy-based coherence
  let entropy = 0;
  for (const state of states) {
    if (state.probability > 0) {
      entropy -= state.probability * Math.log2(state.probability);
    }
  }

  // Normalize by maximum possible entropy
  const maxEntropy = Math.log2(n);
  return maxEntropy > 0 ? entropy / maxEntropy : 0;
}

/**
 * Calculate the collapse probability for observation
 * @param {object} quantumPiece - Quantum piece being observed
 * @param {string} observerPosition - Position of observer
 * @param {number} observationRange - Range of observation
 * @returns {number} Probability of collapse (0-1)
 */
export function calculateCollapseprobability(
  quantumPiece,
  observerPosition,
  observationRange = 2
) {
  if (!quantumPiece?.superposition_states) {
    return 0; // Already classical
  }

  // Import chess utils for distance calculation
  const { squareDistance } = require("./chessUtils");

  let totalProbabilityInRange = 0;

  for (const state of quantumPiece.superposition_states) {
    const distance = squareDistance(state.position, observerPosition);
    if (distance <= observationRange) {
      totalProbabilityInRange += state.probability;
    }
  }

  // Base collapse probability plus probability mass in observation range
  const baseCollapseProb = 0.3;
  const rangeMultiplier = 0.7;

  return Math.min(
    baseCollapseProb + rangeMultiplier * totalProbabilityInRange,
    1.0
  );
}

/**
 * Simulate quantum measurement/collapse
 * @param {object} quantumPiece - Quantum piece to collapse
 * @param {string} forcedPosition - Optional position to force collapse to
 * @returns {object} Collapsed piece state
 */
export function simulateCollapse(quantumPiece, forcedPosition = null) {
  if (!quantumPiece?.superposition_states) {
    return quantumPiece; // Already classical
  }

  let collapsedPosition;

  if (forcedPosition) {
    // Force collapse to specific position if valid
    const validPosition = quantumPiece.superposition_states.find(
      (state) => state.position === forcedPosition
    );
    collapsedPosition = validPosition ? forcedPosition : null;
  }

  if (!collapsedPosition) {
    // Random collapse based on probability distribution
    const random = Math.random();
    let cumulativeProb = 0;

    for (const state of quantumPiece.superposition_states) {
      cumulativeProb += state.probability;
      if (random <= cumulativeProb) {
        collapsedPosition = state.position;
        break;
      }
    }
  }

  // Return collapsed state
  return {
    ...quantumPiece,
    is_quantum: false,
    position: collapsedPosition,
    superposition_states: null,
    collapsed_at: Date.now(),
  };
}

/**
 * Calculate quantum interference effects between moves
 * @param {object[]} possibleMoves - Array of possible moves with probabilities
 * @returns {object[]} Moves with interference effects applied
 */
export function calculateQuantumInterference(possibleMoves) {
  if (!possibleMoves || possibleMoves.length <= 1) {
    return possibleMoves;
  }

  // Simple interference model: constructive for similar moves, destructive for opposing
  const modifiedMoves = possibleMoves.map((move) => {
    let interferenceEffect = 1.0;

    for (const otherMove of possibleMoves) {
      if (move === otherMove) continue;

      // Calculate similarity between moves
      const similarity = calculateMoveSimilarity(move, otherMove);

      // Constructive interference for similar moves
      if (similarity > 0.7) {
        interferenceEffect *= 1.1;
      }
      // Destructive interference for opposing moves
      else if (similarity < 0.3) {
        interferenceEffect *= 0.9;
      }
    }

    return {
      ...move,
      probability: Math.min(move.probability * interferenceEffect, 1.0),
    };
  });

  // Renormalize probabilities
  const totalProb = modifiedMoves.reduce(
    (sum, move) => sum + move.probability,
    0
  );

  if (totalProb > 0) {
    return modifiedMoves.map((move) => ({
      ...move,
      probability: move.probability / totalProb,
    }));
  }

  return modifiedMoves;
}

/**
 * Calculate similarity between two moves for interference calculation
 * @param {object} move1 - First move
 * @param {object} move2 - Second move
 * @returns {number} Similarity score (0-1)
 */
function calculateMoveSimilarity(move1, move2) {
  if (!move1.from || !move1.to || !move2.from || !move2.to) {
    return 0;
  }

  const { squareDistance } = require("./chessUtils");

  // Compare starting and ending positions
  const fromDistance = squareDistance(move1.from, move2.from);
  const toDistance = squareDistance(move1.to, move2.to);

  // Similarity decreases with distance
  const maxDistance = 7; // Maximum possible distance on board
  const fromSimilarity = 1 - fromDistance / maxDistance;
  const toSimilarity = 1 - toDistance / maxDistance;

  return (fromSimilarity + toSimilarity) / 2;
}

/**
 * Create a quantum superposition from classical piece
 * @param {object} classicalPiece - Classical chess piece
 * @param {string[]} positions - Positions for superposition
 * @param {number[]} probabilities - Corresponding probabilities (optional)
 * @returns {object} Quantum piece in superposition
 */
export function createSuperposition(
  classicalPiece,
  positions,
  probabilities = null
) {
  if (!positions || positions.length === 0) {
    return classicalPiece;
  }

  // Use equal probabilities if none provided
  if (!probabilities) {
    const equalProb = 1.0 / positions.length;
    probabilities = new Array(positions.length).fill(equalProb);
  }

  // Normalize probabilities
  const totalProb = probabilities.reduce((sum, prob) => sum + prob, 0);
  const normalizedProbs = probabilities.map((prob) => prob / totalProb);

  const superpositionStates = positions.map((position, index) => ({
    position,
    probability: normalizedProbs[index],
    created_at: Date.now(),
  }));

  return {
    ...classicalPiece,
    is_quantum: true,
    superposition_states: superpositionStates,
    quantum_created_at: Date.now(),
  };
}

/**
 * Check if a quantum state is decoherent (effectively classical)
 * @param {object} quantumPiece - Quantum piece to check
 * @returns {boolean} True if state is decoherent
 */
export function isDecoherent(quantumPiece) {
  if (!quantumPiece?.is_quantum || !quantumPiece.superposition_states) {
    return true; // Already classical
  }

  // Check if one state has overwhelming probability
  const maxProb = Math.max(
    ...quantumPiece.superposition_states.map((s) => s.probability)
  );
  return maxProb > 0.95;
}

/**
 * Calculate quantum tunneling probability
 * Used for special quantum moves that bypass classical rules
 * @param {object} quantumPiece - Quantum piece attempting tunneling
 * @param {string} targetPosition - Target position for tunneling
 * @param {object[]} obstacles - Pieces blocking the path
 * @returns {number} Tunneling probability (0-1)
 */
export function calculateTunnelingProbability(
  quantumPiece,
  targetPosition,
  obstacles = []
) {
  if (!quantumPiece?.is_quantum) {
    return 0; // Classical pieces cannot tunnel
  }

  const coherence = calculateCoherence(quantumPiece);
  const baseProb = coherence * 0.1; // Base tunneling probability

  // Reduce probability based on number of obstacles
  const obstacleReduction = Math.pow(0.8, obstacles.length);

  return baseProb * obstacleReduction;
}

/**
 * Validate quantum piece data structure
 * @param {object} piece - Piece to validate
 * @returns {{valid: boolean, errors: string[]}} Validation result
 */
export function validateQuantumPiece(piece) {
  const errors = [];

  if (!piece) {
    return { valid: false, errors: ["Piece is null or undefined"] };
  }

  // Required fields
  if (!piece.id) errors.push("Missing piece ID");
  if (!piece.type) errors.push("Missing piece type");
  if (!piece.color) errors.push("Missing piece color");

  // Quantum-specific validation
  if (piece.is_quantum) {
    if (!piece.superposition_states) {
      errors.push("Quantum piece missing superposition states");
    } else {
      // Validate superposition states
      if (!Array.isArray(piece.superposition_states)) {
        errors.push("Superposition states must be an array");
      } else {
        for (let i = 0; i < piece.superposition_states.length; i++) {
          const state = piece.superposition_states[i];
          if (!state.position) {
            errors.push(`State ${i} missing position`);
          }
          if (
            typeof state.probability !== "number" ||
            state.probability < 0 ||
            state.probability > 1
          ) {
            errors.push(`State ${i} has invalid probability`);
          }
        }

        // Check probability sum
        if (!isValidQuantumState(piece)) {
          errors.push("Probabilities do not sum to 1.0");
        }
      }
    }
  } else {
    // Classical piece validation
    if (!piece.position) {
      errors.push("Classical piece missing position");
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export default {
  getProbabilityAtPosition,
  getPossiblePositions,
  getTotalProbability,
  isValidQuantumState,
  normalizeQuantumState,
  calculateEntanglementStrength,
  areEntangled,
  calculateCoherence,
  calculateCollapseprobability,
  simulateCollapse,
  calculateQuantumInterference,
  createSuperposition,
  isDecoherent,
  calculateTunnelingProbability,
  validateQuantumPiece,
};

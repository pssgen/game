/**
 * API Service for Quantum Chess
 * Handles all HTTP requests to the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/game";

class GameAPI {
  /**
   * Create a new game
   * @returns {Promise<{game_id: string, initial_state: object}>}
   */
  async createGame() {
    const response = await fetch(`${API_BASE_URL}/new`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create game: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get current game state
   * @param {string} gameId
   * @returns {Promise<object>}
   */
  async getGameState(gameId) {
    const response = await fetch(`${API_BASE_URL}/state/${gameId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch game state: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Make a move
   * @param {string} gameId
   * @param {object} moveData - {from_square, to_square, player}
   * @returns {Promise<object>}
   */
  async makeMove(gameId, moveData) {
    const response = await fetch(`${API_BASE_URL}/move`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        game_id: gameId,
        ...moveData,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      // Handle new error format
      throw new Error(error.message || error.detail || "Move failed");
    }

    return response.json();
  }

  /**
   * Observe a quantum piece (collapse superposition)
   * @param {string} gameId
   * @param {string} pieceId
   * @param {string} player
   * @returns {Promise<object>}
   */
  async observePiece(gameId, pieceId, player) {
    const response = await fetch(`${API_BASE_URL}/observe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        game_id: gameId,
        piece_id: pieceId,
        player,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      // Handle new error format
      throw new Error(error.message || error.detail || "Observation failed");
    }

    return response.json();
  }

  /**
   * Get valid moves for a piece
   * @param {string} gameId
   * @param {string} pieceId
   * @returns {Promise<{valid_moves: string[], quantum_moves: string[], capture_moves: string[]}>}
   */
  async getValidMoves(gameId, pieceId) {
    const response = await fetch(
      `${API_BASE_URL}/valid-moves/${gameId}/${pieceId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get valid moves: ${response.statusText}`);
    }

    return response.json();
  }

  // ==================== OBSERVER METHODS ====================

  /**
   * Move Observer piece
   * @param {string} gameId
   * @param {object} moveData - {observer_id, to_square}
   * @returns {Promise<{success: boolean, new_position: string, observed_pieces: string[], collapsed_states: object[], new_state: object}>}
   */
  async moveObserver(gameId, moveData) {
    const response = await fetch(`${API_BASE_URL}/move/observer`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        game_id: gameId,
        ...moveData,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      // Handle new error format
      throw new Error(error.message || error.detail || "Observer move failed");
    }

    return response.json();
  }

  /**
   * Get Observer's observation zone
   * @param {string} observerId
   * @param {string} gameId
   * @returns {Promise<{observer_id: string, current_position: string, zone_squares: string[], affected_pieces: object[]}>}
   */
  async getObservationZone(observerId, gameId) {
    const response = await fetch(
      `${API_BASE_URL}/observer/${observerId}/zone?game_id=${gameId}`
    );

    if (!response.ok) {
      const error = await response.json();
      // Handle new error format
      throw new Error(
        error.message ||
          error.detail ||
          `Failed to get observation zone: ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Get Observer statistics
   * @param {string} observerId
   * @returns {Promise<{observations_made: number, total_pieces_affected: number, observation_history: object[]}>}
   */
  async getObserverStats(observerId) {
    const response = await fetch(
      `${API_BASE_URL}/observer/${observerId}/stats`
    );

    if (!response.ok) {
      const error = await response.json();
      // Handle new error format
      throw new Error(
        error.message ||
          error.detail ||
          `Failed to get observer stats: ${response.statusText}`
      );
    }

    return response.json();
  }
}

export const gameAPI = new GameAPI();

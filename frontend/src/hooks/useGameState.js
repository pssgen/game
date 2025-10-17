/**
 * Game State Management Hook
 * Handles all game state logic and API calls
 */
import { useState, useEffect, useCallback } from "react";
import { gameAPI } from "../services/api";

export function useGameState() {
  const [gameId, setGameId] = useState(null);
  const [boardState, setBoardState] = useState(null);
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [validMoves, setValidMoves] = useState([]);
  const [observationsLeft, setObservationsLeft] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize new game
  const initGame = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await gameAPI.createGame();
      console.log("Game created:", response);
      setGameId(response.game_id);
      setBoardState(response.initial_state);

      // Set initial observations
      if (response.initial_state?.game) {
        setObservationsLeft(
          response.initial_state.game.active_player === "white"
            ? response.initial_state.game.white_observations_left
            : response.initial_state.game.black_observations_left
        );
      }
    } catch (err) {
      console.error("Failed to initialize game:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch current game state
  const fetchGameState = useCallback(
    async (id = gameId) => {
      if (!id) return;

      try {
        const state = await gameAPI.getGameState(id);
        setBoardState(state);

        // Update observations for current player
        const obs =
          state.game.active_player === "white"
            ? state.game.white_observations_left
            : state.game.black_observations_left;
        setObservationsLeft(obs);
      } catch (err) {
        console.error("Failed to fetch game state:", err);
        setError(err.message);
      }
    },
    [gameId]
  );

  // Make a move
  const makeMove = useCallback(
    async (fromSquare, toSquare) => {
      if (!gameId || !boardState) return;

      setLoading(true);
      setError(null);

      try {
        const response = await gameAPI.makeMove(gameId, {
          from_square: fromSquare,
          to_square: toSquare,
          player: boardState.game.active_player,
        });

        console.log("Move response:", response);
        setBoardState(response.new_state);
        setSelectedPiece(null);
        setSelectedSquare(null);
        setValidMoves([]);

        // Update observations
        const obs =
          response.new_state.game.active_player === "white"
            ? response.new_state.game.white_observations_left
            : response.new_state.game.black_observations_left;
        setObservationsLeft(obs);

        return response;
      } catch (err) {
        console.error("Move failed:", err);
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [gameId, boardState]
  );

  // Observe (collapse) a quantum piece
  const observePiece = useCallback(
    async (pieceId) => {
      if (!gameId || !boardState || observationsLeft <= 0) return;

      setLoading(true);
      setError(null);

      try {
        const response = await gameAPI.observePiece(
          gameId,
          pieceId,
          boardState.game.active_player
        );

        console.log("Observation response:", response);
        setBoardState(response.new_state);
        setObservationsLeft((prev) => prev - 1);

        return response;
      } catch (err) {
        console.error("Observation failed:", err);
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [gameId, boardState, observationsLeft]
  );

  // Get valid moves for selected piece
  const getValidMoves = useCallback(
    async (pieceId) => {
      if (!gameId) return [];

      try {
        const moves = await gameAPI.getValidMoves(gameId, pieceId);
        setValidMoves(moves.valid_moves || []);
        return moves;
      } catch (err) {
        console.error("Failed to get valid moves:", err);
        return [];
      }
    },
    [gameId]
  );

  // Select a piece
  const selectPiece = useCallback(
    async (piece, square) => {
      if (!piece || piece.quantum_state === "superposed") {
        // Can't move superposed pieces
        setSelectedPiece(null);
        setSelectedSquare(null);
        setValidMoves([]);
        return;
      }

      setSelectedPiece(piece);
      setSelectedSquare(square);
      await getValidMoves(piece.id);
    },
    [getValidMoves]
  );

  return {
    gameId,
    boardState,
    selectedPiece,
    selectedSquare,
    validMoves,
    observationsLeft,
    loading,
    error,
    initGame,
    fetchGameState,
    makeMove,
    observePiece,
    selectPiece,
    setError,
  };
}

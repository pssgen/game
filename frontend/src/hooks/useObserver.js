import { useState, useCallback } from "react";

/**
 * Hook for managing Observer piece state and actions
 */
export function useObserver(gameId, apiService) {
  const [observationZone, setObservationZone] = useState([]);
  const [affectedPieces, setAffectedPieces] = useState([]);
  const [lastObservation, setLastObservation] = useState(null);

  /**
   * Move Observer piece to a new square
   */
  const moveObserver = useCallback(
    async (observerId, toSquare) => {
      if (!gameId) {
        throw new Error("No active game");
      }

      try {
        const response = await apiService.moveObserver(gameId, {
          observer_id: observerId,
          to_square: toSquare,
        });

        // Store observation results
        setLastObservation({
          observed_pieces: response.observed_pieces,
          collapsed_states: response.collapsed_states,
          timestamp: Date.now(),
        });

        // Clear zone preview after move
        setObservationZone([]);
        setAffectedPieces([]);

        return response;
      } catch (error) {
        console.error("Observer move failed:", error);
        throw error;
      }
    },
    [gameId, apiService]
  );

  /**
   * Get preview of Observer's observation zone
   */
  const getObservationZonePreview = useCallback(
    async (observerId) => {
      if (!gameId) return { zone_squares: [], affected_pieces: [] };

      try {
        const response = await apiService.getObservationZone(
          observerId,
          gameId
        );
        setObservationZone(response.zone_squares || []);
        setAffectedPieces(response.affected_pieces || []);
        return response;
      } catch (error) {
        console.error("Failed to get observation zone:", error);
        return { zone_squares: [], affected_pieces: [] };
      }
    },
    [gameId, apiService]
  );

  /**
   * Get Observer statistics
   */
  const getObserverStats = useCallback(
    async (observerId) => {
      try {
        const response = await apiService.getObserverStats(observerId);
        return response;
      } catch (error) {
        console.error("Failed to get observer stats:", error);
        return {
          observations_made: 0,
          total_pieces_affected: 0,
          observation_history: [],
        };
      }
    },
    [apiService]
  );

  /**
   * Clear observation zone preview
   */
  const clearObservationZone = useCallback(() => {
    setObservationZone([]);
    setAffectedPieces([]);
  }, []);

  return {
    observationZone,
    affectedPieces,
    lastObservation,
    moveObserver,
    getObservationZonePreview,
    getObserverStats,
    clearObservationZone,
  };
}

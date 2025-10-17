/**
 * WebSocket Hook for Real-time Game Updates
 */
import { useEffect, useRef, useCallback, useState } from "react";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

export function useWebSocket(gameId) {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    if (!gameId) return;

    console.log(`Connecting to WebSocket: ${WS_BASE_URL}/ws/${gameId}`);
    ws.current = new WebSocket(`${WS_BASE_URL}/ws/${gameId}`);

    ws.current.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);

      // Request initial sync
      ws.current.send(
        JSON.stringify({
          action: "sync",
          data: {},
        })
      );
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("WebSocket message:", message);
        setLastMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);

      // Attempt reconnection after 3 seconds
      reconnectTimeout.current = setTimeout(() => {
        console.log("Attempting to reconnect...");
        connect();
      }, 3000);
    };
  }, [gameId]);

  const sendMessage = useCallback((action, data) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action, data }));
    } else {
      console.warn("WebSocket not connected");
    }
  }, []);

  const makeMove = useCallback(
    (fromSquare, toSquare, player) => {
      sendMessage("move", {
        from_square: fromSquare,
        to_square: toSquare,
        player,
      });
    },
    [sendMessage]
  );

  const observePiece = useCallback(
    (pieceId) => {
      sendMessage("observe", {
        piece_id: pieceId,
      });
    },
    [sendMessage]
  );

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    makeMove,
    observePiece,
  };
}

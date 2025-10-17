"""
Custom Exceptions for Quantum Chess
Provides specific error types and detailed error messages
"""
from typing import Optional, Dict, Any


class QuantumChessError(Exception):
    """Base exception for all Quantum Chess errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)


class GameNotFoundError(QuantumChessError):
    """Raised when a game is not found"""
    
    def __init__(self, game_id: str):
        super().__init__(
            f"Game '{game_id}' not found",
            "GAME_NOT_FOUND",
            {"game_id": game_id}
        )


class PieceNotFoundError(QuantumChessError):
    """Raised when a piece is not found"""
    
    def __init__(self, piece_id: str):
        super().__init__(
            f"Piece '{piece_id}' not found",
            "PIECE_NOT_FOUND",
            {"piece_id": piece_id}
        )


class InvalidMoveError(QuantumChessError):
    """Raised when a move is invalid according to chess rules"""
    
    def __init__(self, from_square: str, to_square: str, reason: str, piece_id: str = None):
        super().__init__(
            f"Invalid move {from_square} -> {to_square}: {reason}",
            "INVALID_MOVE",
            {
                "from_square": from_square,
                "to_square": to_square,
                "reason": reason,
                "piece_id": piece_id
            }
        )


class QuantumStateError(QuantumChessError):
    """Raised when there's an issue with quantum states"""
    
    def __init__(self, piece_id: str, current_state: str, attempted_operation: str):
        super().__init__(
            f"Cannot perform '{attempted_operation}' on piece '{piece_id}' in state '{current_state}'",
            "QUANTUM_STATE_ERROR",
            {
                "piece_id": piece_id,
                "current_state": current_state,
                "attempted_operation": attempted_operation
            }
        )


class DatabaseError(QuantumChessError):
    """Raised when there's a database operation error"""
    
    def __init__(self, operation: str, original_error: str):
        super().__init__(
            f"Database error during {operation}: {original_error}",
            "DATABASE_ERROR",
            {"operation": operation, "original_error": original_error}
        )


class TurnOrderError(QuantumChessError):
    """Raised when a move is attempted out of turn"""
    
    def __init__(self, game_id: str, active_player: str, attempted_player: str):
        super().__init__(
            f"It's {active_player}'s turn, but {attempted_player} attempted to move",
            "TURN_ORDER_ERROR",
            {
                "game_id": game_id,
                "active_player": active_player,
                "attempted_player": attempted_player
            }
        )


class ObservationError(QuantumChessError):
    """Raised when there's an issue with quantum observation"""
    
    def __init__(self, piece_id: str, reason: str):
        super().__init__(
            f"Cannot observe piece '{piece_id}': {reason}",
            "OBSERVATION_ERROR",
            {"piece_id": piece_id, "reason": reason}
        )


class GameStateError(QuantumChessError):
    """Raised when game is in an invalid state for the requested operation"""
    
    def __init__(self, game_id: str, current_status: str, requested_operation: str):
        super().__init__(
            f"Cannot perform '{requested_operation}' on game '{game_id}' with status '{current_status}'",
            "GAME_STATE_ERROR",
            {
                "game_id": game_id,
                "current_status": current_status,
                "requested_operation": requested_operation
            }
        )


class ValidationError(QuantumChessError):
    """Raised when input validation fails"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Invalid value for '{field}': {value} ({reason})",
            "VALIDATION_ERROR",
            {"field": field, "value": value, "reason": reason}
        )


class ConfigurationError(QuantumChessError):
    """Raised when there's a configuration issue"""
    
    def __init__(self, setting: str, issue: str):
        super().__init__(
            f"Configuration error for '{setting}': {issue}",
            "CONFIGURATION_ERROR",
            {"setting": setting, "issue": issue}
        )
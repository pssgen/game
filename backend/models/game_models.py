"""
Pydantic models for Quantum Chess API
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
import neo4j.time


class PositionData(BaseModel):
    """Position information for a piece"""
    square: str = Field(..., description="Algebraic notation (e.g., 'e4')")
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    is_ghost: bool = Field(default=False, description="True if probabilistic position")


class PieceData(BaseModel):
    """Complete piece information"""
    id: str = Field(..., description="Unique piece ID (e.g., 'knight-w-1')")
    type: Literal["king", "queen", "rook", "bishop", "knight", "pawn", "observer"]
    color: Literal["white", "black"]
    quantum_ability: bool = Field(default=False)
    quantum_state: Literal["classical", "superposed", "entangled"] = "classical"
    captured: bool = False
    move_count: int = 0
    positions: List[PositionData] = []
    entangled_with: List[str] = Field(default_factory=list)
    observations_made: Optional[int] = Field(default=None, description="Observer-specific: count of observations")
    observation_range: Optional[int] = Field(default=1, description="Observer-specific: observation radius")


class GameInfo(BaseModel):
    """Game metadata"""
    id: str
    current_turn: int = 1
    active_player: Literal["white", "black"] = "white"
    status: Literal["active", "checkmate", "stalemate", "draw"] = "active"
    white_observations_left: int = 1
    black_observations_left: int = 1
    created_at: Optional[datetime] = None

    @validator('created_at', pre=True)
    def convert_neo4j_datetime(cls, v):
        if isinstance(v, neo4j.time.DateTime):
            return v.to_native()
        return v


class GameState(BaseModel):
    """Complete game state"""
    game: GameInfo
    pieces: List[PieceData]


class MoveRequest(BaseModel):
    """Request to make a chess move"""
    game_id: str
    from_square: str = Field(..., pattern=r"^[a-h][1-8]$")
    to_square: str = Field(..., pattern=r"^[a-h][1-8]$")
    player: Literal["white", "black"]
    promotion: Optional[Literal["queen", "rook", "bishop", "knight"]] = None


class QuantumEvent(BaseModel):
    """Quantum mechanics event that occurred during move"""
    type: Literal[
        "superposition_created",
        "superposition_collapsed",
        "entanglement_formed",
        "entanglement_broken",
        "cascade_collapse"
    ]
    piece_id: str
    details: dict = Field(default_factory=dict)


class MoveResponse(BaseModel):
    """Response after making a move"""
    success: bool
    move_type: Literal["classical", "quantum_split", "capture", "castle", "promotion"]
    new_state: GameState
    quantum_events: List[QuantumEvent] = Field(default_factory=list)
    message: Optional[str] = None


class ObserveRequest(BaseModel):
    """Request to observe (collapse) a quantum piece"""
    game_id: str
    piece_id: str
    player: Literal["white", "black"]


class ObserveResponse(BaseModel):
    """Response after observation"""
    success: bool
    collapsed_position: str
    new_state: GameState
    cascade_events: List[QuantumEvent] = Field(default_factory=list)


class ValidMovesResponse(BaseModel):
    """Valid moves for a piece"""
    piece_id: str
    valid_moves: List[str]
    quantum_moves: List[str] = Field(
        default_factory=list,
        description="Moves that trigger superposition"
    )
    capture_moves: List[str] = Field(default_factory=list)


class CollapsedPieceInfo(BaseModel):
    """Information about a collapsed quantum piece"""
    piece_id: str
    from_state: Literal["superposed", "entangled"]
    to_position: Optional[str] = None
    to_state: Optional[Literal["classical"]] = None


class ObserverMoveRequest(BaseModel):
    """Request to move Observer piece"""
    game_id: str
    observer_id: str
    to_square: str = Field(..., pattern=r"^[a-h][1-8]$")


class ObserverMoveResponse(BaseModel):
    """Response after moving Observer"""
    success: bool
    new_position: str
    observed_pieces: List[str] = Field(default_factory=list)
    collapsed_states: List[CollapsedPieceInfo] = Field(default_factory=list)
    new_state: GameState


class AffectedPiece(BaseModel):
    """Piece affected by Observer's observation zone"""
    piece_id: str
    current_state: Literal["superposed", "entangled"]
    will_collapse: bool
    position: str


class ObservationZoneResponse(BaseModel):
    """Observer's current observation zone"""
    observer_id: str
    current_position: str
    zone_squares: List[str]
    affected_pieces: List[AffectedPiece] = Field(default_factory=list)


class ObservationHistoryItem(BaseModel):
    """Single observation event"""
    piece_id: str
    turn: int
    state: Literal["superposed", "entangled"]


class ObserverStatsResponse(BaseModel):
    """Observer statistics"""
    observations_made: int
    total_pieces_affected: int
    observation_history: List[ObservationHistoryItem] = Field(default_factory=list)

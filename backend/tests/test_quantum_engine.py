"""
Tests for Quantum Engine
"""
import pytest
from backend.core.quantum_engine import QuantumEngine


def test_should_trigger_superposition_knight(db_client):
    """Knights should always trigger superposition"""
    engine = QuantumEngine(db_client)
    result = engine.should_trigger_superposition('knight', 'b1', 'd2')
    assert result == True


def test_should_trigger_superposition_pawn_forward(db_client):
    """Pawns should trigger superposition on forward moves"""
    engine = QuantumEngine(db_client)
    result = engine.should_trigger_superposition('pawn', 'e2', 'e4')
    assert result == True


def test_should_trigger_superposition_pawn_capture(db_client):
    """Pawns should NOT trigger superposition on captures"""
    engine = QuantumEngine(db_client)
    result = engine.should_trigger_superposition('pawn', 'e4', 'd5')
    assert result == False


def test_should_not_trigger_superposition_queen(db_client):
    """Queens should not trigger superposition"""
    engine = QuantumEngine(db_client)
    result = engine.should_trigger_superposition('queen', 'd1', 'd4')
    assert result == False

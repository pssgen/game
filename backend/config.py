"""
Configuration management for Quantum Chess Backend
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Neo4j Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Stockfish Engine
    stockfish_path: str = ""
    
    # Quantum Mechanics Settings
    max_superposition_duration: int = 3
    entanglement_correlation_strength: float = 0.7
    max_entangled_partners: int = 2
    entanglement_max_distance: int = 3
    
    # Observation Settings
    observations_per_turn: int = 1
    
    class Config:
        env_file = "backend/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Configuration loaded - debug prints removed to prevent repetition during imports

# Global settings instance
settings = Settings()

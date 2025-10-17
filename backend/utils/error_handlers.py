"""
Error Handlers for Quantum Chess API
Provides consistent error responses and logging
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.utils.exceptions import QuantumChessError
from backend.utils.logger_factory import get_module_logger, log_error_with_analysis
import traceback
from typing import Union
from pydantic import ValidationError

logger = get_module_logger()


async def quantum_chess_error_handler(request: Request, exc: QuantumChessError) -> JSONResponse:
    """Handle custom Quantum Chess errors"""
    log_error_with_analysis(
        logger,
        f"QuantumChessError: {exc.message}",
        details=exc.details,
        error_type=exc.error_code
    )
    
    # Map error codes to HTTP status codes
    status_code_map = {
        "GAME_NOT_FOUND": 404,
        "PIECE_NOT_FOUND": 404,
        "INVALID_MOVE": 400,
        "QUANTUM_STATE_ERROR": 409,  # Conflict
        "DATABASE_ERROR": 500,
        "TURN_ORDER_ERROR": 409,
        "OBSERVATION_ERROR": 400,
        "GAME_STATE_ERROR": 409,
        "VALIDATION_ERROR": 422,
        "CONFIGURATION_ERROR": 500
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": str(request.state.__dict__.get('start_time', ''))
        }
    )


async def validation_error_handler(request: Request, exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    """Handle Pydantic validation errors"""
    error_details = []
    
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    log_error_with_analysis(
        logger,
        f"Validation error: {len(error_details)} fields failed validation",
        details={"errors": error_details}
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed",
            "details": {
                "validation_errors": error_details
            },
            "timestamp": str(request.state.__dict__.get('start_time', ''))
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions with consistent format"""
    log_error_with_analysis(
        logger,
        f"HTTP {exc.status_code}: {exc.detail}",
        details={"headers": exc.headers}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
            "timestamp": str(request.state.__dict__.get('start_time', ''))
        },
        headers=exc.headers
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    error_trace = traceback.format_exc()
    
    log_error_with_analysis(
        logger,
        f"Unexpected error: {str(exc)}",
        details={
            "exception_type": type(exc).__name__,
            "traceback": error_trace
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {
                "exception_type": type(exc).__name__,
                # Only include trace in debug mode
                **({"traceback": error_trace} if logger.level <= 10 else {})
            },
            "timestamp": str(request.state.__dict__.get('start_time', ''))
        }
    )


def add_error_handlers(app):
    """Add all error handlers to FastAPI app"""
    app.add_exception_handler(QuantumChessError, quantum_chess_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers registered successfully")
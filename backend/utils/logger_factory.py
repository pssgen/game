"""
Logger Factory for Quantum Chess Backend
Provides structured logging with per-file logs, color-coded terminal output, and debug tracing
"""
import logging
import logging.config
import os
import sys
import inspect
from pathlib import Path
from typing import Dict, Any

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

class ColorFormatter(logging.Formatter):
    """Color-coded formatter for terminal output"""

    def __init__(self, fmt=None, datefmt=None, style='%', use_color=True):
        super().__init__(fmt, datefmt, style)
        self.use_color = use_color

        # Color mapping for log levels
        self.level_colors = {
            logging.DEBUG: Colors.BRIGHT_CYAN,
            logging.INFO: Colors.BRIGHT_GREEN,
            logging.WARNING: Colors.BRIGHT_YELLOW,
            logging.ERROR: Colors.BRIGHT_RED + Colors.BOLD,
            logging.CRITICAL: Colors.RED + Colors.BOLD,
        }

        # Icon mapping
        self.level_icons = {
            logging.DEBUG: "🔍",
            logging.INFO: "✅",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "🚨",
        }

    def format(self, record):
        # Add filename, line number, and function name
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)

        # Create the base message
        message = super().format(record)

        if self.use_color:
            color = self.level_colors.get(record.levelno, Colors.WHITE)
            icon = self.level_icons.get(record.levelno, "📝")

            # Format: ICON [LEVEL] (file:line function) message
            colored_message = f"{icon} {color}[{record.levelname}]{Colors.RESET} ({record.filename}:{record.lineno} {record.funcName}) {message}"
            return colored_message

        return message

def get_logger_factory():
    """Get the configured logger factory function"""

    # Logging configuration
    LOGGING_CONFIG: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'file': {
                'format': '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'console': {
                '()': ColorFormatter,
                'fmt': '%(message)s',
                'use_color': True
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console',
                'stream': sys.stdout,
                'level': 'DEBUG'
            },
            'app_file': {
                'class': 'logging.FileHandler',
                'filename': LOGS_DIR / 'app.log',
                'formatter': 'file',
                'mode': 'w',  # Overwrite on each run
                'level': 'DEBUG'
            }
        },
        'root': {
            'handlers': ['console', 'app_file'],
            'level': 'DEBUG'
        },
        'loggers': {
            # Will be dynamically added for each module
        }
    }

    # Apply configuration
    logging.config.dictConfig(LOGGING_CONFIG)

    def create_logger(module_name: str) -> logging.Logger:
        """
        Create a logger for a specific module with per-file logging

        Args:
            module_name: Name of the module (e.g., 'game_state', 'quantum_engine')

        Returns:
            Configured logger instance
        """
        logger_name = module_name

        # Get or create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # Try to create per-file handler, fall back to console-only if it fails
        try:
            file_handler = logging.FileHandler(
                LOGS_DIR / f'{module_name}.log',
                mode='w'  # Overwrite on each run
            )
            file_handler.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            file_handler.setLevel(logging.DEBUG)
            
            # Add the file handler if not already added
            if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith(f'{module_name}.log')
                      for h in logger.handlers):
                logger.addHandler(file_handler)
        except (OSError, ValueError) as e:
            # If file logging fails, just log to console
            logger.warning(f"File logging disabled for {module_name}: {e}")

        # Ensure logger doesn't propagate to root (to avoid duplicate console output)
        logger.propagate = False

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter(use_color=True))
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

        return logger

    return create_logger

# Global logger factory
create_logger = get_logger_factory()

def debug_trace(message: str, logger: logging.Logger = None, context: str = None):
    """
    Debug trace helper that automatically includes file, line, and function info
    Also prints concise terminal hints for immediate visibility during testing

    Args:
        message: Debug message
        logger: Logger to use (if None, uses root logger)
        context: Optional context for terminal hint
    """
    if logger is None:
        logger = logging.getLogger()

    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    line_no = frame.f_lineno
    func_name = frame.f_code.co_name

    # Print terminal hint for immediate visibility
    hint = f"🧩 DEBUG TRACE → {message}"
    if context:
        hint += f" [{context}]"
    print(hint)

    logger.debug(f"{message} ({filename}:{line_no} in {func_name})")

def log_game_event(logger: logging.Logger, event_type: str, details: str, **kwargs):
    """
    Log game-related events with structured format and gameplay prefixes

    Args:
        logger: Logger instance
        event_type: Type of event (e.g., 'game_created', 'move_executed')
        details: Event details
        **kwargs: Additional context
    """
    # Map event types to gameplay prefixes
    prefix_map = {
        'game_created': '[GAMEPLAY]',
        'move_executed': '[MOVE]',
        'observation_executed': '[OBSERVER]',
        'observer_moved': '[OBSERVER]',
        'observation_completed': '[OBSERVER]',
        'superposition_created': '[COLLAPSE]',
        'entanglement_created': '[COLLAPSE]',
        'superposition_collapsed': '[COLLAPSE]',
        'entanglement_broken': '[COLLAPSE]',
        'turn_advanced': '[GAMEPLAY]',
        'game_ended': '[GAMEPLAY]'
    }

    prefix = prefix_map.get(event_type, '[GAMEPLAY]')
    context = " ".join(f"{k}={v}" for k, v in kwargs.items())
    message = f"{prefix} {details}"
    if context:
        message += f" | {context}"

    logger.info(message)

def log_error_with_analysis(logger: logging.Logger, error_msg: str, root_cause: str, action: str):
    """
    Log errors with root cause analysis and suggested action

    Args:
        logger: Logger instance
        error_msg: The error message
        root_cause: Analysis of why it happened
        action: Suggested action taken
    """
    logger.error(f"{error_msg}")
    logger.error(f"ROOT CAUSE: {root_cause}")
    logger.error(f"ACTION: {action}")

# Convenience function to get logger for current module
def get_module_logger() -> logging.Logger:
    """Get logger for the calling module"""
    try:
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        module_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Handle cases where filename is invalid (e.g., '<string>' from python -c)
        if not module_name or module_name == '<string>' or not module_name.replace('_', '').replace('-', '').isalnum():
            module_name = 'console'
            
        return create_logger(module_name)
    except Exception:
        # Fallback to console logger if anything goes wrong
        return create_logger('console')
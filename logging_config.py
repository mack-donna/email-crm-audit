"""
Shared Logging Configuration

Consolidates duplicate logging setup code from across the codebase.
Provides a factory function to create consistent loggers for all modules.

Replaces duplicate setup_logging() methods in:
- email_generator.py
- learning_engine.py
- contact_processor.py
- email_history_analyzer.py
- workflow_orchestrator.py
- review_interface.py
- linkedin_client.py
- public_info_researcher.py
- And other files
"""

import logging
from datetime import datetime
import os


def setup_logger(name, level="INFO", log_to_file=True, log_dir="logs"):
    """
    Create and configure a logger with consistent formatting.

    Args:
        name (str): Logger name (typically __name__ of the calling module)
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file (bool): Whether to log to a file in addition to console
        log_dir (str): Directory for log files (default: "logs")

    Returns:
        logging.Logger: Configured logger instance

    Example:
        # In your module:
        from logging_config import setup_logger
        logger = setup_logger(__name__, "INFO")
        logger.info("Application started")
    """
    # Create logger
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                # If we can't create the directory, just skip file logging
                pass

        # Create log filename with timestamp
        # Extract simple module name (e.g., "email_generator" from "email_crm_audit.email_generator")
        simple_name = name.split('.')[-1] if '.' in name else name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = "{}_{}.log".format(simple_name, timestamp)
        log_path = os.path.join(log_dir, log_filename)

        try:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            # If we can't create the log file, log a warning to console but continue
            logger.warning("Could not create log file {}: {}".format(log_path, str(e)))

    return logger


def setup_basic_logger(name, level="INFO"):
    """
    Create a basic logger with console output only.

    Simpler version of setup_logger() for cases where file logging is not needed.

    Args:
        name (str): Logger name
        level (str): Logging level

    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(name, level, log_to_file=False)


def configure_root_logger(level="INFO"):
    """
    Configure the root logger for the entire application.

    Call this once at application startup to set global logging behavior.

    Args:
        level (str): Logging level for root logger
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

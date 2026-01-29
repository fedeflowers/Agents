"""Logging configuration using structlog for structured output."""
import logging
import structlog
from src.config import settings


def configure_logging() -> None:
    """Configure structlog with appropriate processors for the log level."""
    
    # Set the stdlib logging level
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Configure on import
configure_logging()
logger = get_logger("extraction_pipeline")

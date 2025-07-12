"""
Logger setup utilities.
"""
import logging

def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Set up logger based on the module name. Ensures:
    - No duplicate handlers are added.
    - Propagation to the root logger is disabled.
    - A standard formatter is applied.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove all old handlers if they exist (prevents duplicate logs on reload)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Turn off propagation to the root logger
    logger.propagate = False

    # Create console handler
    console_handler = logging.StreamHandler()
    formatter       = logging.Formatter(
        fmt     = "[%(levelname)s]\t%(name)s\t%(funcName)s\t%(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger
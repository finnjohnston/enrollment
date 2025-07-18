import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
LOG_LEVEL = logging.INFO

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(LOG_FORMAT))

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
if not root_logger.handlers:
    root_logger.addHandler(handler)


def get_logger(name=None):
    """Get a logger with the given name, or the root logger if None."""
    return logging.getLogger(name)
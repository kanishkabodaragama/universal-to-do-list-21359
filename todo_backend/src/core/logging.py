import logging
import sys

OCEAN_PRIMARY = "#2563EB"
OCEAN_AMBER = "#F59E0B"
OCEAN_ERROR = "#EF4444"
OCEAN_TEXT = "#111827"


class OceanFormatter(logging.Formatter):
    """Custom formatter that tags logs with Ocean Professional theme hints."""

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        base = super().format(record)
        if level in ("ERROR", "CRITICAL"):
            return f"[Ocean:{OCEAN_ERROR}] {base}"
        if level in ("WARNING",):
            return f"[Ocean:{OCEAN_AMBER}] {base}"
        return f"[Ocean:{OCEAN_PRIMARY}] {base}"


# PUBLIC_INTERFACE
def get_logger(name: str = "todo_backend") -> logging.Logger:
    """Get configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(OceanFormatter(fmt))
        logger.addHandler(handler)
        logger.propagate = False
    return logger

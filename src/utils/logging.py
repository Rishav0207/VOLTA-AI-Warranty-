"""Logging setup for the VOLTA backend."""

import logging
import sys


def configure_logging() -> None:
    """Configure structured-enough console logging for local and container runs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

Runtime logging is configured by `src/utils/logging.py`.

This directory is intentionally not a Python package so it does not shadow the
standard-library `logging` module when the backend is launched from `src/`.

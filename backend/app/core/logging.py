import logging


def setup_logging() -> None:
    fmt = "[%(levelname)s] %(asctime)s %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)

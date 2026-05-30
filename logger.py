import logging
import sys

from rich.console import Console
from rich.logging import RichHandler


def setup(level: int | str = logging.WARNING) -> None:
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    console = Console(file=sys.stdout, force_terminal=True)
    handler = RichHandler(
        console=console,
        level=level,
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
    )
    handler.setFormatter(logging.Formatter("%(name)-12s %(message)s"))

    logging.basicConfig(level=level, handlers=[handler], force=True)


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

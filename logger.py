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
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
    )
    handler.setLevel(logging.DEBUG)  # handler passes everything
    handler.setFormatter(logging.Formatter("%(name)-12s %(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # root passes everything
    root.addHandler(handler)

    # set the default level on the root so components inherit it
    root.setLevel(level)


def set_component_level(component: str, level: str) -> None:
    logging.getLogger(component).setLevel(level.upper())


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)


DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

import logger
from mmu import MMU

log = logger.get("Timer")


class Timer:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        log.debug("Timer initialized")

    def step(self, cycles: int) -> None:
        pass

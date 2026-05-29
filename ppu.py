import logger
from mmu import MMU

log = logger.get("PPU")


class PPU:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        log.debug("PPU initialized")

    def step(self, cycles: int) -> None:
        log.debug("Step %d cycles", cycles)

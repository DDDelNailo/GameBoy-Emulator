import logger
from mmu import MMU

log = logger.get("Joypad")


class Joypad:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        log.debug("Joypad initialized")

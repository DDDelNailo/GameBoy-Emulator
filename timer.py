from mmu import MMU

class Timer:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        
    def step(self, cycles: int) -> None:
        pass
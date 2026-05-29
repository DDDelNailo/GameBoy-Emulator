from mmu import MMU

class CPU:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        
    def step(self) -> int:
        cycles: int = 0
        return cycles
from mmu import MMU
from cpu import CPU
from ppu import PPU
from timer import Timer
from joypad import Joypad

class Emulator:
    def __init__(self, rom_path: str) -> None:
        self.mmu: MMU = MMU(rom_path)
        self.cpu: CPU = CPU(self.mmu)
        self.ppu: PPU = PPU(self.mmu)
        self.timer: Timer = Timer(self.mmu)
        self.joypad: Joypad = Joypad(self.mmu)

    def step(self) -> None:
        cycles: int = self.cpu.step()
        self.ppu.step(cycles)
        self.timer.step(cycles)

    def run(self) -> None:
        for _ in range(10):
            self.step()
            
if __name__ == "__main__":
    emulator = Emulator("roms/Pokemon - Red Version.gb")
    emulator.run()
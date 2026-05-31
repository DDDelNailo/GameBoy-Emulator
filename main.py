import argparse

import warnings
warnings.filterwarnings("ignore", message=".*avx2.*")
import pygame
import numpy as np

import logger
from mmu import MMU
from cpu import CPU
from ppu import PPU
from timer import Timer
from joypad import Joypad

log = logger.get("Emulator")

SCALE = 3

class Emulator:
    def __init__(self, rom_path: str, boot_rom_path: str) -> None:
        log.info("Loading ROM %s", rom_path)
        self.mmu: MMU = MMU(rom_path, boot_rom_path)
        self.cpu: CPU = CPU(self.mmu)
        self.ppu: PPU = PPU(self.mmu)
        self.timer: Timer = Timer(self.mmu)
        self.joypad: Joypad = Joypad(self.mmu)
        
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode((160 * SCALE, 144 * SCALE))
        pygame.display.set_caption("GameBoy Emulator")
        self.clock: pygame.time.Clock = pygame.time.Clock()

    def step(self) -> int:
        if self.cpu.log_from is not None and self.cpu.pc == self.cpu.log_from:
            logger.setup(level=logger.DEBUG)
            
        cycles: int = self.cpu.step()
        if cycles == 0:
            log.error("CPU step returned 0 cycles, which is invalid")
            exit()
        self.ppu.step(cycles)
        self.timer.step(cycles)
        return cycles

    def run(self) -> None:
        log.info("Starting emulator loop")

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
            self.ppu.frame_ready = False
            while not self.ppu.frame_ready:
                self.step()

            self._blit()

            self.clock.tick(60)

    def _blit(self) -> None:
        arr = np.array(self.ppu.framebuffer, dtype=np.uint8)  # (144, 160, 3)
        surf = pygame.surfarray.make_surface(arr.transpose(1, 0, 2))
        surf = pygame.transform.scale(surf, (160 * SCALE, 144 * SCALE))
        self.screen.blit(surf, (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="WARNING")
    parser.add_argument("--log-from", default=None, metavar="ADDR")
    parser.add_argument("--log-cpu", default=None, metavar="LEVEL")
    parser.add_argument("--log-mmu", default=None, metavar="LEVEL")
    parser.add_argument("--log-ppu", default=None, metavar="LEVEL")
    parser.add_argument("--log-timer", default=None, metavar="LEVEL")
    parser.add_argument("--log-joypad", default=None, metavar="LEVEL")
    parser.add_argument("--log-rom", default=None, metavar="LEVEL")
    args = parser.parse_args()

    logger.setup(level=args.log)

    if args.log_cpu:
        logger.set_component_level("CPU", args.log_cpu)
    if args.log_mmu:
        logger.set_component_level("MMU", args.log_mmu)
    if args.log_ppu:
        logger.set_component_level("PPU", args.log_ppu)
    if args.log_timer:
        logger.set_component_level("Timer", args.log_timer)
    if args.log_joypad:
        logger.set_component_level("Joypad", args.log_joypad)
    if args.log_rom:
        logger.set_component_level("ROM", args.log_rom)

    log_from: int | None = int(args.log_from, 16) if args.log_from else None

    emulator = Emulator("roms/Tetris.gb", "roms/boot/dmg_boot.bin")
    # emulator = Emulator("roms/Pokemon - Red Version.gb", "roms/boot/dmg_boot.bin")
    emulator.cpu.log_from = log_from
    emulator.run()

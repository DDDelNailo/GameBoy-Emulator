import pygame
import numpy as np
from mmu import MMU
from cpu import CPU
from ppu import PPU
from timer import Timer
from joypad import Joypad

import perf as perf_module

p = perf_module.perf

SCALE = 1


class Emulator:
    def __init__(self, rom_path: str, boot_rom_path: str) -> None:
        self.mmu: MMU = MMU(rom_path, boot_rom_path)
        self.cpu: CPU = CPU(self.mmu)
        self.ppu: PPU = PPU(self.mmu)
        self.timer: Timer = Timer(self.mmu)
        self.joypad: Joypad = Joypad(self.mmu)

        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (160 * SCALE, 144 * SCALE)
        )
        pygame.display.set_caption("GameBoy Emulator")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        self._fb_array = np.zeros((144, 160, 3), dtype=np.uint8)
        self._screen_surf = pygame.Surface((160 * SCALE, 144 * SCALE))

    def step(self) -> int:
        t = p.begin("cpu")
        cycles: int = self.cpu.step()
        p.end("cpu", t)

        if cycles == 0:
            print("CPU step returned 0 cycles, which is invalid")
            exit()

        t = p.begin("ppu")
        self.ppu.step(cycles)
        p.end("ppu", t)

        t = p.begin("timer")
        self.timer.step(cycles)
        p.end("timer", t)

        t = p.begin("apu")
        self.mmu.apu.step(cycles)
        p.end("apu", t)

        return cycles

    def run(self) -> None:
        running = True
        while running:
            p.frame_start()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.ppu.frame_ready = False
            while not self.ppu.frame_ready:
                self.step()

            t = p.begin("blit")
            self._blit()
            p.end("blit", t)

            t = p.begin("apu_flush")
            self.mmu.apu.flush()
            p.end("apu_flush", t)

            p.frame_end()
            self.clock.tick(60)

    def _blit(self) -> None:
        np.copyto(self._fb_array, self.ppu.framebuffer)
        surf = pygame.surfarray.make_surface(self._fb_array.transpose(1, 0, 2))
        pygame.transform.scale(surf, (160 * SCALE, 144 * SCALE), self._screen_surf)
        self.screen.blit(self._screen_surf, (0, 0))
        pygame.display.flip()

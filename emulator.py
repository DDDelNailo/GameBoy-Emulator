import pygame
from mmu import MMU
from cpu import CPU
from ppu import PPU
from timer import Timer
from joypad import Joypad

import perf as perf_module

p = perf_module.perf


class Emulator:
    def __init__(self, rom_path: str, boot_rom_path: str) -> None:
        pygame.init()

        self.mmu: MMU = MMU(rom_path, boot_rom_path)
        self.cpu: CPU = CPU(self.mmu)
        self.ppu: PPU = PPU(self.mmu)
        self.timer: Timer = Timer(self.mmu)
        self.joypad: Joypad = Joypad(self.mmu)

        self.screen = pygame.display.set_mode(
            (160, 144),
            pygame.SCALED | pygame.RESIZABLE,
        )
        pygame.display.set_caption("GameBoy Emulator")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        self._screen_surf = pygame.Surface(
            (160, 144),
            depth=32,
        )
        self._scaled_surf = pygame.Surface(
            self.screen.get_size(),
            depth=32,
        )

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
        surf_array = pygame.surfarray.pixels2d(self._screen_surf)

        surf_array[:, :] = self.ppu.framebuffer.T

        del surf_array

        pygame.transform.scale(
            self._screen_surf,
            self.screen.get_size(),
            self._scaled_surf,
        )

        self.screen.blit(self._scaled_surf, (0, 0))

        pygame.display.flip()

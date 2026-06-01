from mmu import MMU
import numpy as np
from ppu_fast import render_bg_scanline

# STAT modes
MODE_HBLANK = 0
MODE_VBLANK = 1
MODE_OAM = 2
MODE_DRAW = 3

# Cycle budgets per mode per scanline
OAM_CYCLES = 80
DRAW_CYCLES = 172
HBLANK_CYCLES = 204
LINE_CYCLES = 456  # OAM + DRAW + HBLANK
VBLANK_LINE = 144
TOTAL_LINES = 154


class PPU:
    PALETTE = np.array(
        [
            0xFFFFFFFF,
            0xFFAAAAAA,
            0xFF555555,
            0xFF000000,
        ],
        dtype=np.uint32,
    )

    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self.cycles: int = 0
        self.ly: int = 0
        self.mode: int = MODE_OAM
        self.framebuffer = np.zeros((144, 160), dtype=np.uint32)
        self.frame_ready: bool = False
        self._mode_names = {
            MODE_HBLANK: "HBLANK",
            MODE_VBLANK: "VBLANK",
            MODE_OAM: "OAM",
            MODE_DRAW: "DRAW",
        }

        self.tile_lut = np.zeros(
            (256, 256, 8),
            dtype=np.uint8,
        )

        for byte1 in range(256):
            for byte2 in range(256):
                for bit in range(8):
                    self.tile_lut[byte1, byte2, bit] = (
                        ((byte2 >> (7 - bit)) & 1) << 1
                    ) | ((byte1 >> (7 - bit)) & 1)

        self.palette_lut = np.zeros(
            (256, 4),
            dtype=np.uint8,
        )

        for bgp in range(256):
            for color in range(4):
                self.palette_lut[bgp, color] = (bgp >> (color * 2)) & 0x03

    def step(self, cycles: int) -> None:
        lcdc: int = self.mmu.read_u8(0xFF40)

        if not (lcdc & 0x80):  # LCD disabled
            return

        # self.frame_ready = False
        self.cycles += cycles

        if self.mode == MODE_OAM:
            if self.cycles >= OAM_CYCLES:
                self.cycles -= OAM_CYCLES
                self._set_mode(MODE_DRAW)

        elif self.mode == MODE_DRAW:
            if self.cycles >= DRAW_CYCLES:
                self.cycles -= DRAW_CYCLES
                self._render_scanline()
                self._set_mode(MODE_HBLANK)

        elif self.mode == MODE_HBLANK:
            if self.cycles >= HBLANK_CYCLES:
                self.cycles -= HBLANK_CYCLES
                self.ly += 1
                self.mmu.write_u8(0xFF44, self.ly)
                self._check_lyc()

                if self.ly == VBLANK_LINE:
                    self._set_mode(MODE_VBLANK)
                    self._trigger_vblank()
                    self.frame_ready = True
                else:
                    self._set_mode(MODE_OAM)

        elif self.mode == MODE_VBLANK:
            if self.cycles >= LINE_CYCLES:
                self.cycles -= LINE_CYCLES
                self.ly += 1
                self.mmu.write_u8(0xFF44, self.ly)

                if self.ly >= TOTAL_LINES:
                    self.ly = 0
                    self.mmu.write_u8(0xFF44, 0)
                    self._set_mode(MODE_OAM)

    def _set_mode(self, mode: int) -> None:
        self.mode = mode
        stat: int = self.mmu.read_u8(0xFF41)
        self.mmu.write_u8(0xFF41, (stat & 0xFC) | mode)

    def _check_lyc(self) -> None:
        lyc: int = self.mmu.read_u8(0xFF45)
        stat: int = self.mmu.read_u8(0xFF41)
        if self.ly == lyc:
            self.mmu.write_u8(0xFF41, stat | 0x04)
        else:
            self.mmu.write_u8(0xFF41, stat & ~0x04)

    def _trigger_vblank(self) -> None:
        if_: int = self.mmu.read_u8(0xFF0F)
        self.mmu.write_u8(0xFF0F, if_ | 0x01)

    def _render_scanline(self) -> None:
        lcdc: int = self.mmu.read_u8(0xFF40)
        if not (lcdc & 0x01):  # BG disabled
            return

        scy: int = self.mmu.read_u8(0xFF42)
        scx: int = self.mmu.read_u8(0xFF43)
        bgp: int = self.mmu.read_u8(0xFF47)  # background palette

        render_bg_scanline(
            self.mmu.vram_np,
            self.framebuffer,
            self.PALETTE,
            self.tile_lut,
            self.palette_lut,
            self.ly,
            scx,
            scy,
            lcdc,
            bgp,
        )

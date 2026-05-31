import logger
from mmu import MMU
import numpy as np

log = logger.get("PPU")

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
    PALETTE: np.ndarray = np.array(
        [
            [255, 255, 255],
            [170, 170, 170],
            [85, 85, 85],
            [0, 0, 0],
        ],
        dtype=np.uint8,
    )

    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self.cycles: int = 0
        self.ly: int = 0
        self.mode: int = MODE_OAM
        self.framebuffer: np.ndarray = np.full(
            (144, 160, 3), (255, 255, 255), dtype=np.uint8
        )
        self.frame_ready: bool = False
        self._mode_names = {
            MODE_HBLANK: "HBLANK",
            MODE_VBLANK: "VBLANK",
            MODE_OAM: "OAM",
            MODE_DRAW: "DRAW",
        }

        log.debug("PPU initialized")

    def step(self, cycles: int) -> None:
        lcdc: int = self.mmu.read_u8(0xFF40)[0]
        log.debug(
            "PPU step %d cycles (mode=%s LY=%d)",
            cycles,
            self._mode_names.get(self.mode, self.mode),
            self.ly,
        )

        if not (lcdc & 0x80):  # LCD disabled
            log.debug("LCD disabled - skipping PPU step")
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
                self.mmu.write_u8(0xFF44, bytes([self.ly]))
                log.debug("LY -> %d", self.ly)
                self._check_lyc()

                if self.ly == VBLANK_LINE:
                    self._set_mode(MODE_VBLANK)
                    self._trigger_vblank()
                    self.frame_ready = True
                    log.debug("Frame ready at LY=%d", self.ly)
                else:
                    self._set_mode(MODE_OAM)

        elif self.mode == MODE_VBLANK:
            if self.cycles >= LINE_CYCLES:
                self.cycles -= LINE_CYCLES
                self.ly += 1
                self.mmu.write_u8(0xFF44, bytes([self.ly]))

                if self.ly >= TOTAL_LINES:
                    self.ly = 0
                    self.mmu.write_u8(0xFF44, bytes([0]))
                    log.debug("LY reset to 0")
                    self._set_mode(MODE_OAM)

    def _set_mode(self, mode: int) -> None:
        self.mode = mode
        stat: int = self.mmu.read_u8(0xFF41)[0]
        self.mmu.write_u8(0xFF41, bytes([(stat & 0xFC) | mode]))
        log.debug("Mode -> %s", self._mode_names.get(mode, mode))

    def _check_lyc(self) -> None:
        lyc: int = self.mmu.read_u8(0xFF45)[0]
        stat: int = self.mmu.read_u8(0xFF41)[0]
        if self.ly == lyc:
            self.mmu.write_u8(0xFF41, bytes([stat | 0x04]))
            log.debug("LY==LYC (%d) - STAT LYC flag set", self.ly)
        else:
            self.mmu.write_u8(0xFF41, bytes([stat & ~0x04]))
            log.debug("LY!=LYC (%d vs %d) - STAT LYC flag cleared", self.ly, lyc)

    def _trigger_vblank(self) -> None:
        if_: int = self.mmu.read_u8(0xFF0F)[0]
        self.mmu.write_u8(0xFF0F, bytes([if_ | 0x01]))
        log.debug("VBlank triggered at LY=%d", self.ly)

    def _render_scanline(self) -> None:
        lcdc: int = self.mmu.read_u8(0xFF40)[0]
        if not (lcdc & 0x01):  # BG disabled
            log.debug("BG disabled at LY=%d - skipping render", self.ly)
            return

        scy: int = self.mmu.read_u8(0xFF42)[0]
        scx: int = self.mmu.read_u8(0xFF43)[0]
        bgp: int = self.mmu.read_u8(0xFF47)[0]  # background palette

        log.debug(
            "Render scanline LY=%d SCX=%d SCY=%d BGP=0x%02X", self.ly, scx, scy, bgp
        )

        y: int = (self.ly + scy) & 0xFF  # which row in the full 256x256 BG map

        # Which tilemap: LCDC bit 3 selects $9C00 vs $9800
        tilemap_base: int = 0x9C00 if (lcdc & 0x08) else 0x9800

        vram = self.mmu.vram_np

        xs = np.arange(160, dtype=np.uint16)
        pxs = (xs + scx) & 0xFF

        tile_cols = pxs >> 3
        tile_row = y >> 3

        # BG tile map offsets inside VRAM
        tilemap_offsets = (tilemap_base - 0x8000) + tile_row * 32 + tile_cols

        tile_ids = vram[tilemap_offsets].astype(np.int16)

        # Tile addressing
        if lcdc & 0x10:
            tile_data_offsets = tile_ids * 16
        else:
            signed_ids = np.where(tile_ids > 127, tile_ids - 256, tile_ids)
            tile_data_offsets = 0x1000 + signed_ids * 16
            # because 0x9000 - 0x8000 = 0x1000

        row_in_tile = (y & 7) * 2

        byte1s = vram[tile_data_offsets + row_in_tile]
        byte2s = vram[tile_data_offsets + row_in_tile + 1]

        bits = 7 - (pxs & 7)

        color_ids = (((byte2s >> bits) & 1) << 1) | ((byte1s >> bits) & 1)

        shades = (bgp >> (color_ids * 2)) & 0x03

        self.framebuffer[self.ly] = self.PALETTE[shades]

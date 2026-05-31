import logger
from mmu import MMU

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
    PALETTE = [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)]

    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self.cycles: int = 0
        self.ly: int = 0
        self.mode: int = MODE_OAM
        self.framebuffer: list[list[tuple[int, int, int]]] = [
            [(255, 255, 255)] * 160 for _ in range(144)
        ]
        self.frame_ready: bool = False
        self._mode_names = {
            MODE_HBLANK: "HBLANK",
            MODE_VBLANK: "VBLANK",
            MODE_OAM: "OAM",
            MODE_DRAW: "DRAW",
        }

        log.debug("PPU initialized")

    def step(self, cycles: int) -> None:
        lcdc: int = self.mmu.read(0xFF40)[0]
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
                self.mmu.write(0xFF44, bytes([self.ly]))
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
                self.mmu.write(0xFF44, bytes([self.ly]))

                if self.ly >= TOTAL_LINES:
                    self.ly = 0
                    self.mmu.write(0xFF44, bytes([0]))
                    log.debug("LY reset to 0")
                    self._set_mode(MODE_OAM)

    def _set_mode(self, mode: int) -> None:
        self.mode = mode
        stat: int = self.mmu.read(0xFF41)[0]
        self.mmu.write(0xFF41, bytes([(stat & 0xFC) | mode]))
        log.debug("Mode -> %s", self._mode_names.get(mode, mode))

    def _check_lyc(self) -> None:
        lyc: int = self.mmu.read(0xFF45)[0]
        stat: int = self.mmu.read(0xFF41)[0]
        if self.ly == lyc:
            self.mmu.write(0xFF41, bytes([stat | 0x04]))
            log.debug("LY==LYC (%d) - STAT LYC flag set", self.ly)
        else:
            self.mmu.write(0xFF41, bytes([stat & ~0x04]))
            log.debug("LY!=LYC (%d vs %d) - STAT LYC flag cleared", self.ly, lyc)

    def _trigger_vblank(self) -> None:
        if_: int = self.mmu.read(0xFF0F)[0]
        self.mmu.write(0xFF0F, bytes([if_ | 0x01]))
        log.debug("VBlank triggered at LY=%d", self.ly)

    def _render_scanline(self) -> None:
        lcdc: int = self.mmu.read(0xFF40)[0]
        if not (lcdc & 0x01):  # BG disabled
            log.debug("BG disabled at LY=%d - skipping render", self.ly)
            return

        scy: int = self.mmu.read(0xFF42)[0]
        scx: int = self.mmu.read(0xFF43)[0]
        bgp: int = self.mmu.read(0xFF47)[0]  # background palette

        log.debug(
            "Render scanline LY=%d SCX=%d SCY=%d BGP=0x%02X", self.ly, scx, scy, bgp
        )

        y: int = (self.ly + scy) & 0xFF  # which row in the full 256x256 BG map

        # Which tilemap: LCDC bit 3 selects $9C00 vs $9800
        tilemap_base: int = 0x9C00 if (lcdc & 0x08) else 0x9800

        for x in range(160):
            px: int = (x + scx) & 0xFF  # which column in BG map

            # Tile index in the 32x32 tile map
            tile_col: int = px // 8
            tile_row: int = y // 8
            tile_addr: int = tilemap_base + tile_row * 32 + tile_col
            tile_id: int = self.mmu.read(tile_addr)[0]

            # Tile data address
            if lcdc & 0x10:
                tile_data_addr: int = 0x8000 + tile_id * 16
            else:
                # Signed addressing: tile_id is signed, base is $9000
                if tile_id > 127:
                    tile_id -= 256
                tile_data_addr: int = 0x9000 + tile_id * 16

            # Which row of the tile (each row = 2 bytes)
            row_in_tile: int = (y % 8) * 2
            byte1: int = self.mmu.read(tile_data_addr + row_in_tile)[0]
            byte2: int = self.mmu.read(tile_data_addr + row_in_tile + 1)[0]

            # Which bit in the row
            bit: int = 7 - (px % 8)
            color_id: int = ((byte2 >> bit) & 1) << 1 | ((byte1 >> bit) & 1)

            # Apply palette
            shade: int = (bgp >> (color_id * 2)) & 0x03
            self.framebuffer[self.ly][x] = self.PALETTE[shade]

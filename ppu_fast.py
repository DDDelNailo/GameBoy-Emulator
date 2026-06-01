import numpy as np
from numba import njit  # type: ignore


@njit(cache=True)  # type: ignore
def render_bg_scanline(
    vram: np.ndarray,
    framebuffer: np.ndarray,
    palette: np.ndarray,
    tile_lut: np.ndarray,
    palette_lut: np.ndarray,
    ly: int,
    scx: int,
    scy: int,
    lcdc: int,
    bgp: int,
) -> None:
    y: int = (ly + scy) & 0xFF

    # BG tilemap base
    tilemap_base: int = 0x1C00 if (lcdc & 0x08) else 0x1800

    # Fine X scroll
    fine_x: int = scx & 7

    # First tile
    map_x: int = scx >> 3

    # Tile row
    tile_row: int = y >> 3

    # Row inside tile
    row_in_tile: int = (y & 7) * 2

    framebuffer_x: int = 0

    for tile_x in range(21):  # 20 visible + 1 partial
        tile_col: int = (map_x + tile_x) & 31

        tile_addr: int = tilemap_base + tile_row * 32 + tile_col

        tile_id: int = vram[tile_addr]

        # Tile data addressing
        if lcdc & 0x10:
            tile_data_addr: int = tile_id * 16
        else:
            if tile_id > 127:
                tile_id -= 256

            tile_data_addr = 0x1000 + tile_id * 16

        byte1: int = vram[tile_data_addr + row_in_tile]
        byte2: int = vram[tile_data_addr + row_in_tile + 1]

        tile_pixels = tile_lut[byte1, byte2]

        pixels = palette_lut[bgp][tile_pixels]

        start: int = 0
        end: int = 8

        # First tile clipping
        if tile_x == 0:
            start = fine_x

        # Last tile clipping
        remaining: int = 160 - framebuffer_x
        if remaining < (end - start):
            end = start + remaining

        count: int = end - start

        framebuffer[ly, framebuffer_x : framebuffer_x + count] = palette[pixels[start:end]]

        framebuffer_x += count

        if framebuffer_x >= 160:
            break

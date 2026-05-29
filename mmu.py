from rom import Rom


class MMU:
    def __init__(self, rom_path: str) -> None:
        self.rom: Rom = Rom(rom_path)
        self.rom.header.info()

        # 0000-3FFF: 16 KiB ROM Bank 00 (fixed bank from cartridge)
        # 4000-7FFF: 16 KiB ROM Bank 01..NN (switchable via mapper/MBC later)
        # 8000-9FFF: 8 KiB Video RAM (VRAM). In CGB, banks 0/1.
        # A000-BFFF: 8 KiB External (Cartridge) RAM. Banking controlled by mapper.
        # C000-CFFF: 4 KiB Work RAM (WRAM) bank 0
        # D000-DFFF: 4 KiB Work RAM (WRAM) bank 1 (switchable on CGB)
        # E000-FDFF: Echo of C000-DDFF (mirror of lower WRAM area).
        # FE00-FE9F: Object Attribute Memory (OAM) — sprite attribute table (160 bytes)
        # FEA0-FEFF: Not Usable — reserved / prohibited region (96 bytes)
        # FF00-FF7F: I/O Registers (128 bytes)
        # FF80-FFFE: High RAM (HRAM) (127 bytes)
        # FFFF: Interrupt Enable register (IE)

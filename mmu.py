from apu import APU
from rom import Rom
import numpy as np


class MMU:
    def __init__(self, rom_path: str, boot_rom_path: str) -> None:
        self.rom: Rom = Rom(rom_path)
        self.vram: bytearray = bytearray(0x2000)  # 8KB VRAM
        self.eram: bytearray = bytearray(0x2000)  # 8KB external RAM
        self.wram: bytearray = bytearray(0x2000)  # 8KB work RAM
        self.oam: bytearray = bytearray(0xA0)  # 160 bytes OAM
        self.io: bytearray = bytearray(0x80)  # 128 bytes I/O registers
        self.hram: bytearray = bytearray(0x7F)  # 127 bytes HRAM
        self.ie: int = 0  # 1 byte IE register

        self.apu: APU = APU()
                
        self.vram_np = np.frombuffer(self.vram, dtype=np.uint8)
        self.io_np = np.frombuffer(self.io, dtype=np.uint8)

        self.io[0xFF40 - 0xFF00] = 0x91  # LCDC — LCD on, BG on
        self.io[0xFF47 - 0xFF00] = 0xFC  # BGP  — default palette

        with open(boot_rom_path, "rb") as f:
            self.boot_rom: bytes = f.read()
            self.boot_rom_active: bool = True

    def read_u8(self, addr: int) -> int:
        data: int
        if addr < 0x8000:  # ROM
            if self.boot_rom_active and addr < 0x100:
                data = self.boot_rom[addr]
            else:
                data = self.rom.read_u8(addr)
            return data
        elif addr < 0xA000:  # VRAM
            data = self.vram[addr - 0x8000]
            return data
        elif addr < 0xC000:  # External RAM
            data = self.eram[addr - 0xA000]
            return data
        elif addr < 0xD000:  # Work RAM
            data = self.wram[addr - 0xC000]
            return data
        elif addr < 0xFE00:  # Echo RAM
            data = self.wram[addr - 0xE000]
            return data
        elif addr < 0xFEA0:  # OAM
            data = self.oam[addr - 0xFE00]
            return data
        elif addr < 0xFF00:  # Unusable memory
            return 0xFF
        elif addr < 0xFF80:  # I/O registers
            if 0xFF10 <= addr <= 0xFF26:
                data = self.apu.read(addr)
            else:
                data = self.io[addr - 0xFF00]
            return data
        elif addr < 0xFFFF:  # HRAM
            data = self.hram[addr - 0xFF80]
            return data
        elif addr == 0xFFFF:  # IE register
            return self.ie
        else:
            raise ValueError(f"MMU read from invalid address {addr:04X}")

    def write_u8(self, addr: int, data: int) -> None:
        if addr < 0x8000:  # ROM
            pass
        elif addr < 0xA000:  # VRAM
            self.vram[addr - 0x8000] = data
        elif addr < 0xC000:  # External RAM
            self.eram[addr - 0xA000] = data
        elif addr < 0xD000:  # Work RAM
            self.wram[addr - 0xC000] = data
        elif addr < 0xFE00:  # Echo RAM
            self.wram[addr - 0xE000] = data
        elif addr < 0xFEA0:  # OAM
            self.oam[addr - 0xFE00] = data
        elif addr < 0xFF00:  # Unusable memory
            pass
        elif addr < 0xFF80:  # I/O registers
            val = data

            self.io[addr - 0xFF00] = val

            if 0xFF10 <= addr <= 0xFF26:
                self.apu.write(addr, val)

            if addr == 0xFF50 and data == 0x01:
                self.boot_rom_active = False
        elif addr < 0xFFFF:  # HRAM
            self.hram[addr - 0xFF80] = data
        elif addr == 0xFFFF:  # IE register
            self.ie = data
        else:
            raise ValueError(f"MMU write to invalid address {addr:04X}")

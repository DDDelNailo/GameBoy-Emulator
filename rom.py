from pathlib import Path

# Header Constants
ENTRY_POINT = 0x0100, 0x0103
NINTENDO_LOGO = 0x0104, 0x0133
TITLE = 0x0134, 0x0143
MANUFACTURER_CODE = 0x013F, 0x0142
CGB_FLAG = 0x0143
NEW_LICENSEE_CODE = 0x0144, 0x0145
SGB_FLAG = 0x0146
CARTRIDGE_TYPE = 0x0147
ROM_SIZE = 0x0148
RAM_SIZE = 0x0149
DESTINATION_CODE = 0x014A
OLD_LICENSEE_CODE = 0x014B
MASK_ROM_VERSION_NUMBER = 0x014C
HEADER_CHECKSUM = 0x014D
GLOBAL_CHECKSUM = 0x014E, 0x014F

CARTRIDGE_TYPES: dict[int, str] = {
    0x00: "ROM ONLY",
    0x01: "MBC1",
    0x02: "MBC1+RAM",
    0x03: "MBC1+RAM+BATTERY",
    0x05: "MBC2",
    0x06: "MBC2+BATTERY",
    0x08: "ROM+RAM",
    0x09: "ROM+RAM+BATTERY",
    0x0B: "MMM01",
    0x0C: "MMM01+RAM",
    0x0D: "MMM01+RAM+BATTERY",
    0x0F: "MBC3+TIMER+BATTERY",
    0x10: "MBC3+TIMER+RAM+BATTERY",
    0x11: "MBC3",
    0x12: "MBC3+RAM",
    0x13: "MBC3+RAM+BATTERY",
    0x19: "MBC5",
    0x1A: "MBC5+RAM",
    0x1B: "MBC5+RAM+BATTERY",
    0x1C: "MBC5+RUMBLE",
    0x1D: "MBC5+RUMBLE+RAM",
    0x1E: "MBC5+RUMBLE+RAM+BATTERY",
    0x20: "MBC6",
    0x22: "MBC7+SENSOR+RUMBLE+RAM+BATTERY",
    0xFC: "POCKET CAMERA",
    0xFD: "BANDAI TAMA5",
    0xFE: "HuC3",
    0xFF: "HuC1+RAM+BATTERY",
}

ROM_SIZES: dict[int, str] = {
    0x00: "32 KiB (no banking)",
    0x01: "64 KiB",
    0x02: "128 KiB",
    0x03: "256 KiB",
    0x04: "512 KiB",
    0x05: "1 MiB",
    0x06: "2 MiB",
    0x07: "4 MiB",
    0x08: "8 MiB",
    0x52: "1.1 MiB",
    0x53: "1.2 MiB",
    0x54: "1.5 MiB",
}
ROM_BANKS: dict[int, int] = {
    0x00: 2,
    0x01: 4,
    0x02: 8,
    0x03: 16,
    0x04: 32,
    0x05: 64,
    0x06: 128,
    0x07: 256,
    0x08: 512,
    0x52: 72,
    0x53: 80,
    0x54: 96,
}

RAM_SIZES: dict[int, str] = {
    0x00: "None",
    0x01: "2 KiB",
    0x02: "8 KiB",
    0x03: "32 KiB (4 banks of 8 KiB each)",
    0x04: "128 KiB (16 banks of 8 KiB each)",
    0x05: "64 KiB (8 banks of 8 KiB each)",
}

DESTINATION_CODES: dict[int, str] = {
    0x00: "Japan (and possibly overseas)",
    0x01: "Overseas only",
}


class Rom:
    def __init__(self, path: str):
        self.data: bytes = Path(path).read_bytes()
        self.header: Header = Header(self)

    def read_u8(self, addr: int) -> bytes:
        return self.data[addr : addr + 1]

    def read_u16(self, addr: int) -> bytes:
        return self.data[addr : addr + 2]

    def read_bytes(self, addr: int, size: int) -> bytes:
        return self.data[addr : addr + size]

    def read_to_bytes(self, addr: int, to_addr: int) -> bytes:
        return self.data[addr : to_addr + 1]

    def print(self, from_addr: int, to_addr: int) -> None:
        data: bytes = self.read_to_bytes(from_addr, to_addr)

        print(" " * 9 + " ".join(f"{i:02X}" for i in range(16)))

        data_offset: int = 0
        line_offset: int = from_addr % 0x10

        out: str = ""

        while data_offset < len(data):
            if not out:
                addr: int = from_addr + data_offset - line_offset
                out = f"{addr:08X}"

                if line_offset:
                    out += " .." * line_offset

            out += f" {data[data_offset]:02X}"

            data_offset += 1
            line_offset += 1

            if line_offset == 0x10:
                print(out)
                out = ""
                line_offset = 0

        if out:
            out += " .." * (0x10 - line_offset)
            print(out)


class Header:
    def __init__(self, rom: Rom):
        self.b_entry_point: bytes = rom.read_to_bytes(*ENTRY_POINT)
        self.b_nintendo_logo: bytes = rom.read_to_bytes(*NINTENDO_LOGO)
        self.b_title: bytes = rom.read_to_bytes(*TITLE)
        self.title: str = self.b_title.decode("ascii").rstrip("\0")
        self.b_manufacturer_code: bytes = rom.read_to_bytes(*MANUFACTURER_CODE)
        self.manufacturer_code: str = self.b_manufacturer_code.decode("ascii").rstrip(
            "\0"
        )
        self.b_cgb_flag: bytes = rom.read_u8(CGB_FLAG)
        self.b_new_licensee_code: bytes = rom.read_u16(NEW_LICENSEE_CODE[0])
        self.b_sgb_flag: bytes = rom.read_u8(SGB_FLAG)
        self.b_cartridge_type: bytes = rom.read_u8(CARTRIDGE_TYPE)
        self.cartridge_type: str = CARTRIDGE_TYPES.get(
            self.b_cartridge_type[0], "Unknown"
        )
        self.b_rom_size: bytes = rom.read_u8(ROM_SIZE)
        self.rom_size: str = ROM_SIZES.get(self.b_rom_size[0], "Unknown")
        self.rom_banks: int = ROM_BANKS.get(self.b_rom_size[0], 0)
        self.b_ram_size: bytes = rom.read_u8(RAM_SIZE)
        self.ram_size: str = RAM_SIZES.get(self.b_ram_size[0], "Unknown")
        self.b_destination_code: bytes = rom.read_u8(DESTINATION_CODE)
        self.destination_code: str = DESTINATION_CODES.get(
            self.b_destination_code[0], "Unknown"
        )
        self.b_old_licensee_code: bytes = rom.read_u8(OLD_LICENSEE_CODE)
        self.licensee_code: str = ""
        self.b_mask_rom_version_number: bytes = rom.read_u8(MASK_ROM_VERSION_NUMBER)
        self.b_header_checksum: bytes = rom.read_u8(HEADER_CHECKSUM)
        self.b_global_checksum: bytes = rom.read_u16(GLOBAL_CHECKSUM[0])

    def info(self) -> None:
        print(f"Entry Point: {self.b_entry_point.hex().upper()}")
        print(f"Nintendo Logo: {self.b_nintendo_logo.hex().upper()}")
        print(f"Title: {self.title}")
        print(f"Manufacturer Code: {self.manufacturer_code}")
        print(f"CGB Flag: {self.b_cgb_flag.hex().upper()}")
        print(f"New Licensee Code: ")
        print(f"SGB Flag: {self.b_sgb_flag.hex().upper()}")
        print(f"Cartridge Type: {self.cartridge_type}")
        print(f"ROM Size: {self.rom_size}")
        print(f"ROM Banks: {self.rom_banks}")
        print(f"RAM Size: {self.ram_size}")
        print(f"Destination Code: {self.destination_code}")
        print(f"Old Licensee Code: {self.b_old_licensee_code.hex().upper()}")
        print(f"Mask ROM Version Number: {self.b_mask_rom_version_number.hex().upper()}")
        print(f"Header Checksum: {self.b_header_checksum.hex().upper()}")
        print(f"Global Checksum: {self.b_global_checksum.hex().upper()}")

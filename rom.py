from pathlib import Path

import logger

log = logger.get("ROM")

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

OLD_LICENSEE_CODES: dict[int, str] = {
    0x00: "None",
    0x01: "Nintendo",
    0x08: "Capcom",
    0x09: "HOT-B",
    0x0A: "Jaleco",
    0x0B: "Coconuts Japan",
    0x0C: "Elite Systems",
    0x13: "EA (Electronic Arts)",
    0x18: "Hudson Soft",
    0x19: "ITC Entertainment",
    0x1A: "Yanoman",
    0x1D: "Japan Clary",
    0x1F: "Virgin Games Ltd.",
    0x24: "PCM Complete",
    0x25: "San-X",
    0x28: "Kemco",
    0x29: "SETA Corporation",
    0x30: "Infogrames",
    0x31: "Nintendo",
    0x32: "Bandai",
    0x33: "New licensee code",
    0x34: "Konami",
    0x35: "HectorSoft",
    0x38: "Capcom",
    0x39: "Banpresto",
    0x3C: "Entertainment Interactive (stub)",
    0x3E: "Gremlin",
    0x41: "Ubi Soft",
    0x42: "Atlus",
    0x44: "Malibu Interactive",
    0x46: "Angel",
    0x47: "Spectrum HoloByte",
    0x49: "Irem",
    0x4A: "Virgin Games Ltd.",
    0x4D: "Malibu Interactive",
    0x4F: "U.S. Gold",
    0x50: "Absolute",
    0x51: "Acclaim Entertainment",
    0x52: "Activision",
    0x53: "Sammy USA Corporation",
    0x54: "GameTek",
    0x55: "Park Place",
    0x56: "LJN",
    0x57: "Matchbox",
    0x59: "Milton Bradley Company",
    0x5A: "Mindscape",
    0x5B: "Romstar",
    0x5C: "Naxat Soft",
    0x5D: "Tradewest",
    0x60: "Titus Interactive",
    0x61: "Virgin Games Ltd.",
    0x67: "Ocean Software",
    0x69: "EA (Electronic Arts)",
    0x6E: "Elite Systems",
    0x6F: "Electro Brain",
    0x70: "Infogrames5",
    0x71: "Interplay Entertainment",
    0x72: "Broderbund",
    0x73: "Sculptured Software",
    0x75: "The Sales Curve Limited",
    0x78: "THQ",
    0x79: "Accolade",
    0x7A: "Triffix Entertainment",
    0x7C: "MicroProse",
    0x7F: "Kemco",
    0x80: "Misawa Entertainment",
    0x83: "LOZC G.",
    0x86: "Tokuma Shoten",
    0x8B: "Bullet-Proof Software",
    0x8C: "Vic Tokai Corp.",
    0x8E: "Ape Inc.",
    0x8F: "I'Max",
    0x91: "Chunsoft Co.",
    0x92: "Video System",
    0x93: "Tsubaraya Productions",
    0x95: "Varie",
    0x96: "Yonezawa/S'Pal",
    0x97: "Kemco",
    0x99: "Arc",
    0x9A: "Nihon Bussan",
    0x9B: "Tecmo",
    0x9C: "Imagineer",
    0x9D: "Banpresto",
    0x9F: "Nova",
    0xA1: "Hori Electric",
    0xA2: "Bandai",
    0xA4: "Konami",
    0xA6: "Kawada",
    0xA7: "Takara",
    0xA9: "Technos Japan",
    0xAA: "Broderbund",
    0xAC: "Toei Animation",
    0xAD: "Toho",
    0xAF: "Namco",
    0xB0: "Acclaim Entertainment",
    0xB1: "ASCII Corporation or Nexsoft",
    0xB2: "Bandai",
    0xB4: "Square Enix",
    0xB6: "HAL Laboratory",
    0xB7: "SNK",
    0xB9: "Pony Canyon",
    0xBA: "Culture Brain",
    0xBB: "Sunsoft",
    0xBD: "Sony Imagesoft",
    0xBF: "Sammy Corporation",
    0xC0: "Taito",
    0xC2: "Kemco",
    0xC3: "Square",
    0xC4: "Tokuma Shoten",
    0xC5: "Data East",
    0xC6: "Tonkin House",
    0xC8: "Koei",
    0xC9: "UFL",
    0xCA: "Ultra Games",
    0xCB: "VAP, Inc.",
    0xCC: "Use Corporation",
    0xCD: "Meldac",
    0xCE: "Pony Canyon",
    0xCF: "Angel",
    0xD0: "Taito",
    0xD1: "SOFEL (Software Engineering Lab)",
    0xD2: "Quest",
    0xD3: "Sigma Enterprises",
    0xD4: "ASK Kodansha Co.",
    0xD6: "Naxat Soft",
    0xD7: "Copya System",
    0xD9: "Banpresto",
    0xDA: "Tomy",
    0xDB: "LJN",
    0xDD: "Nippon Computer Systems",
    0xDE: "Human Ent.",
    0xDF: "Altron",
    0xE0: "Jaleco",
    0xE1: "Towa Chiki",
    0xE2: "Yutaka",
    0xE3: "Varie",
    0xE5: "Epoch",
    0xE7: "Athena",
    0xE8: "Asmik Ace Entertainment",
    0xE9: "Natsume",
    0xEA: "King Records",
    0xEB: "Atlus",
    0xEC: "Epic/Sony Records",
    0xEE: "IGS",
    0xF0: "A Wave",
    0xF3: "Extreme Entertainment",
    0xFF: "LJN",
}
NEW_LICENSEE_CODES: dict[str, str] = {
    "00": "None",
    "01": "Nintendo Research & Development 1",
    "08": "Capcom",
    "13": "EA (Electronic Arts)",
    "18": "Hudson Soft",
    "19": "B-AI",
    "20": "KSS",
    "22": "Planning Office WADA",
    "24": "PCM Complete",
    "25": "San-X",
    "28": "Kemco",
    "29": "SETA Corporation",
    "30": "Viacom",
    "31": "Nintendo",
    "32": "Bandai",
    "33": "Ocean Software/Acclaim Entertainment",
    "34": "Konami",
    "35": "HectorSoft",
    "37": "Taito",
    "38": "Hudson Soft",
    "39": "Banpresto",
    "41": "Ubi Soft",
    "42": "Atlus",
    "44": "Malibu Interactive",
    "46": "Angel",
    "47": "Bullet-Proof Software",
    "49": "Irem",
    "50": "Absolute",
    "51": "Acclaim Entertainment",
    "52": "Activision",
    "53": "Sammy USA Corporation",
    "54": "Konami",
    "55": "Hi Tech Expressions",
    "56": "LJN",
    "57": "Matchbox",
    "58": "Mattel",
    "59": "Milton Bradley Company",
    "60": "Titus Interactive",
    "61": "Virgin Games Ltd.",
    "64": "Lucasfilm Games",
    "67": "Ocean Software",
    "69": "EA (Electronic Arts)",
    "70": "Infogrames",
    "71": "Interplay Entertainment",
    "72": "Broderbund",
    "73": "Sculptured Software",
    "75": "The Sales Curve Limited",
    "78": "THQ",
    "79": "Accolade",
    "80": "Misawa Entertainment",
    "83": "LOZC G.",
    "86": "Tokuma Shoten",
    "87": "Tsukuda Original",
    "91": "Chunsoft Co.",
    "92": "Video System",
    "93": "Ocean Software/Acclaim Entertainment",
    "95": "Varie",
    "96": "Yonezawa/S'Pal",
    "97": "Kaneko",
    "99": "Pack-In-Video",
    "9H": "Bottom Up",
    "A4": "Konami (Yu-Gi-Oh!)",
    "BL": "MTO",
    "DK": "Kodansha",
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

        log.debug("%s", " " * 9 + " ".join(f"{i:02X}" for i in range(16)))

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
                log.debug("%s", out)
                out = ""
                line_offset = 0

        if out:
            out += " .." * (0x10 - line_offset)
            log.debug("%s", out)


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
        if self.b_old_licensee_code[0] == 0x33:
            self.licensee_code = NEW_LICENSEE_CODES.get(
                self.b_new_licensee_code.decode("ascii"), "Unknown"
            )
        else:
            self.licensee_code = OLD_LICENSEE_CODES.get(
                self.b_old_licensee_code[0], "Unknown"
            )
        self.b_mask_rom_version_number: bytes = rom.read_u8(MASK_ROM_VERSION_NUMBER)
        self.b_header_checksum: bytes = rom.read_u8(HEADER_CHECKSUM)
        self.b_global_checksum: bytes = rom.read_u16(GLOBAL_CHECKSUM[0])

    def info(self) -> None:
        log.info("Entry Point: %s", self.b_entry_point.hex().upper())
        log.info("Nintendo Logo: %s", self.b_nintendo_logo.hex().upper())
        log.info("Title: %s", self.title)
        log.info("Manufacturer Code: %s", self.manufacturer_code)
        log.info("CGB Flag: %s", self.b_cgb_flag.hex().upper())
        log.info("SGB Flag: %s", self.b_sgb_flag.hex().upper())
        log.info("Cartridge Type: %s", self.cartridge_type)
        log.info("ROM Size: %s", self.rom_size)
        log.info("ROM Banks: %s", self.rom_banks)
        log.info("RAM Size: %s", self.ram_size)
        log.info("Destination Code: %s", self.destination_code)
        log.info("Licensee Code: %s", self.licensee_code)
        log.info(
            "Mask ROM Version Number: %s",
            self.b_mask_rom_version_number.hex().upper(),
        )
        log.info("Header Checksum: %s", self.b_header_checksum.hex().upper())
        log.info("Global Checksum: %s", self.b_global_checksum.hex().upper())

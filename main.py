from pathlib import Path


class Rom:
    def __init__(self, path: str):
        self.data: bytes = Path(path).read_bytes()

    def get(self, from_addr: int, to_addr: int) -> bytes:
        return self.data[from_addr:to_addr]

    def print(self, from_addr: int, to_addr: int) -> None:
        data: bytes = self.get(from_addr, to_addr)

        offsets: list[int] = [i for i in range(16)]
        print(f" " * 9 + " ".join(["0" + hex(i)[-1] for i in range(16)]).upper())

        for chunk_start in range(0x0, len(data), 0x10):
            out = hex(chunk_start)[2:].rjust(8, "0")
            for offset in offsets:
                out += " " + hex(data[chunk_start + offset])[2:].rjust(2, "0")
            print(out.upper())


rom: Rom = Rom("roms/Pokemon - Red Version.gb")
# header:  $0100—$014F
print(rom.get(0x0100, 0x014F))  # Header
rom.print(0x0100, 0x014F)  # Header

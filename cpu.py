import logger
from mmu import MMU

log = logger.get("CPU")

log = logger.get("CPU")


class CPU:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self.pc: int = 0x0000
        self.sp: int = 0x0000
        self.a: int = 0x00
        self.f: int = 0x00
        self.b: int = 0x00
        self.c: int = 0x00
        self.d: int = 0x00
        self.e: int = 0x00
        self.h: int = 0x00
        self.l: int = 0x00

        self.ime: bool = False

    @property
    def af(self) -> int:
        return (self.a << 8) | self.f

    @af.setter
    def af(self, v: int):
        self.a = (v >> 8) & 0xFF
        self.f = v & 0xF0  # low nibble always 0
        log.debug("AF <- 0x%04X", v & 0xFFFF)

    @property
    def hl(self) -> int:
        return (self.h << 8) | self.l

    @hl.setter
    def hl(self, v: int):
        self.h = (v >> 8) & 0xFF
        self.l = v & 0xFF
        log.debug("HL <- 0x%04X", v & 0xFFFF)

    @property
    def bc(self) -> int:
        return (self.b << 8) | self.c

    @bc.setter
    def bc(self, v: int):
        self.b = (v >> 8) & 0xFF
        self.c = v & 0xFF
        log.debug("BC <- 0x%04X", v & 0xFFFF)

    @property
    def de(self) -> int:
        return (self.d << 8) | self.e

    @de.setter
    def de(self, v: int):
        self.d = (v >> 8) & 0xFF
        self.e = v & 0xFF
        log.debug("DE <- 0x%04X", v & 0xFFFF)

    # Flag helpers
    def flag_z(self) -> int:
        return (self.f >> 7) & 1

    def flag_n(self) -> int:
        return (self.f >> 6) & 1

    def flag_h(self) -> int:
        return (self.f >> 5) & 1

    def flag_c(self) -> int:
        return (self.f >> 4) & 1

    def set_flags(
        self,
        z: int | None = None,
        n: int | None = None,
        h: int | None = None,
        c: int | None = None,
    ) -> None:
        old_f: int = self.f
        if z is not None:
            self.f = (self.f & ~0x80) | ((z & 1) << 7)
        if n is not None:
            self.f = (self.f & ~0x40) | ((n & 1) << 6)
        if h is not None:
            self.f = (self.f & ~0x20) | ((h & 1) << 5)
        if c is not None:
            self.f = (self.f & ~0x10) | ((c & 1) << 4)
        log.debug(
            "F 0x%02X -> 0x%02X (Z=%s N=%s H=%s C=%s)",
            old_f,
            self.f,
            "-" if z is None else z,
            "-" if n is None else n,
            "-" if h is None else h,
            "-" if c is None else c,
        )

    def step(self) -> int:
        opcode: bytes = self.mmu.read(self.pc)
        log.debug("PC=0x%04X OP=0x%02X", self.pc, opcode[0])
        self.pc = (self.pc + 1) & 0xFFFF
        return self.execute(opcode)

    def execute(self, opcode: bytes) -> int:
        log.error("Unimplemented opcode 0x%02X", opcode[0])
        exit()
        return 0

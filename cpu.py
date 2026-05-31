from mmu import MMU
from typing import Callable

ADDRESSES: dict[str, dict[int, str]] = {
    "r8": {
        0b000: "b",
        0b001: "c",
        0b010: "d",
        0b011: "e",
        0b100: "h",
        0b101: "l",
        0b110: "(hl)",
        0b111: "a",
    },
    "r16": {
        0b00: "bc",
        0b01: "de",
        0b10: "hl",
        0b11: "sp",
    },
    "r16stk": {
        0b00: "bc",
        0b01: "de",
        0b10: "hl",
        0b11: "af",
    },
    "r16mem": {
        0b00: "bc",
        0b01: "de",
        0b10: "hl+",
        0b11: "hl-",
    },
    "cond": {
        0b00: "nz",
        0b01: "z",
        0b10: "nc",
        0b11: "c",
    },
}


class CPU:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self._pc: int = 0x0000
        self._sp: int = 0x0000
        self._a: int = 0x00
        self._b: int = 0x00
        self._c: int = 0x00
        self._d: int = 0x00
        self._e: int = 0x00
        self._f: int = 0x00
        self._h: int = 0x00
        self._l: int = 0x00

        self.pc_jumped: bool = False

        self.ime: bool = False
        self.op_codes: dict[str, Callable[[int], int]] = self.build_op_codes(
            {
                # "00000000": self._op_nop,
                "00rr0001": self._op_ld_r16_imm16,
                "00rr0010": self._op_ld_p_r16mem_a,
                "00rr1010": self._op_ld_a_p_r16mem,
                # "........": self._op_ld_p_imm16_sp,
                "00rr0011": self._op_inc_r16,
                # "00rr1011": self._op_dec_r16,
                # "........": self._op_add_hl_r16,
                "00ttt100": self._op_inc_r8,
                "00ttt101": self._op_dec_r8,
                "00ttt110": self._op_ld_r8_imm8,
                # "........": self._op_rlca,
                # "........": self._op_rrca,
                "00010111": self._op_rla,
                # "........": self._op_rra,
                # "........": self._op_daa,
                # "........": self._op_cpl,
                # "........": self._op_scf,
                # "........": self._op_ccf,
                "00011000": self._op_jr_imm8,
                "001rr000": self._op_jr_cond_imm8,
                # "........": self._op_stop,
                "01xxxyyy": self._op_ld_r8_r8,
                # "........": self._op_halt,
                # "........": self._op_add_a_r8,
                # "........": self._op_adc_a_r8,
                "10010ttt": self._op_sub_a_r8,
                # "........": self._op_sbc_a_r8,
                # "........": self._op_and_a_r8,
                "10101ttt": self._op_xor_a_r8,
                # "........": self._op_or_a_r8,
                "10111110": self._op_cp_a_r8,
                # "........": self._op_add_a_imm8,
                # "........": self._op_adc_a_imm8,
                # "........": self._op_sub_a_imm8,
                # "........": self._op_sbc_a_imm8,
                # "........": self._op_and_a_imm8,
                # "........": self._op_xor_a_imm8,
                # "........": self._op_or_a_imm8,
                "11111110": self._op_cp_a_imm8,
                # "........": self._op_ret_cond,
                "11001001": self._op_ret,
                # "........": self._op_reti,
                # "........": self._op_jp_cond_imm16,
                # "........": self._op_jp_imm16,
                # "........": self._op_jp_hl,
                # "........": self._op_call_cond_imm16,
                "11001101": self._op_call_imm16,
                # "........": self._op_rst_tgt3,
                "11rr0001": self._op_pop_r16stk,
                "11rr0101": self._op_push_r16stk,
                "11001011": self._op_PREFIX,
                "11100010": self._op_ldh_p_c_a,
                "11100000": self._op_ldh_p_imm8_a,
                "11101010": self._op_ld_p_imm16_a,
                # "........": self._op_ldh_a_p_c,
                "11110000": self._op_ldh_a_p_imm8,
                # "........": self._op_ld_a_imm16,
                # "........": self._op_add_sp_imm8,
                # "........": self._op_ld_hl_sp_plus_imm8,
                # "........": self._op_ld_sp_hl,
                # "........": self._op_di,
                # "........": self._op_ei,
            }
        )
        self.prefix_op_codes: dict[str, Callable[[int], int]] = self.build_op_codes(
            {
                # "........": self._op_rlc_r8,
                # "........": self._op_rrc_r8,
                "00010ttt": self._op_rl_r8,
                # "........": self._op_rr_r8,
                # "........": self._op_sla_r8,
                # "........": self._op_sra_r8,
                # "........": self._op_swap_r8,
                # "........": self._op_srl_r8,
                "01xxxyyy": self.bit_b3_r8,
                # "........": self.res_b3_r8,
                # "........": self.set_b3_r8,
            }
        )

    @staticmethod
    def build_op_codes(
        op_codes_base: dict[str, Callable[[int], int]],
    ) -> dict[str, Callable[[int], int]]:
        op_codes: dict[str, Callable[[int], int]] = {}

        for pattern, func in op_codes_base.items():
            if "r" in pattern:
                for r in range(4):
                    op_codes[pattern.replace("rr", format(r, "02b"))] = func
            if "t" in pattern:
                for t in range(8):
                    op_codes[pattern.replace("ttt", format(t, "03b"))] = func
            elif "x" in pattern and "y" in pattern:
                for x in range(8):
                    for y in range(8):
                        op_codes[
                            pattern.replace("xxx", format(x, "03b")).replace(
                                "yyy", format(y, "03b")
                            )
                        ] = func
            else:
                op_codes[pattern] = func

        return op_codes

    @property
    def pc(self) -> int:
        return self._pc

    @pc.setter
    def pc(self, v: int):
        self._pc = v & 0xFFFF

    @property
    def a(self) -> int:
        return self._a

    @a.setter
    def a(self, v: int):
        self._a = v & 0xFF

    @property
    def b(self) -> int:
        return self._b

    @b.setter
    def b(self, v: int):
        self._b = v & 0xFF

    @property
    def c(self) -> int:
        return self._c

    @c.setter
    def c(self, v: int):
        self._c = v & 0xFF

    @property
    def d(self) -> int:
        return self._d

    @d.setter
    def d(self, v: int):
        self._d = v & 0xFF

    @property
    def e(self) -> int:
        return self._e

    @e.setter
    def e(self, v: int):
        self._e = v & 0xFF

    @property
    def f(self) -> int:
        return self._f

    @f.setter
    def f(self, v: int):
        self._f = v & 0xFF

    @property
    def h(self) -> int:
        return self._h

    @h.setter
    def h(self, v: int):
        self._h = v & 0xFF

    @property
    def l(self) -> int:
        return self._l

    @l.setter
    def l(self, v: int):
        self._l = v & 0xFF

    @property
    def sp(self) -> int:
        return self._sp

    @sp.setter
    def sp(self, v: int):
        self._sp = v & 0xFFFF

    @property
    def af(self) -> int:
        return (self.a << 8) | self.f

    @af.setter
    def af(self, v: int):
        self.a = (v >> 8) & 0xFF
        self.f = v & 0xF0  # low nibble always 0

    @property
    def hl(self) -> int:
        return (self.h << 8) | self.l

    @hl.setter
    def hl(self, v: int):
        self.h = (v >> 8) & 0xFF
        self.l = v & 0xFF

    @property
    def bc(self) -> int:
        return (self.b << 8) | self.c

    @bc.setter
    def bc(self, v: int):
        self.b = (v >> 8) & 0xFF
        self.c = v & 0xFF

    @property
    def de(self) -> int:
        return (self.d << 8) | self.e

    @de.setter
    def de(self, v: int):
        self.d = (v >> 8) & 0xFF
        self.e = v & 0xFF

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
        flags: bytearray = bytearray()

        if z is not None:
            flags.append(0x80 if z & 1 else 0x00)
        if n is not None:
            flags.append(0x40 if n & 1 else 0x00)
        if h is not None:
            flags.append(0x20 if h & 1 else 0x00)
        if c is not None:
            flags.append(0x10 if c & 1 else 0x00)

        self.f = sum(flags)

    def advance_pc(self, n: int = 1) -> None:
        self.pc += n

    def get_advance_pc_u8(self) -> int:
        self.advance_pc(1)
        return self.mmu.read_u8(self.pc)

    def get_advance_pc_u16(self) -> int:
        lo = self.get_advance_pc_u8()
        hi = self.get_advance_pc_u8()
        return lo | (hi << 8)

    @staticmethod
    def to_signed_u8(v: int) -> int:
        return v - 0x100 if v & 0x80 else v

    @staticmethod
    def to_signed_u16(v: int) -> int:
        return v - 0x10000 if v & 0x8000 else v

    def step(self) -> int:
        self.pc_jumped = False

        opcode: int = self.mmu.read_u8(self.pc)
        cycles: int = self.execute(opcode)

        if not self.pc_jumped:
            self.advance_pc()

        return cycles

    def execute(self, opcode: int, prefix: bool = False) -> int:
        opcode_str: str = format(opcode, "08b")

        if prefix:
            if opcode_str in self.prefix_op_codes:
                return self.prefix_op_codes[opcode_str](opcode)
        elif opcode_str in self.op_codes:
            return self.op_codes[opcode_str](opcode)

        print(f"Unimplemented opcode 0x{opcode:02X}")
        exit()

    # def _op_nop(self, opcode: int) -> int:
    #     return 4

    def _op_ld_r16_imm16(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11
        r16: str = ADDRESSES["r16"][dest_reg]
        imm16: int = self.get_advance_pc_u16()

        setattr(self, r16, imm16)

        return 12

    def _op_ld_p_r16mem_a(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        r16mem: str = ADDRESSES["r16mem"][src_reg]

        match r16mem:
            case "bc":
                addr: int = self.bc
            case "de":
                addr: int = self.de
            case "hl+":
                addr: int = self.hl
                self.hl += 1
            case "hl-":
                addr: int = self.hl
                self.hl -= 1
            case _:
                print(f"Invalid r16mem register code: {src_reg}")
                exit()

        self.mmu.write_u8(addr, self.a)

        return 8

    def _op_ld_a_p_r16mem(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        r16mem: str = ADDRESSES["r16mem"][src_reg]

        match r16mem:
            case "bc":
                addr: int = self.bc
            case "de":
                addr: int = self.de
            case "hl+":
                addr: int = self.hl
                self.hl += 1
            case "hl-":
                addr: int = self.hl
                self.hl -= 1
            case _:
                print(f"Invalid r16mem register code: {src_reg}")
                exit()

        value: int = self.mmu.read_u8(addr)
        self.a = value

        return 8

    # def _op_ld_p_imm16_sp(self, opcode: int) -> int:
    #     return 0

    def _op_inc_r16(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11
        r16: str = ADDRESSES["r16"][dest_reg]

        value = (getattr(self, r16) + 1) & 0xFFFF
        setattr(self, r16, value)

        return 8

    # def _op_dec_r16(self, opcode: int) -> int:
    #     return 0

    # def _op_add_hl_r16(self, opcode: int) -> int:
    #     return 0

    def _op_inc_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]

        if r8 == "(hl)":
            addr: int = self.hl
            original: int = self.mmu.read_u8(addr)
            value: int = original + 1
            self.mmu.write_u8(addr, value & 0xFF)
        else:
            original: int = getattr(self, r8)
            value: int = original + 1
            setattr(self, r8, value)

        self.set_flags(
            z=(value & 0xFF) == 0,
            n=0,
            h=(original & 0x0F) == 0x0F,
        )

        return 4

    def _op_dec_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]

        if r8 == "(hl)":
            addr: int = self.hl
            original: int = self.mmu.read_u8(addr)
            value: int = original - 1
            self.mmu.write_u8(addr, value & 0xFF)
        else:
            original: int = getattr(self, r8)
            value: int = original - 1
            setattr(self, r8, value)

        self.set_flags(
            z=(value & 0xFF) == 0,
            n=1,
            h=(original & 0x0F) == 0x00,
        )

        return 4

    def _op_ld_r8_imm8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]
        imm8: int = self.get_advance_pc_u8()

        setattr(self, r8, imm8)

        return 8

    # def _op_rlca(self, opcode: int) -> int:
    #     return 0

    # def _op_rrca(self, opcode: int) -> int:
    #     return 0

    def _op_rla(self, opcode: int) -> int:
        carry: int = (self.a >> 7) & 1
        self.a = ((self.a << 1) | self.flag_c()) & 0xFF

        self.set_flags(
            z=0,
            n=0,
            h=0,
            c=carry,
        )

        return 8

    # def _op_rra(self, opcode: int) -> int:
    #     return 0

    # def _op_daa(self, opcode: int) -> int:
    #     return 0

    # def _op_cpl(self, opcode: int) -> int:
    #     return 0

    # def _op_scf(self, opcode: int) -> int:
    #     return 0

    # def _op_ccf(self, opcode: int) -> int:
    #     return 0

    def _op_jr_imm8(self, opcode: int) -> int:
        imm8: int = self.to_signed_u8(self.get_advance_pc_u8())
        jump: int = (self.pc + imm8) & 0xFFFF

        self.pc = jump + 1
        self.pc_jumped = True

        return 12

    def _op_jr_cond_imm8(self, opcode: int) -> int:
        cond_code: int = (opcode >> 3) & 0b11
        cond: str = ADDRESSES["cond"][cond_code]
        imm8: int = self.to_signed_u8(self.get_advance_pc_u8())

        jump: int = (self.pc + imm8) & 0xFFFF

        cc: bool = False
        match cond:
            case "nz":
                if not self.flag_z():
                    cc = True
            case "z":
                if self.flag_z():
                    cc = True
            case "nc":
                if not self.flag_c():
                    cc = True
            case "c":
                if self.flag_c():
                    cc = True
            case _:
                print(f"Invalid condition code: {cond_code}")
                exit()

        if cc:
            self.pc = jump + 1
            self.pc_jumped = True

        return 12 if cc else 8

    # def _op_stop(self, opcode: int) -> int:
    #     return 0

    def _op_ld_r8_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        src_reg: int = opcode & 0b111
        dest_r8: str = ADDRESSES["r8"][dest_reg]
        src_r8: str = ADDRESSES["r8"][src_reg]

        value: int = 0

        if src_r8 == "(hl)":
            addr: int = self.hl
            value: int = self.mmu.read_u8(addr)
        else:
            value: int = getattr(self, src_r8)

        if dest_r8 == "(hl)":
            addr: int = self.hl
            self.mmu.write_u8(addr, value)
        else:
            setattr(self, dest_r8, value)

        return 4

    # def _op_halt(self, opcode: int) -> int:
    #     return 0

    # def _op_add_a_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_adc_a_r8(self, opcode: int) -> int:
    #     return 0

    def _op_sub_a_r8(self, opcode: int) -> int:
        src_reg: int = opcode & 0b111
        r8: str = ADDRESSES["r8"][src_reg]

        value: int = 0
        if r8 == "(hl)":
            addr: int = self.hl
            value: int = self.mmu.read_u8(addr)
        else:
            value: int = getattr(self, r8)

        result: int = (self.a - value) & 0xFF
        self.a = result

        self.set_flags(
            z=result == 0,
            n=1,
            h=(self.a & 0x0F) < (value & 0x0F),
            c=self.a < value,
        )

        return 4

    # def _op_sbc_a_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_and_a_r8(self, opcode: int) -> int:
    #     return 0

    def _op_xor_a_r8(self, opcode: int) -> int:
        src_reg: int = opcode & 0b111
        r8: str = ADDRESSES["r8"][src_reg]

        value: int = 0

        if r8 == "(hl)":
            addr: int = self.hl
            value: int = self.mmu.read_u8(addr)
        else:
            value: int = getattr(self, r8)

        self.a ^= value

        self.set_flags(
            z=self.a == 0,
            n=0,
            h=0,
            c=0,
        )
        return 4

    # def _op_or_a_r8(self, opcode: int) -> int:
    #     return 0

    def _op_cp_a_r8(self, opcode: int) -> int:
        return 0

    # def _op_add_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_adc_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_sub_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_sbc_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_and_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_xor_a_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_or_a_imm8(self, opcode: int) -> int:
    #     return 0

    def _op_cp_a_imm8(self, opcode: int) -> int:
        imm8: int = self.get_advance_pc_u8()

        result: int = (self.a - imm8) & 0xFF

        self.set_flags(
            z=result == 0,
            n=1,
            h=(self.a & 0x0F) < (imm8 & 0x0F),
            c=self.a < imm8,
        )

        return 8

    # def _op_ret_cond(self, opcode: int) -> int:
    #     return 0

    def _op_ret(self, opcode: int) -> int:
        low: int = self.mmu.read_u8(self.sp)
        self.sp += 1
        high: int = self.mmu.read_u8(self.sp)
        self.sp += 1

        addr: int = (high << 8) | low
        self.pc = addr
        self.pc_jumped = True

        return 16

    # def _op_reti(self, opcode: int) -> int:
    #     return 0

    # def _op_jp_cond_imm16(self, opcode: int) -> int:
    #     return 0

    # def _op_jp_imm16(self, opcode: int) -> int:
    #     return 0

    # def _op_jp_hl(self, opcode: int) -> int:
    #     return 0

    # def _op_call_cond_imm16(self, opcode: int) -> int:
    #     return 0

    def _op_call_imm16(self, opcode: int) -> int:
        imm16: int = self.get_advance_pc_u16()

        self.advance_pc()

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, self.pc >> 8 & 0xFF)
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, self.pc & 0xFF)

        self.pc = imm16
        self.pc_jumped = True

        return 24

    # def _op_rst_tgt3(self, opcode: int) -> int:
    #     return 0

    def _op_pop_r16stk(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11
        r16stk: str = ADDRESSES["r16stk"][dest_reg]

        low: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF
        high: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF

        value: int = (high << 8) | low
        setattr(self, r16stk, value)

        return 12

    def _op_push_r16stk(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        r16stk: str = ADDRESSES["r16stk"][src_reg]

        value: int = getattr(self, r16stk)

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, (value >> 8) & 0xFF)
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, value & 0xFF)

        return 16

    def _op_PREFIX(self, opcode: int) -> int:
        opcode = self.get_advance_pc_u8()
        return self.execute(opcode, prefix=True)

    def _op_ldh_p_c_a(self, opcode: int) -> int:
        addr: int = 0xFF00 + self.c

        self.mmu.write_u8(addr, self.a)

        return 8

    def _op_ldh_p_imm8_a(self, opcode: int) -> int:
        imm8: int = self.get_advance_pc_u8()
        addr: int = 0xFF00 + imm8

        self.mmu.write_u8(addr, self.a)

        return 12

    def _op_ld_p_imm16_a(self, opcode: int) -> int:
        imm16: int = self.get_advance_pc_u16()

        self.mmu.write_u8(imm16, self.a)

        return 16

    # def _op_ldh_a_p_c(self, opcode: int) -> int:
    #     return 0

    def _op_ldh_a_p_imm8(self, opcode: int) -> int:
        imm8: int = self.get_advance_pc_u8()
        addr: int = 0xFF00 + imm8

        value: int = self.mmu.read_u8(addr)
        self.a = value

        return 12

    # def _op_ld_a_imm16(self, opcode: int) -> int:
    #     return 0

    # def _op_add_sp_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_ld_hl_sp_plus_imm8(self, opcode: int) -> int:
    #     return 0

    # def _op_ld_sp_hl(self, opcode: int) -> int:
    #     return 0

    # def _op_di(self, opcode: int) -> int:
    #     return 0

    # def _op_ei(self, opcode: int) -> int:
    #     return 0

    # def _op_rlc_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_rrc_r8(self, opcode: int) -> int:
    #     return 0

    def _op_rl_r8(self, opcode: int) -> int:
        dest_reg: int = opcode & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]

        value: int = 0

        if r8 == "(hl)":
            addr: int = self.hl
            value: int = self.mmu.read_u8(addr)
        else:
            value: int = getattr(self, r8)

        carry: int = (value >> 7) & 1
        value = ((value << 1) | self.flag_c()) & 0xFF

        if r8 == "(hl)":
            addr: int = self.hl
            self.mmu.write_u8(addr, value)
        else:
            setattr(self, r8, value)

        self.set_flags(
            z=value == 0,
            n=0,
            h=0,
            c=carry,
        )

        return 8

    # def _op_rr_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_sla_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_sra_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_swap_r8(self, opcode: int) -> int:
    #     return 0

    # def _op_srl_r8(self, opcode: int) -> int:
    #     return 0

    def bit_b3_r8(self, opcode: int) -> int:
        bit: int = (opcode >> 3) & 0b111
        src_reg: int = opcode & 0b111
        r8: str = ADDRESSES["r8"][src_reg]

        value: int = 0

        if r8 == "(hl)":
            addr: int = self.hl
            value = self.mmu.read_u8(addr)
        else:
            value = getattr(self, r8)

        self.set_flags(
            z=(value & (1 << bit)) == 0,
            n=0,
            h=1,
            c=None,
        )

        return 8

    # def res_b3_r8(self, opcode: int) -> int:
    #     return 0

    # def set_b3_r8(self, opcode: int) -> int:
    #     return 0

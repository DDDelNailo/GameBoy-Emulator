from mmu import MMU
from typing import Callable

# TODO: remove addresses dict and check manually inside functions
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
        self.pc: int = 0x0000
        self.sp: int = 0x0000
        self.a: int = 0x00
        self.b: int = 0x00
        self.c: int = 0x00
        self.d: int = 0x00
        self.e: int = 0x00
        self.f: int = 0x00
        self.h: int = 0x00
        self.l: int = 0x00

        self.pc_jumped: bool = False

        self.ime: bool = False
        self.op_table: list[Callable[[int], int]] = [self._op_unimplemented] * 256
        self.cb_table: list[Callable[[int], int]] = [self._op_unimplemented] * 256
        self.op_codes: dict[str, Callable[[int], int]] = {
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
        self.cb_codes: dict[str, Callable[[int], int]] = {
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

        self.build_op_codes()
        self.build_cb_codes()

    def build_op_codes(self) -> None:
        for pattern, func in self.op_codes.items():
            if "r" in pattern:
                for r in range(4):
                    self.op_table[int(pattern.replace("rr", format(r, "02b")), 2)] = (
                        func
                    )
            elif "t" in pattern:
                for t in range(8):
                    self.op_table[int(pattern.replace("ttt", format(t, "03b")), 2)] = (
                        func
                    )
            elif "x" in pattern and "y" in pattern:
                for x in range(8):
                    for y in range(8):
                        self.op_table[
                            int(
                                pattern.replace("xxx", format(x, "03b")).replace(
                                    "yyy", format(y, "03b")
                                ),
                                2,
                            )
                        ] = func
            else:
                self.op_table[int(pattern, 2)] = func

    def build_cb_codes(self) -> None:
        for pattern, func in self.cb_codes.items():
            if "t" in pattern:
                for t in range(8):
                    self.cb_table[int(pattern.replace("ttt", format(t, "03b")), 2)] = (
                        func
                    )
            elif "x" in pattern and "y" in pattern:
                for x in range(8):
                    for y in range(8):
                        self.cb_table[
                            int(
                                pattern.replace("xxx", format(x, "03b")).replace(
                                    "yyy", format(y, "03b")
                                ),
                                2,
                            )
                        ] = func
            else:
                self.cb_table[int(pattern, 2)] = func

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
            self.pc = (self.pc + 1) & 0xFFFF

        return cycles

    def execute(self, opcode: int, prefix: bool = False) -> int:
        if prefix:
            return self.cb_table[opcode](opcode)

        return self.op_table[opcode](opcode)

    def _op_unimplemented(self, opcode: int) -> int:
        print(f"Unimplemented opcode 0x{opcode:02X}")
        exit()

    # def _op_nop(self, opcode: int) -> int:
    #     return 4

    def _op_ld_r16_imm16(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11
        # inline get_advance_pc_u16
        self.pc = (self.pc + 1) & 0xFFFF
        lo: int = self.mmu.read_u8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        hi: int = self.mmu.read_u8(self.pc)
        imm16: int = lo | (hi << 8)

        match dest_reg:
            case 0:
                self.b = (imm16 >> 8) & 0xFF
                self.c = imm16 & 0xFF
            case 1:
                self.d = (imm16 >> 8) & 0xFF
                self.e = imm16 & 0xFF
            case 2:
                self.h = (imm16 >> 8) & 0xFF
                self.l = imm16 & 0xFF
            case 3:
                self.sp = imm16 & 0xFFFF
            case _:
                print(f"Invalid r16 register code: {dest_reg}")
                exit()

        return 12

    def _op_ld_p_r16mem_a(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        r16mem: str = ADDRESSES["r16mem"][src_reg]

        match r16mem:
            case "bc":
                addr: int = (self.b << 8) | self.c
            case "de":
                addr: int = (self.d << 8) | self.e
            case "hl+":
                addr = (self.h << 8) | self.l
                hl: int = (addr + 1) & 0xFFFF
                self.h = (hl >> 8) & 0xFF
                self.l = hl & 0xFF
            case "hl-":
                addr = (self.h << 8) | self.l
                hl = (addr - 1) & 0xFFFF
                self.h = (hl >> 8) & 0xFF
                self.l = hl & 0xFF
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
                addr: int = (self.b << 8) | self.c
            case "de":
                addr: int = (self.d << 8) | self.e
            case "hl+":
                addr = (self.h << 8) | self.l
                hl: int = (addr + 1) & 0xFFFF
                self.h = (hl >> 8) & 0xFF
                self.l = hl & 0xFF
            case "hl-":
                addr = (self.h << 8) | self.l
                hl = (addr - 1) & 0xFFFF
                self.h = (hl >> 8) & 0xFF
                self.l = hl & 0xFF
            case _:
                print(f"Invalid r16mem register code: {src_reg}")
                exit()

        value: int = self.mmu.read_u8(addr)
        self.a = value & 0xFF

        return 8

    # def _op_ld_p_imm16_sp(self, opcode: int) -> int:
    #     return 0

    def _op_inc_r16(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11

        match dest_reg:
            case 0:
                value: int = ((self.b << 8) | self.c) + 1
                value &= 0xFFFF
                self.b = (value >> 8) & 0xFF
                self.c = value & 0xFF
            case 1:
                value = ((self.d << 8) | self.e) + 1
                value &= 0xFFFF
                self.d = (value >> 8) & 0xFF
                self.e = value & 0xFF
            case 2:
                value = ((self.h << 8) | self.l) + 1
                value &= 0xFFFF
                self.h = (value >> 8) & 0xFF
                self.l = value & 0xFF
            case 3:
                self.sp = (self.sp + 1) & 0xFFFF
            case _:
                print(f"Invalid r16 register code: {dest_reg}")
                exit()

        return 8

    # def _op_dec_r16(self, opcode: int) -> int:
    #     return 0

    # def _op_add_hl_r16(self, opcode: int) -> int:
    #     return 0

    def _op_inc_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]

        if r8 == "(hl)":
            addr: int = (self.h << 8) | self.l
            original: int = self.mmu.read_u8(addr)
            value: int = original + 1
            self.mmu.write_u8(addr, value & 0xFF)
        elif r8 == "a":
            original = self.a
            value = original + 1
            self.a = value & 0xFF
        elif r8 == "b":
            original = self.b
            value = original + 1
            self.b = value & 0xFF
        elif r8 == "c":
            original = self.c
            value = original + 1
            self.c = value & 0xFF
        elif r8 == "d":
            original = self.d
            value = original + 1
            self.d = value & 0xFF
        elif r8 == "e":
            original = self.e
            value = original + 1
            self.e = value & 0xFF
        elif r8 == "h":
            original = self.h
            value = original + 1
            self.h = value & 0xFF
        elif r8 == "l":
            original = self.l
            value = original + 1
            self.l = value & 0xFF
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        self.f = (
            (int(value & 0xFF == 0) << 7)
            | (0 << 6)
            | (int((original & 0x0F) == 0x0F) << 5)
            | (0 << 4)
        ) & 0xF0

        return 4

    def _op_dec_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        r8: str = ADDRESSES["r8"][dest_reg]

        if r8 == "(hl)":
            addr: int = (self.h << 8) | self.l
            original: int = self.mmu.read_u8(addr)
            value: int = original - 1
            self.mmu.write_u8(addr, value & 0xFF)
        elif r8 == "a":
            original = self.a
            value = original - 1
            self.a = value & 0xFF
        elif r8 == "b":
            original = self.b
            value = original - 1
            self.b = value & 0xFF
        elif r8 == "c":
            original = self.c
            value = original - 1
            self.c = value & 0xFF
        elif r8 == "d":
            original = self.d
            value = original - 1
            self.d = value & 0xFF
        elif r8 == "e":
            original = self.e
            value = original - 1
            self.e = value & 0xFF
        elif r8 == "h":
            original = self.h
            value = original - 1
            self.h = value & 0xFF
        elif r8 == "l":
            original = self.l
            value = original - 1
            self.l = value & 0xFF
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        self.f = (
            (int(value & 0xFF == 0) << 7)
            | (1 << 6)
            | (int((original & 0x0F) == 0x00) << 5)
            | (0 << 4)
        ) & 0xF0

        return 4

    def _op_ld_r8_imm8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)

        if dest_reg == 0:
            self.b = imm8 & 0xFF
        elif dest_reg == 1:
            self.c = imm8 & 0xFF
        elif dest_reg == 2:
            self.d = imm8 & 0xFF
        elif dest_reg == 3:
            self.e = imm8 & 0xFF
        elif dest_reg == 4:
            self.h = imm8 & 0xFF
        elif dest_reg == 5:
            self.l = imm8 & 0xFF
        elif dest_reg == 7:
            self.a = imm8 & 0xFF
        else:
            print(f"Invalid r8 register code: {dest_reg}")
            exit()

        return 8

    # def _op_rlca(self, opcode: int) -> int:
    #     return 0

    # def _op_rrca(self, opcode: int) -> int:
    #     return 0

    def _op_rla(self, opcode: int) -> int:
        carry: int = (self.a >> 7) & 1
        self.a = ((self.a << 1) | ((self.f >> 4) & 1)) & 0xFF

        self.f = ((0 << 7) | (0 << 6) | (0 << 5) | (carry << 4)) & 0xF0

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
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.to_signed_u8(self.mmu.read_u8(self.pc))
        jump: int = (self.pc + imm8) & 0xFFFF

        self.pc = (jump + 1) & 0xFFFF
        self.pc_jumped = True

        return 12

    def _op_jr_cond_imm8(self, opcode: int) -> int:
        cond_code: int = (opcode >> 3) & 0b11
        cond: str = ADDRESSES["cond"][cond_code]
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.to_signed_u8(self.mmu.read_u8(self.pc))

        jump: int = (self.pc + imm8) & 0xFFFF

        cc: bool = False
        match cond:
            case "nz":
                if (self.f & 0x80) == 0:
                    cc = True
            case "z":
                if (self.f & 0x80) != 0:
                    cc = True
            case "nc":
                if (self.f & 0x10) == 0:
                    cc = True
            case "c":
                if (self.f & 0x10) != 0:
                    cc = True
            case _:
                print(f"Invalid condition code: {cond_code}")
                exit()

        if cc:
            self.pc = (jump + 1) & 0xFFFF
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
            addr: int = (self.h << 8) | self.l
            value: int = self.mmu.read_u8(addr)
        elif src_r8 == "a":
            value = self.a
        elif src_r8 == "b":
            value = self.b
        elif src_r8 == "c":
            value = self.c
        elif src_r8 == "d":
            value = self.d
        elif src_r8 == "e":
            value = self.e
        elif src_r8 == "h":
            value = self.h
        elif src_r8 == "l":
            value = self.l
        else:
            print(f"Invalid source r8 register code: {src_r8}")
            exit()

        if dest_r8 == "(hl)":
            addr: int = (self.h << 8) | self.l
            self.mmu.write_u8(addr, value)
        elif dest_r8 == "a":
            self.a = value & 0xFF
        elif dest_r8 == "b":
            self.b = value & 0xFF
        elif dest_r8 == "c":
            self.c = value & 0xFF
        elif dest_r8 == "d":
            self.d = value & 0xFF
        elif dest_r8 == "e":
            self.e = value & 0xFF
        elif dest_r8 == "h":
            self.h = value & 0xFF
        elif dest_r8 == "l":
            self.l = value & 0xFF
        else:
            print(f"Invalid destination r8 register code: {dest_r8}")
            exit()

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
            addr: int = (self.h << 8) | self.l
            value: int = self.mmu.read_u8(addr)
        elif r8 == "a":
            value = self.a
        elif r8 == "b":
            value = self.b
        elif r8 == "c":
            value = self.c
        elif r8 == "d":
            value = self.d
        elif r8 == "e":
            value = self.e
        elif r8 == "h":
            value = self.h
        elif r8 == "l":
            value = self.l
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        result: int = (self.a - value) & 0xFF
        self.a = result & 0xFF

        self.f = (
            (int(result == 0) << 7)
            | (1 << 6)
            | (int((result & 0x0F) < (value & 0x0F)) << 5)
            | (int(result < value) << 4)
        ) & 0xF0

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
            addr: int = (self.h << 8) | self.l
            value: int = self.mmu.read_u8(addr)
        elif r8 == "a":
            value = self.a
        elif r8 == "b":
            value = self.b
        elif r8 == "c":
            value = self.c
        elif r8 == "d":
            value = self.d
        elif r8 == "e":
            value = self.e
        elif r8 == "h":
            value = self.h
        elif r8 == "l":
            value = self.l
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        self.a = (self.a ^ value) & 0xFF

        self.f = ((int(self.a == 0) << 7) | (0 << 6) | (0 << 5) | (0 << 4)) & 0xF0
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
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)

        result: int = (self.a - imm8) & 0xFF

        self.f = (
            (int(result == 0) << 7)
            | (1 << 6)
            | (int((self.a & 0x0F) < (imm8 & 0x0F)) << 5)
            | (int(self.a < imm8) << 4)
        ) & 0xF0

        return 8

    # def _op_ret_cond(self, opcode: int) -> int:
    #     return 0

    def _op_ret(self, opcode: int) -> int:
        low: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF
        high: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF

        addr: int = (high << 8) | low
        self.pc = addr & 0xFFFF
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
        # inline get_advance_pc_u16
        self.pc = (self.pc + 1) & 0xFFFF
        lo: int = self.mmu.read_u8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        hi: int = self.mmu.read_u8(self.pc)
        imm16: int = lo | (hi << 8)

        # advance past opcode (original code called self.advance_pc())
        self.pc = (self.pc + 1) & 0xFFFF

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, self.pc >> 8 & 0xFF)
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, self.pc & 0xFF)

        self.pc = imm16 & 0xFFFF
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

        match r16stk:
            case "bc":
                self.b = (value >> 8) & 0xFF
                self.c = value & 0xFF
            case "de":
                self.d = (value >> 8) & 0xFF
                self.e = value & 0xFF
            case "hl":
                self.h = (value >> 8) & 0xFF
                self.l = value & 0xFF
            case "af":
                self.a = (value >> 8) & 0xFF
                self.f = value & 0xF0
            case _:
                print(f"Invalid r16stk register code: {r16stk}")
                exit()

        return 12

    def _op_push_r16stk(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        r16stk: str = ADDRESSES["r16stk"][src_reg]

        match r16stk:
            case "bc":
                value: int = (self.b << 8) | self.c
            case "de":
                value = (self.d << 8) | self.e
            case "hl":
                value = (self.h << 8) | self.l
            case "af":
                value = (self.a << 8) | self.f
            case _:
                print(f"Invalid r16stk register code: {r16stk}")
                exit()

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, (value >> 8) & 0xFF)
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, value & 0xFF)

        return 16

    def _op_PREFIX(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        opcode = self.mmu.read_u8(self.pc)
        return self.execute(opcode, prefix=True)

    def _op_ldh_p_c_a(self, opcode: int) -> int:
        addr: int = 0xFF00 + self.c

        self.mmu.write_u8(addr, self.a)

        return 8

    def _op_ldh_p_imm8_a(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)
        addr: int = 0xFF00 + imm8

        self.mmu.write_u8(addr, self.a)

        return 12

    def _op_ld_p_imm16_a(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        lo: int = self.mmu.read_u8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        hi: int = self.mmu.read_u8(self.pc)
        imm16: int = lo | (hi << 8)

        self.mmu.write_u8(imm16, self.a)

        return 16

    # def _op_ldh_a_p_c(self, opcode: int) -> int:
    #     return 0

    def _op_ldh_a_p_imm8(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)
        addr: int = 0xFF00 + imm8

        value: int = self.mmu.read_u8(addr)
        self.a = value & 0xFF

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
            addr: int = (self.h << 8) | self.l
            value: int = self.mmu.read_u8(addr)
        elif r8 == "a":
            value = self.a
        elif r8 == "b":
            value = self.b
        elif r8 == "c":
            value = self.c
        elif r8 == "d":
            value = self.d
        elif r8 == "e":
            value = self.e
        elif r8 == "h":
            value = self.h
        elif r8 == "l":
            value = self.l
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        carry: int = (value >> 7) & 1
        value = ((value << 1) | ((self.f >> 4) & 1)) & 0xFF

        if r8 == "(hl)":
            addr: int = (self.h << 8) | self.l
            self.mmu.write_u8(addr, value)
        elif r8 == "a":
            self.a = value & 0xFF
        elif r8 == "b":
            self.b = value & 0xFF
        elif r8 == "c":
            self.c = value & 0xFF
        elif r8 == "d":
            self.d = value & 0xFF
        elif r8 == "e":
            self.e = value & 0xFF
        elif r8 == "h":
            self.h = value & 0xFF
        elif r8 == "l":
            self.l = value & 0xFF
        else:
            print(f"Invalid destination r8 register code: {r8}")
            exit()

        self.f = ((0 << 7) | (0 << 6) | (0 << 5) | (carry << 4)) & 0xF0

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
            addr: int = (self.h << 8) | self.l
            value = self.mmu.read_u8(addr)
        elif r8 == "a":
            value = self.a
        elif r8 == "b":
            value = self.b
        elif r8 == "c":
            value = self.c
        elif r8 == "d":
            value = self.d
        elif r8 == "e":
            value = self.e
        elif r8 == "h":
            value = self.h
        elif r8 == "l":
            value = self.l
        else:
            print(f"Invalid r8 register code: {r8}")
            exit()

        self.f = (
            ((value & (1 << bit)) == 0) << 7 | (0 << 6) | (1 << 5) | (0 << 4)
        ) & 0xF0

        return 8

    # def res_b3_r8(self, opcode: int) -> int:
    #     return 0

    # def set_b3_r8(self, opcode: int) -> int:
    #     return 0

import numpy as np
from mmu import MMU
from typing import Callable

REG_B = 0
REG_C = 1
REG_D = 2
REG_E = 3
REG_H = 4
REG_L = 5
REG_F = 6
REG_A = 7


class CPU:
    def __init__(self, mmu: MMU) -> None:
        self.mmu: MMU = mmu
        self.pc: int = 0x0000
        self.sp: int = 0x0000
        self.u8_regs: np.ndarray = np.zeros(8, dtype=np.uint8)
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
            "01xxxyyy": self._op_bit_b_r8,
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
        self.pc = (self.pc + 1) & 0xFFFF
        lo: int = self.mmu.read_u8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        hi: int = self.mmu.read_u8(self.pc)
        imm16: int = lo | (hi << 8)

        match dest_reg:
            case 0:
                self.u8_regs[REG_B] = imm16 >> 8
                self.u8_regs[REG_C] = imm16 & 0xFF
            case 1:
                self.u8_regs[REG_D] = imm16 >> 8
                self.u8_regs[REG_E] = imm16 & 0xFF
            case 2:
                self.u8_regs[REG_H] = imm16 >> 8
                self.u8_regs[REG_L] = imm16 & 0xFF
            case 3:
                self.sp = imm16 & 0xFFFF
            case _:
                print(f"Invalid r16 register code: {dest_reg}")
                exit()

        return 12

    def _op_ld_p_r16mem_a(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11

        if src_reg == 0:
            addr: int = (int(self.u8_regs[REG_B]) << 8) | int(self.u8_regs[REG_C])
        elif src_reg == 1:
            addr: int = (int(self.u8_regs[REG_D]) << 8) | int(self.u8_regs[REG_E])
        elif src_reg == 2:
            addr = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            hl: int = (addr + 1) & 0xFFFF
            self.u8_regs[REG_H] = hl >> 8
            self.u8_regs[REG_L] = hl & 0xFF
        elif src_reg == 3:
            addr = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            hl = (addr - 1) & 0xFFFF
            self.u8_regs[REG_H] = hl >> 8
            self.u8_regs[REG_L] = hl & 0xFF
        else:
            print(f"Invalid r16mem register code: {src_reg}")
            exit()

        self.mmu.write_u8(addr, int(self.u8_regs[REG_A]))

        return 8

    def _op_ld_a_p_r16mem(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11

        if src_reg == 0:
            addr: int = (int(self.u8_regs[REG_B]) << 8) | int(self.u8_regs[REG_C])
        elif src_reg == 1:
            addr: int = (int(self.u8_regs[REG_D]) << 8) | int(self.u8_regs[REG_E])
        elif src_reg == 2:
            addr = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            hl: int = (addr + 1) & 0xFFFF
            self.u8_regs[REG_H] = hl >> 8
            self.u8_regs[REG_L] = hl & 0xFF
        elif src_reg == 3:
            addr = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            hl = (addr - 1) & 0xFFFF
            self.u8_regs[REG_H] = hl >> 8
            self.u8_regs[REG_L] = hl & 0xFF
        else:
            print(f"Invalid r16mem register code: {src_reg}")
            exit()

        value: int = self.mmu.read_u8(addr)
        self.u8_regs[REG_A] = value

        return 8

    # def _op_ld_p_imm16_sp(self, opcode: int) -> int:
    #     return 0

    def _op_inc_r16(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11

        match dest_reg:
            case 0:
                value: int = (
                    (int(self.u8_regs[REG_B]) << 8) | int(self.u8_regs[REG_C])
                ) + 1
                self.u8_regs[REG_B] = value >> 8
                self.u8_regs[REG_C] = value & 0xFF
            case 1:
                value: int = (
                    (int(self.u8_regs[REG_D]) << 8) | int(self.u8_regs[REG_E])
                ) + 1
                self.u8_regs[REG_D] = value >> 8
                self.u8_regs[REG_E] = value & 0xFF
            case 2:
                value: int = (
                    (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
                ) + 1
                self.u8_regs[REG_H] = value >> 8
                self.u8_regs[REG_L] = value & 0xFF
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
        mmu_read_u8 = self.mmu.read_u8
        mmu_write_u8 = self.mmu.write_u8
        value: int = 0
        original: int
        addr: int

        if dest_reg == 6:  # (hl)
            addr = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            original = mmu_read_u8(addr)
            value = original + 1
            mmu_write_u8(addr, value & 0xFF)
        elif dest_reg == 7:  # a
            original = self.u8_regs[REG_A]
            value = original + 1
            self.u8_regs[REG_A] = value
        elif dest_reg == 0:  # b
            original = self.u8_regs[REG_B]
            value = original + 1
            self.u8_regs[REG_B] = value
        elif dest_reg == 1:  # c
            original = self.u8_regs[REG_C]
            value = original + 1
            self.u8_regs[REG_C] = value
        elif dest_reg == 2:  # d
            original = self.u8_regs[REG_D]
            value = original + 1
            self.u8_regs[REG_D] = value
        elif dest_reg == 3:  # e
            original = self.u8_regs[REG_E]
            value = original + 1
            self.u8_regs[REG_E] = value
        elif dest_reg == 4:  # h
            original = self.u8_regs[REG_H]
            value = original + 1
            self.u8_regs[REG_H] = value
        elif dest_reg == 5:  # l
            original = self.u8_regs[REG_L]
            value = original + 1
            self.u8_regs[REG_L] = value
        else:
            print(f"Invalid r8 register code: {dest_reg}")
            exit()

        self.f = (
            (int(value == 0) << 7)
            | (0 << 6)
            | (int((original & 0x0F) == 0x0F) << 5)
            | (0 << 4)
        ) & 0xF0

        return 4

    def _op_dec_r8(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 3) & 0b111
        mmu_read_u8 = self.mmu.read_u8
        mmu_write_u8 = self.mmu.write_u8
        value: int = 0

        if dest_reg == 6:  # (hl)
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            original: int = mmu_read_u8(addr)
            value = original - 1
            mmu_write_u8(addr, value & 0xFF)
        elif dest_reg == 7:  # a
            original = int(self.u8_regs[REG_A])
            value = original - 1
            self.u8_regs[REG_A] = value & 0xFF
        elif dest_reg == 0:  # b
            original = int(self.u8_regs[REG_B])
            value = original - 1
            self.u8_regs[REG_B] = value & 0xFF
        elif dest_reg == 1:  # c
            original = int(self.u8_regs[REG_C])
            value = original - 1
            self.u8_regs[REG_C] = value & 0xFF
        elif dest_reg == 2:  # d
            original = int(self.u8_regs[REG_D])
            value = original - 1
            self.u8_regs[REG_D] = value & 0xFF
        elif dest_reg == 3:  # e
            original = int(self.u8_regs[REG_E])
            value = original - 1
            self.u8_regs[REG_E] = value & 0xFF
        elif dest_reg == 4:  # h
            original = int(self.u8_regs[REG_H])
            value = original - 1
            self.u8_regs[REG_H] = value & 0xFF
        elif dest_reg == 5:  # l
            original = int(self.u8_regs[REG_L])
            value = original - 1
            self.u8_regs[REG_L] = value & 0xFF
        else:
            print(f"Invalid r8 register code: {dest_reg}")
            exit()

        self.f = (
            (int(value == 0) << 7)
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
            self.u8_regs[REG_B] = imm8
        elif dest_reg == 1:
            self.u8_regs[REG_C] = imm8
        elif dest_reg == 2:
            self.u8_regs[REG_D] = imm8
        elif dest_reg == 3:
            self.u8_regs[REG_E] = imm8
        elif dest_reg == 4:
            self.u8_regs[REG_H] = imm8
        elif dest_reg == 5:
            self.u8_regs[REG_L] = imm8
        elif dest_reg == 7:
            self.u8_regs[REG_A] = imm8
        else:
            print(f"Invalid r8 register code: {dest_reg}")
            exit()

        return 8

    # def _op_rlca(self, opcode: int) -> int:
    #     return 0

    # def _op_rrca(self, opcode: int) -> int:
    #     return 0

    def _op_rla(self, opcode: int) -> int:
        carry: int = (int(self.u8_regs[REG_A]) >> 7) & 1
        self.u8_regs[REG_A] = (int(self.u8_regs[REG_A]) << 1) & 0xFF | (
            (self.f >> 4) & 1
        )

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
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.to_signed_u8(self.mmu.read_u8(self.pc))

        jump: int = (self.pc + imm8) & 0xFFFF

        cc: bool = False
        match cond_code:
            case 0:  # nz
                if (self.f & 0x80) == 0:
                    cc = True
            case 1:  # z
                if (self.f & 0x80) != 0:
                    cc = True
            case 2:  # nc
                if (self.f & 0x10) == 0:
                    cc = True
            case 3:  # c
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
        mmu_read_u8 = self.mmu.read_u8
        mmu_write_u8 = self.mmu.write_u8

        value: int = 0

        # source
        if src_reg == 6:  # (hl)
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            value: int = mmu_read_u8(addr)
        elif src_reg == 7:
            value = self.u8_regs[REG_A]
        elif src_reg == 0:
            value = self.u8_regs[REG_B]
        elif src_reg == 1:
            value = self.u8_regs[REG_C]
        elif src_reg == 2:
            value = self.u8_regs[REG_D]
        elif src_reg == 3:
            value = self.u8_regs[REG_E]
        elif src_reg == 4:
            value = self.u8_regs[REG_H]
        elif src_reg == 5:
            value = self.u8_regs[REG_L]
        else:
            print(f"Invalid source r8 register code: {src_reg}")
            exit()

        # destination
        if dest_reg == 6:  # (hl)
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            mmu_write_u8(addr, value)
        elif dest_reg == 7:
            self.u8_regs[REG_A] = value
        elif dest_reg == 0:
            self.u8_regs[REG_B] = value
        elif dest_reg == 1:
            self.u8_regs[REG_C] = value
        elif dest_reg == 2:
            self.u8_regs[REG_D] = value
        elif dest_reg == 3:
            self.u8_regs[REG_E] = value
        elif dest_reg == 4:
            self.u8_regs[REG_H] = value
        elif dest_reg == 5:
            self.u8_regs[REG_L] = value
        else:
            print(f"Invalid destination r8 register code: {dest_reg}")
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
        mmu_read_u8 = self.mmu.read_u8

        value: int = 0
        if src_reg == 6:
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            value: int = mmu_read_u8(addr)
        elif src_reg == 7:
            value = self.u8_regs[REG_A]
        elif src_reg == 0:
            value = self.u8_regs[REG_B]
        elif src_reg == 1:
            value = self.u8_regs[REG_C]
        elif src_reg == 2:
            value = self.u8_regs[REG_D]
        elif src_reg == 3:
            value = self.u8_regs[REG_E]
        elif src_reg == 4:
            value = self.u8_regs[REG_H]
        elif src_reg == 5:
            value = self.u8_regs[REG_L]
        else:
            print(f"Invalid r8 register code: {src_reg}")
            exit()

        result: int = self.u8_regs[REG_A] - value
        self.u8_regs[REG_A] = result

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
        mmu_read_u8 = self.mmu.read_u8

        value: int = 0

        if src_reg == 6:
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            value: int = mmu_read_u8(addr)
        elif src_reg == 7:
            value = self.u8_regs[REG_A]
        elif src_reg == 0:
            value = self.u8_regs[REG_B]
        elif src_reg == 1:
            value = self.u8_regs[REG_C]
        elif src_reg == 2:
            value = self.u8_regs[REG_D]
        elif src_reg == 3:
            value = self.u8_regs[REG_E]
        elif src_reg == 4:
            value = self.u8_regs[REG_H]
        elif src_reg == 5:
            value = self.u8_regs[REG_L]
        else:
            print(f"Invalid r8 register code: {src_reg}")
            exit()

        self.u8_regs[REG_A] = self.u8_regs[REG_A] ^ value

        self.f = (
            (int(self.u8_regs[REG_A] == 0) << 7) | (0 << 6) | (0 << 5) | (0 << 4)
        ) & 0xF0
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

        result: int = int(self.u8_regs[REG_A]) - imm8

        self.f = (
            (int(result == 0) << 7)
            | (1 << 6)
            | (int((self.u8_regs[REG_A] & 0x0F) < (imm8 & 0x0F)) << 5)
            | (int(self.u8_regs[REG_A] < imm8) << 4)
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

        # advance past opcode (original code called self.regs[REG_A]dvance_pc())
        self.pc = (self.pc + 1) & 0xFFFF

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, int(self.pc >> 8))
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, int(self.pc & 0xFF))

        self.pc = imm16 & 0xFFFF
        self.pc_jumped = True

        return 24

    # def _op_rst_tgt3(self, opcode: int) -> int:
    #     return 0

    def _op_pop_r16stk(self, opcode: int) -> int:
        dest_reg: int = (opcode >> 4) & 0b11
        low: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF
        high: int = self.mmu.read_u8(self.sp)
        self.sp = (self.sp + 1) & 0xFFFF

        value: int = (high << 8) | low

        if dest_reg == 0:  # bc
            self.u8_regs[REG_B] = (value >> 8) & 0xFF
            self.u8_regs[REG_C] = value & 0xFF
        elif dest_reg == 1:  # de
            self.u8_regs[REG_D] = (value >> 8) & 0xFF
            self.u8_regs[REG_E] = value & 0xFF
        elif dest_reg == 2:  # hl
            self.u8_regs[REG_H] = (value >> 8) & 0xFF
            self.u8_regs[REG_L] = value & 0xFF
        elif dest_reg == 3:  # af
            self.u8_regs[REG_A] = (value >> 8) & 0xFF
            self.f = value & 0xF0
        else:
            print(f"Invalid r16stk register code: {dest_reg}")
            exit()

        return 12

    def _op_push_r16stk(self, opcode: int) -> int:
        src_reg: int = (opcode >> 4) & 0b11
        if src_reg == 0:  # bc
            value: int = (int(self.u8_regs[REG_B]) << 8) | int(self.u8_regs[REG_C])
        elif src_reg == 1:  # de
            value = (int(self.u8_regs[REG_D]) << 8) | int(self.u8_regs[REG_E])
        elif src_reg == 2:  # hl
            value = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
        elif src_reg == 3:  # af
            value = (int(self.u8_regs[REG_A]) << 8) | self.f
        else:
            print(f"Invalid r16stk register code: {src_reg}")
            exit()

        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, int(value >> 8))
        self.sp = (self.sp - 1) & 0xFFFF
        self.mmu.write_u8(self.sp, int(value & 0xFF))

        return 16

    def _op_PREFIX(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        opcode = self.mmu.read_u8(self.pc)
        return self.execute(opcode, prefix=True)

    def _op_ldh_p_c_a(self, opcode: int) -> int:
        addr: int = 0xFF00 + int(self.u8_regs[REG_C])

        self.mmu.write_u8(addr, int(self.u8_regs[REG_A]))

        return 8

    def _op_ldh_p_imm8_a(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)
        addr: int = 0xFF00 + imm8

        self.mmu.write_u8(addr, int(self.u8_regs[REG_A]))

        return 12

    def _op_ld_p_imm16_a(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        lo: int = self.mmu.read_u8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        hi: int = self.mmu.read_u8(self.pc)
        imm16: int = lo | (hi << 8)

        self.mmu.write_u8(imm16, self.u8_regs[REG_A])

        return 16

    # def _op_ldh_a_p_c(self, opcode: int) -> int:
    #     return 0

    def _op_ldh_a_p_imm8(self, opcode: int) -> int:
        self.pc = (self.pc + 1) & 0xFFFF
        imm8: int = self.mmu.read_u8(self.pc)
        addr: int = 0xFF00 + imm8

        value: int = self.mmu.read_u8(addr)
        self.u8_regs[REG_A] = value

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
        mmu_read_u8 = self.mmu.read_u8
        mmu_write_u8 = self.mmu.write_u8

        value: int = 0

        if dest_reg == 6:
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            value: int = mmu_read_u8(addr)
        elif dest_reg == 7:
            value = self.u8_regs[REG_A]
        elif dest_reg == 0:
            value = self.u8_regs[REG_B]
        elif dest_reg == 1:
            value = self.u8_regs[REG_C]
        elif dest_reg == 2:
            value = self.u8_regs[REG_D]
        elif dest_reg == 3:
            value = self.u8_regs[REG_E]
        elif dest_reg == 4:
            value = self.u8_regs[REG_H]
        elif dest_reg == 5:
            value = self.u8_regs[REG_L]
        else:
            print(f"Invalid r8 register code: {dest_reg}")
            exit()

        carry: int = (int(value) >> 7) & 1
        value = (int(value) << 1) | ((self.f >> 4) & 1)

        if dest_reg == 6:
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            mmu_write_u8(addr, value & 0xFF)
        elif dest_reg == 7:
            self.u8_regs[REG_A] = value & 0xFF
        elif dest_reg == 0:
            self.u8_regs[REG_B] = value & 0xFF
        elif dest_reg == 1:
            self.u8_regs[REG_C] = value & 0xFF
        elif dest_reg == 2:
            self.u8_regs[REG_D] = value & 0xFF
        elif dest_reg == 3:
            self.u8_regs[REG_E] = value & 0xFF
        elif dest_reg == 4:
            self.u8_regs[REG_H] = value & 0xFF
        elif dest_reg == 5:
            self.u8_regs[REG_L] = value & 0xFF
        else:
            print(f"Invalid destination r8 register code: {dest_reg}")
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

    def _op_bit_b_r8(self, opcode: int) -> int:
        bit: int = (opcode >> 3) & 0b111
        src_reg: int = opcode & 0b111
        mmu_read_u8 = self.mmu.read_u8

        value: int = 0

        if src_reg == 6:
            addr: int = (int(self.u8_regs[REG_H]) << 8) | int(self.u8_regs[REG_L])
            value = mmu_read_u8(addr)
        elif src_reg == 7:
            value = self.u8_regs[REG_A]
        elif src_reg == 0:
            value = self.u8_regs[REG_B]
        elif src_reg == 1:
            value = self.u8_regs[REG_C]
        elif src_reg == 2:
            value = self.u8_regs[REG_D]
        elif src_reg == 3:
            value = self.u8_regs[REG_E]
        elif src_reg == 4:
            value = self.u8_regs[REG_H]
        elif src_reg == 5:
            value = self.u8_regs[REG_L]
        else:
            print(f"Invalid r8 register code: {src_reg}")
            exit()

        self.f = (
            ((value & (1 << bit)) == 0) << 7 | (0 << 6) | (1 << 5) | (0 << 4)
        ) & 0xF0

        return 8

    # def res_b3_r8(self, opcode: int) -> int:
    #     return 0

    # def set_b3_r8(self, opcode: int) -> int:
    #     return 0

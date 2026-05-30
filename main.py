import argparse

import logger
from mmu import MMU
from cpu import CPU
from ppu import PPU
from timer import Timer
from joypad import Joypad

log = logger.get("Emulator")


class Emulator:
    def __init__(self, rom_path: str, boot_rom_path: str) -> None:
        log.info("Loading ROM %s", rom_path)
        self.mmu: MMU = MMU(rom_path, boot_rom_path)
        self.cpu: CPU = CPU(self.mmu)
        self.ppu: PPU = PPU(self.mmu)
        self.timer: Timer = Timer(self.mmu)
        self.joypad: Joypad = Joypad(self.mmu)

    def step(self) -> None:
        cycles: int = self.cpu.step()
        if cycles == 0:
            log.error("CPU step returned 0 cycles, which is invalid")
            exit()
        self.ppu.step(cycles)
        self.timer.step(cycles)

    def run(self) -> None:
        log.info("Starting emulator loop")
        while True:
            self.step()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="WARNING")
    parser.add_argument("--log-cpu", default=None)
    parser.add_argument("--log-mmu", default=None)
    parser.add_argument("--log-ppu", default=None)
    parser.add_argument("--log-timer", default=None)
    parser.add_argument("--log-joypad", default=None)
    parser.add_argument("--log-rom", default=None)
    args = parser.parse_args()

    logger.setup(level=args.log)

    if args.log_cpu:
        logger.get("CPU").setLevel(args.log_cpu)
    if args.log_mmu:
        logger.get("MMU").setLevel(args.log_mmu)
    if args.log_ppu:
        logger.get("PPU").setLevel(args.log_ppu)
    if args.log_timer:
        logger.get("Timer").setLevel(args.log_timer)
    if args.log_joypad:
        logger.get("Joypad").setLevel(args.log_joypad)
    if args.log_rom:
        logger.get("ROM").setLevel(args.log_rom)

    emulator = Emulator("roms/Pokemon - Red Version.gb", "roms/boot/dmg_boot.bin")
    emulator.run()

import argparse
import warnings

warnings.filterwarnings("ignore", message=".*avx2.*")

import logger
import perf as perf_module

from emulator import Emulator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="WARNING")
    parser.add_argument("--log-from", default=None, metavar="ADDR")
    parser.add_argument("--log-cpu", default=None, metavar="LEVEL")
    parser.add_argument("--log-mmu", default=None, metavar="LEVEL")
    parser.add_argument("--log-ppu", default=None, metavar="LEVEL")
    parser.add_argument("--log-rom", default=None, metavar="LEVEL")
    parser.add_argument("--log-apu", default=None, metavar="LEVEL")
    parser.add_argument("--log-perf", action="store_true")
    args = parser.parse_args()

    logger.setup(level=args.log)

    if args.log_perf:
        perf_module.perf.enabled = True
        logger.set_component_level("PERF", "DEBUG")
    if args.log_cpu:
        logger.set_component_level("CPU", args.log_cpu)
    if args.log_mmu:
        logger.set_component_level("MMU", args.log_mmu)
    if args.log_ppu:
        logger.set_component_level("PPU", args.log_ppu)
    if args.log_rom:
        logger.set_component_level("ROM", args.log_rom)
    if args.log_apu:
        logger.set_component_level("APU", args.log_apu)

    log_from: int | None = int(args.log_from, 16) if args.log_from else None

    emulator = Emulator("roms/Tetris.gb", "roms/boot/dmg_boot.bin")
    # emulator = Emulator("roms/Pokemon - Red Version.gb", "roms/boot/dmg_boot.bin")
    emulator.cpu.log_from = log_from
    emulator.run()

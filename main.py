import argparse
import warnings

warnings.filterwarnings("ignore", message=".*avx2.*")

import perf as perf_module

from emulator import Emulator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--perf", action="store_true")
    args = parser.parse_args()

    if args.perf:
        perf_module.perf.enabled = True

    emulator = Emulator("roms/Tetris.gb", "roms/boot/dmg_boot.bin")
    # emulator = Emulator("roms/Pokemon - Red Version.gb", "roms/boot/dmg_boot.bin")
    emulator.run()


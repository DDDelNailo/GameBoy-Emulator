import threading
import numpy as np
import pygame

SAMPLE_RATE = 44100
GB_CLOCK = 4194304
CYCLES_PER_SAMPLE = GB_CLOCK / SAMPLE_RATE  # ~95.1
FRAME_SEQ_RATE = 512  # Hz
FRAME_SEQ_CYCLES = GB_CLOCK // FRAME_SEQ_RATE  # 8192 cycles per frame sequencer tick
BUFFER_FRAMES = 4  # how many frames to buffer ahead
SAMPLES_PER_FRAME = SAMPLE_RATE // 60


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

DUTY_PATTERNS = [
    [0, 0, 0, 0, 0, 0, 0, 1],  # 12.5%
    [1, 0, 0, 0, 0, 0, 0, 1],  # 25%
    [1, 0, 0, 0, 1, 1, 1, 1],  # 50%
    [0, 1, 1, 1, 1, 1, 1, 0],  # 75%
]


# ─────────────────────────────────────────────────────────────────────────────
# Channel 1 — Square wave with frequency sweep
# ─────────────────────────────────────────────────────────────────────────────


class Channel1:
    def __init__(self) -> None:
        self.enabled = False
        self.dac_enabled = False

        # registers
        self.nr10: int = 0x00  # sweep
        self.nr11: int = 0x00  # duty + length
        self.nr12: int = 0x00  # envelope
        self.nr13: int = 0x00  # freq lo
        self.nr14: int = 0x00  # freq hi + trigger

        # internal state
        self.duty_pos: int = 0
        self.freq_timer: int = 0
        self.length_timer: int = 0
        self.volume: int = 0
        self.env_timer: int = 0
        self.sweep_timer: int = 0
        self.sweep_freq: int = 0  # shadow frequency register
        self.output: int = 0

    @property
    def _freq_period(self) -> int:
        period = ((self.nr14 & 0x07) << 8) | self.nr13
        return (2048 - period) * 4

    def trigger(self) -> None:
        self.enabled = self.dac_enabled
        self.length_timer = (
            64 - (self.nr11 & 0x3F) if self.length_timer == 0 else self.length_timer
        )
        self.freq_timer = self._freq_period
        self.volume = (self.nr12 >> 4) & 0x0F
        self.env_timer = self.nr12 & 0x07
        self.sweep_freq = ((self.nr14 & 0x07) << 8) | self.nr13
        self.sweep_timer = (self.nr10 >> 4) & 0x07
        if self.sweep_timer == 0:
            self.sweep_timer = 8
        # if sweep shift > 0, check immediately
        if (self.nr10 & 0x07) and self._calc_sweep() > 2047:
            self.enabled = False

    def _calc_sweep(self) -> int:
        shift = self.nr10 & 0x07
        delta = self.sweep_freq >> shift
        if self.nr10 & 0x08:  # decrease
            return self.sweep_freq - delta
        return self.sweep_freq + delta

    def clock_sweep(self) -> None:
        if not self.enabled:
            return
        self.sweep_timer -= 1
        if self.sweep_timer <= 0:
            pace = (self.nr10 >> 4) & 0x07
            self.sweep_timer = pace if pace else 8
            if pace:
                new_freq = self._calc_sweep()
                if new_freq > 2047:
                    self.enabled = False
                elif self.nr10 & 0x07:
                    self.sweep_freq = new_freq
                    self.nr13 = new_freq & 0xFF
                    self.nr14 = (self.nr14 & 0xF8) | ((new_freq >> 8) & 0x07)
                    if self._calc_sweep() > 2047:
                        self.enabled = False

    def clock_length(self) -> None:
        if self.nr14 & 0x40:  # length enabled
            self.length_timer -= 1
            if self.length_timer <= 0:
                self.enabled = False

    def clock_envelope(self) -> None:
        pace = self.nr12 & 0x07
        if pace == 0:
            return
        self.env_timer -= 1
        if self.env_timer <= 0:
            self.env_timer = pace
            if self.nr12 & 0x08:  # increase
                if self.volume < 15:
                    self.volume += 1
            else:  # decrease
                if self.volume > 0:
                    self.volume -= 1

    def step(self, cycles: int) -> None:
        if not self.enabled:
            self.output = 0
            return
        self.freq_timer -= cycles
        while self.freq_timer <= 0:
            self.freq_timer += self._freq_period
            self.duty_pos = (self.duty_pos + 1) & 7
        duty = (self.nr11 >> 6) & 0x03
        self.output = self.volume if DUTY_PATTERNS[duty][self.duty_pos] else 0


# ─────────────────────────────────────────────────────────────────────────────
# Channel 2 — Square wave (no sweep)
# ─────────────────────────────────────────────────────────────────────────────


class Channel2:
    def __init__(self) -> None:
        self.enabled = False
        self.dac_enabled = False

        self.nr21: int = 0x00
        self.nr22: int = 0x00
        self.nr23: int = 0x00
        self.nr24: int = 0x00

        self.duty_pos: int = 0
        self.freq_timer: int = 0
        self.length_timer: int = 0
        self.volume: int = 0
        self.env_timer: int = 0
        self.output: int = 0

    @property
    def _freq_period(self) -> int:
        period = ((self.nr24 & 0x07) << 8) | self.nr23

        return (2048 - period) * 4

    def trigger(self) -> None:
        self.enabled = self.dac_enabled
        self.length_timer = (
            64 - (self.nr21 & 0x3F) if self.length_timer == 0 else self.length_timer
        )
        self.freq_timer = self._freq_period
        self.volume = (self.nr22 >> 4) & 0x0F
        self.env_timer = self.nr22 & 0x07

    def clock_length(self) -> None:
        if self.nr24 & 0x40:
            self.length_timer -= 1
            if self.length_timer <= 0:
                self.enabled = False

    def clock_envelope(self) -> None:
        pace = self.nr22 & 0x07
        if pace == 0:
            return
        self.env_timer -= 1
        if self.env_timer <= 0:
            self.env_timer = pace
            if self.nr22 & 0x08:
                if self.volume < 15:
                    self.volume += 1
            else:
                if self.volume > 0:
                    self.volume -= 1

    def step(self, cycles: int) -> None:
        if not self.enabled:
            self.output = 0
            return
        self.freq_timer -= cycles
        while self.freq_timer <= 0:
            self.freq_timer += self._freq_period
            self.duty_pos = (self.duty_pos + 1) & 7
        duty = (self.nr21 >> 6) & 0x03
        self.output = self.volume if DUTY_PATTERNS[duty][self.duty_pos] else 0


# ─────────────────────────────────────────────────────────────────────────────
# Channel 3 — Wave channel
# ─────────────────────────────────────────────────────────────────────────────

WAVE_VOLUME_SHIFTS = [4, 0, 1, 2]  # 0%, 100%, 50%, 25%


class Channel3:
    def __init__(self) -> None:
        self.enabled = False
        self.dac_enabled = False

        self.nr30: int = 0x00
        self.nr31: int = 0x00
        self.nr32: int = 0x00
        self.nr33: int = 0x00
        self.nr34: int = 0x00
        self.wave_ram: bytearray = bytearray(16)

        self.wave_pos: int = 0
        self.freq_timer: int = 0
        self.length_timer: int = 0
        self.output: int = 0

    @property
    def _freq_period(self) -> int:
        period = ((self.nr34 & 0x07) << 8) | self.nr33
        return (2048 - period) * 2

    def trigger(self) -> None:
        self.enabled = self.dac_enabled
        self.length_timer = (
            256 - self.nr31 if self.length_timer == 0 else self.length_timer
        )
        self.freq_timer = self._freq_period
        self.wave_pos = 0

    def clock_length(self) -> None:
        if self.nr34 & 0x40:
            self.length_timer -= 1
            if self.length_timer <= 0:
                self.enabled = False

    def step(self, cycles: int) -> None:
        if not self.enabled:
            self.output = 0
            return
        self.freq_timer -= cycles
        while self.freq_timer <= 0:
            self.freq_timer += self._freq_period
            self.wave_pos = (self.wave_pos + 1) & 31
        byte = self.wave_ram[self.wave_pos >> 1]
        nibble = (byte >> 4) if (self.wave_pos & 1) == 0 else (byte & 0x0F)
        vol_shift = WAVE_VOLUME_SHIFTS[(self.nr32 >> 5) & 0x03]
        self.output = nibble >> vol_shift


# ─────────────────────────────────────────────────────────────────────────────
# Channel 4 — Noise channel (LFSR)
# ─────────────────────────────────────────────────────────────────────────────

DIVISORS = [8, 16, 32, 48, 64, 80, 96, 112]


class Channel4:
    def __init__(self) -> None:
        self.enabled = False
        self.dac_enabled = False

        self.nr41: int = 0x00
        self.nr42: int = 0x00
        self.nr43: int = 0x00
        self.nr44: int = 0x00

        self.length_timer: int = 0
        self.volume: int = 0
        self.env_timer: int = 0
        self.freq_timer: int = 0
        self.lfsr: int = 0x7FFF
        self.output: int = 0

    @property
    def _freq_period(self) -> int:
        r = self.nr43 & 0x07
        s = (self.nr43 >> 4) & 0x0F
        return DIVISORS[r] << s

    def trigger(self) -> None:
        self.enabled = self.dac_enabled
        self.length_timer = (
            64 - (self.nr41 & 0x3F) if self.length_timer == 0 else self.length_timer
        )
        self.volume = (self.nr42 >> 4) & 0x0F
        self.env_timer = self.nr42 & 0x07
        self.freq_timer = self._freq_period
        self.lfsr = 0x7FFF

    def clock_length(self) -> None:
        if self.nr44 & 0x40:
            self.length_timer -= 1
            if self.length_timer <= 0:
                self.enabled = False

    def clock_envelope(self) -> None:
        pace = self.nr42 & 0x07
        if pace == 0:
            return
        self.env_timer -= 1
        if self.env_timer <= 0:
            self.env_timer = pace
            if self.nr42 & 0x08:
                if self.volume < 15:
                    self.volume += 1
            else:
                if self.volume > 0:
                    self.volume -= 1

    def step(self, cycles: int) -> None:
        if not self.enabled:
            self.output = 0
            return
        self.freq_timer -= cycles
        while self.freq_timer <= 0:
            self.freq_timer += self._freq_period
            bit = (self.lfsr ^ (self.lfsr >> 1)) & 1
            self.lfsr = (self.lfsr >> 1) | (bit << 14)
            if self.nr43 & 0x08:  # 7-bit mode
                self.lfsr = (self.lfsr & ~0x40) | (bit << 6)
        self.output = self.volume if not (self.lfsr & 1) else 0


# ─────────────────────────────────────────────────────────────────────────────
# APU
# ─────────────────────────────────────────────────────────────────────────────


class APU:
    def __init__(self) -> None:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(1)

        self.ch1 = Channel1()
        self.ch2 = Channel2()
        self.ch3 = Channel3()
        self.ch4 = Channel4()

        self.nr50: int = 0x00  # master volume
        self.nr51: int = 0x00  # panning
        self.nr52: int = 0x00  # APU enable

        self._cycle_accum: float = 0.0
        self._frame_seq_accum: int = 0
        self._frame_seq_step: int = 0

        self._sample_buffer: list[tuple[int, int]] = []
        self._lock = threading.Lock()

        # streaming: two pygame Sound buffers, swap between them
        self._stream_channel = pygame.mixer.Channel(0)

    # ── register read/write ───────────────────────────────────────────────────

    def write(self, addr: int, val: int) -> None:
        # APU enable gate — only NR52 and wave RAM are writable when off
        if not (self.nr52 & 0x80) and addr != 0xFF26 and not (0xFF30 <= addr <= 0xFF3F):
            return

        if addr == 0xFF10:
            self.ch1.nr10 = val
        elif addr == 0xFF11:
            self.ch1.nr11 = val
            self.ch1.length_timer = 64 - (val & 0x3F)
        elif addr == 0xFF12:
            self.ch1.nr12 = val
            self.ch1.dac_enabled = (val & 0xF8) != 0
            if not self.ch1.dac_enabled:
                self.ch1.enabled = False
        elif addr == 0xFF13:
            self.ch1.nr13 = val
        elif addr == 0xFF14:
            self.ch1.nr14 = val
            if val & 0x80:
                self.ch1.trigger()

        elif addr == 0xFF16:
            self.ch2.nr21 = val
            self.ch2.length_timer = 64 - (val & 0x3F)
        elif addr == 0xFF17:
            self.ch2.nr22 = val
            self.ch2.dac_enabled = (val & 0xF8) != 0
            if not self.ch2.dac_enabled:
                self.ch2.enabled = False
        elif addr == 0xFF18:
            self.ch2.nr23 = val
        elif addr == 0xFF19:
            self.ch2.nr24 = val
            if val & 0x80:
                self.ch2.trigger()

        elif addr == 0xFF1A:
            self.ch3.nr30 = val
            self.ch3.dac_enabled = bool(val & 0x80)
            if not self.ch3.dac_enabled:
                self.ch3.enabled = False
        elif addr == 0xFF1B:
            self.ch3.nr31 = val
            self.ch3.length_timer = 256 - val
        elif addr == 0xFF1C:
            self.ch3.nr32 = val
        elif addr == 0xFF1D:
            self.ch3.nr33 = val
        elif addr == 0xFF1E:
            self.ch3.nr34 = val
            if val & 0x80:
                self.ch3.trigger()

        elif addr == 0xFF20:
            self.ch4.nr41 = val
            self.ch4.length_timer = 64 - (val & 0x3F)
        elif addr == 0xFF21:
            self.ch4.nr42 = val
            self.ch4.dac_enabled = (val & 0xF8) != 0
            if not self.ch4.dac_enabled:
                self.ch4.enabled = False
        elif addr == 0xFF22:
            self.ch4.nr43 = val
        elif addr == 0xFF23:
            self.ch4.nr44 = val
            if val & 0x80:
                self.ch4.trigger()

        elif addr == 0xFF24:
            self.nr50 = val
        elif addr == 0xFF25:
            self.nr51 = val
        elif addr == 0xFF26:
            self.nr52 = val
            if not (val & 0x80):
                self._reset_all()

        elif 0xFF30 <= addr <= 0xFF3F:
            self.ch3.wave_ram[addr - 0xFF30] = val

    def read(self, addr: int) -> int:
        if addr == 0xFF10:
            return self.ch1.nr10 | 0x80
        elif addr == 0xFF11:
            return self.ch1.nr11 | 0x3F
        elif addr == 0xFF12:
            return self.ch1.nr12
        elif addr == 0xFF13:
            return 0xFF  # write-only
        elif addr == 0xFF14:
            return self.ch1.nr14 | 0xBF

        elif addr == 0xFF16:
            return self.ch2.nr21 | 0x3F
        elif addr == 0xFF17:
            return self.ch2.nr22
        elif addr == 0xFF18:
            return 0xFF
        elif addr == 0xFF19:
            return self.ch2.nr24 | 0xBF

        elif addr == 0xFF1A:
            return self.ch3.nr30 | 0x7F
        elif addr == 0xFF1B:
            return 0xFF
        elif addr == 0xFF1C:
            return self.ch3.nr32 | 0x9F
        elif addr == 0xFF1D:
            return 0xFF
        elif addr == 0xFF1E:
            return self.ch3.nr34 | 0xBF

        elif addr == 0xFF20:
            return 0xFF
        elif addr == 0xFF21:
            return self.ch4.nr42
        elif addr == 0xFF22:
            return self.ch4.nr43
        elif addr == 0xFF23:
            return self.ch4.nr44 | 0xBF

        elif addr == 0xFF24:
            return self.nr50
        elif addr == 0xFF25:
            return self.nr51
        elif addr == 0xFF26:
            val = self.nr52 & 0x80
            if self.ch1.enabled:
                val |= 0x01
            if self.ch2.enabled:
                val |= 0x02
            if self.ch3.enabled:
                val |= 0x04
            if self.ch4.enabled:
                val |= 0x08
            return val | 0x70

        elif 0xFF30 <= addr <= 0xFF3F:
            return self.ch3.wave_ram[addr - 0xFF30]

        return 0xFF

    # ── main step ─────────────────────────────────────────────────────────────

    def step(self, cycles: int) -> None:
        if not (self.nr52 & 0x80):
            return

        self._clock_frame_sequencer(cycles)

        self.ch1.step(cycles)
        self.ch2.step(cycles)
        self.ch3.step(cycles)
        self.ch4.step(cycles)

        self._cycle_accum += cycles
        while self._cycle_accum >= CYCLES_PER_SAMPLE:
            self._cycle_accum -= CYCLES_PER_SAMPLE
            self._push_sample()

    # ── frame sequencer ───────────────────────────────────────────────────────

    def _clock_frame_sequencer(self, cycles: int) -> None:
        self._frame_seq_accum += cycles
        while self._frame_seq_accum >= FRAME_SEQ_CYCLES:
            self._frame_seq_accum -= FRAME_SEQ_CYCLES
            step = self._frame_seq_step

            if step % 2 == 0:  # steps 0,2,4,6
                self.ch1.clock_length()
                self.ch2.clock_length()
                self.ch3.clock_length()
                self.ch4.clock_length()
            if step == 2 or step == 6:  # sweep
                self.ch1.clock_sweep()
            if step == 7:  # envelope
                self.ch1.clock_envelope()
                self.ch2.clock_envelope()
                self.ch4.clock_envelope()

            self._frame_seq_step = (step + 1) & 7

    # ── sample output ─────────────────────────────────────────────────────────

    def _push_sample(self) -> None:
        # mix channels (0-15 each, sum 0-60)
        mixed = self.ch1.output + self.ch2.output + self.ch3.output + self.ch4.output

        # master volume (0-7 per side from NR50)
        vol_l = ((self.nr50 >> 4) & 0x07) + 1
        vol_r = (self.nr50 & 0x07) + 1

        # panning from NR51
        l = int(mixed * vol_l) if (self.nr51 & 0xF0) else 0
        r = int(mixed * vol_r) if (self.nr51 & 0x0F) else 0

        # scale to int16 range
        scale = 32767 // (60 * 8)
        with self._lock:
            self._sample_buffer.append((l * scale, r * scale))

    def flush(self) -> None:
        """Call once per frame from the emulator to push buffered audio."""
        with self._lock:
            if not self._sample_buffer:
                return
            buf = self._sample_buffer[:]
            self._sample_buffer.clear()

        arr = np.array(buf, dtype=np.int16)
        sound = pygame.sndarray.make_sound(arr)

        # queue it — if channel is busy just queue, pygame handles it
        if not self._stream_channel.get_busy():
            self._stream_channel.play(sound)
        else:
            self._stream_channel.queue(sound)

    # ── APU reset ─────────────────────────────────────────────────────────────

    def _reset_all(self) -> None:
        for ch in (self.ch1, self.ch2, self.ch3, self.ch4):
            ch.enabled = False
        self.nr50 = self.nr51 = 0

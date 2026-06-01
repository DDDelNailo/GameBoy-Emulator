import time
import atexit


class PerfMonitor:
    def __init__(self) -> None:
        self.enabled = False

        # rolling stats
        self._timings: dict[str, float] = {}
        self._counts: dict[str, int] = {}
        self._frame_times: list[float] = []

        # lifetime stats
        self._total_timings: dict[str, float] = {}
        self._total_counts: dict[str, int] = {}
        self._all_frame_times: list[float] = []

        self._frame_start: float = 0.0
        self._report_every: int = 60

        atexit.register(self.report_lifetime)

    def frame_start(self) -> None:
        if not self.enabled:
            return

        self._frame_start = time.perf_counter()

    def frame_end(self) -> None:
        if not self.enabled:
            return

        dt = time.perf_counter() - self._frame_start

        self._frame_times.append(dt)
        self._all_frame_times.append(dt)

        if len(self._frame_times) >= self._report_every:
            self._report()
            self._frame_times.clear()
            self._timings.clear()
            self._counts.clear()

    def begin(self, name: str) -> float:
        if not self.enabled:
            return 0.0

        return time.perf_counter()

    def end(self, name: str, start: float) -> None:
        if not self.enabled:
            return

        elapsed = time.perf_counter() - start

        # rolling
        self._timings[name] = self._timings.get(name, 0.0) + elapsed
        self._counts[name] = self._counts.get(name, 0) + 1

        # lifetime
        self._total_timings[name] = self._total_timings.get(name, 0.0) + elapsed
        self._total_counts[name] = self._total_counts.get(name, 0) + 1

    def _report(self) -> None:
        self._print_report(
            "perf report",
            self._frame_times,
            self._timings,
            self._counts,
        )

    def report_lifetime(self) -> None:
        if not self.enabled:
            return

        if not self._all_frame_times:
            return

        self._print_report(
            "lifetime perf report",
            self._all_frame_times,
            self._total_timings,
            self._total_counts,
        )

    def _print_report(
        self,
        title: str,
        frame_times: list[float],
        timings: dict[str, float],
        counts: dict[str, int],
    ) -> None:
        n = len(frame_times)

        avg_ms = (sum(frame_times) / n) * 1000
        max_ms = max(frame_times) * 1000
        fps = 1.0 / (sum(frame_times) / n)

        print(f"── {title} ({n} frames) ──────────────────")
        print(f"  frame   avg={avg_ms:.2f} ms  max={max_ms:.2f} ms  fps={fps:.1f}")

        total = sum(timings.values()) or 1.0

        for name, elapsed in sorted(
            timings.items(),
            key=lambda x: -x[1],
        ):
            calls = counts[name]
            pct = (elapsed / total) * 100
            per_call = (elapsed / calls) * 1_000_000

            print(f"  {name:<12} {pct:5.1f}%  {per_call:6.1f} µs/call  ({calls} calls)")

        print("──────────────────────────────────────────────────")



class NullPerf:
    def frame_start(self) -> None:...
    def frame_end(self) -> None:...
    def begin(self, name: str) -> float:...
    def end(self, name: str, start: float) -> None:...

perf = PerfMonitor()
null_perf = NullPerf()
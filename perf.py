# perf.py
import time
import logger

log = logger.get("PERF")

class PerfMonitor:
    def __init__(self) -> None:
        self.enabled = False
        self._timings: dict[str, float] = {}
        self._counts:  dict[str, int]   = {}
        self._frame_times: list[float]  = []
        self._frame_start: float        = 0.0
        self._report_every: int         = 60   # frames

    def frame_start(self) -> None:
        if not self.enabled: return
        self._frame_start = time.perf_counter()

    def frame_end(self) -> None:
        if not self.enabled: return
        self._frame_times.append(time.perf_counter() - self._frame_start)
        if len(self._frame_times) >= self._report_every:
            self._report()
            self._frame_times.clear()
            self._timings.clear()
            self._counts.clear()

    def begin(self, name: str) -> float:
        if not self.enabled: return 0.0
        return time.perf_counter()

    def end(self, name: str, start: float) -> None:
        if not self.enabled: return
        elapsed = time.perf_counter() - start
        self._timings[name] = self._timings.get(name, 0.0) + elapsed
        self._counts[name]  = self._counts.get(name, 0) + 1

    def _report(self) -> None:
        n = len(self._frame_times)
        avg_ms  = (sum(self._frame_times) / n) * 1000
        max_ms  = max(self._frame_times) * 1000
        fps     = 1.0 / (sum(self._frame_times) / n)

        log.debug("── perf report (last %d frames) ──────────────────", n)
        log.debug("  frame   avg=%.2f ms  max=%.2f ms  fps=%.1f", avg_ms, max_ms, fps)

        total = sum(self._timings.values()) or 1.0
        for name, elapsed in sorted(self._timings.items(), key=lambda x: -x[1]):
            calls   = self._counts[name]
            pct     = (elapsed / total) * 100
            per_call = (elapsed / calls) * 1_000_000   # µs
            log.debug("  %-12s %5.1f%%  %6.1f µs/call  (%d calls)", name, pct, per_call, calls)

        log.debug("──────────────────────────────────────────────────")


perf = PerfMonitor()
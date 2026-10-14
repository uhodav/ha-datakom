"""Сглаживание уровня топлива.

Датчик уровня шумит (±1 %), а пока двигатель работает, показывает примерно на 4 % меньше
(вибрация, топливо в магистралях): при пуске значение сразу падает, при остановке - сразу
возвращается. Поэтому:

- в покое уровень - медиана показаний за последние REST_WINDOW секунд; меняется, только
  когда медиана ушла от него на HYSTERESIS и больше (заправка видна сразу, дрожание - нет);
- на ходу уровень - уровень в покое перед пуском минус то, насколько упали показания
  относительно своей «базы» этого запуска (медиана первых BASELINE секунд работы);
  сдвиг датчика при этом сокращается. На ходу уровень не растёт;
- первые SETTLE секунд после остановки остаётся последнее значение (показания возвращаются).
"""

from __future__ import annotations

from collections import deque
from statistics import median

WINDOW = 600
REST_WINDOW = 1800
BASELINE = 300
SETTLE = 120
HYSTERESIS = 1.0


class FuelLevelFilter:
    """Сглаженный уровень топлива, %."""

    def __init__(self) -> None:
        self._samples: deque[tuple[float, float]] = deque()
        self._last_key = None
        self.level: float | None = None
        self.running = False
        self.mode_since: float | None = None
        self.start_level: float | None = None
        self.baseline: float | None = None
        self.raw: float | None = None
        self.liters_per_percent: float | None = None

    def restore(self, level, attributes: dict) -> None:
        """Состояние после перезапуска Home Assistant."""
        try:
            self.level = float(level)
        except (TypeError, ValueError):
            self.level = None
        self.running = attributes.get("mode") == "running"
        for key in ("mode_since", "start_level", "baseline", "liters_per_percent"):
            value = attributes.get(key)
            setattr(self, key, float(value) if isinstance(value, (int, float)) else None)

    def attributes(self) -> dict:
        return {
            "mode": "running" if self.running else "rest",
            "raw": self.raw,
            "liters": self.liters,
            "liters_per_percent": self.liters_per_percent,
            "mode_since": self.mode_since,
            "start_level": self.start_level,
            "baseline": self.baseline,
        }

    @property
    def liters(self) -> float | None:
        if self.level is None or self.liters_per_percent is None:
            return None
        return round(self.level * self.liters_per_percent, 1)

    def _window(self, now: float, seconds: float, since: float | None = None) -> list[float]:
        start = now - seconds
        if since is not None:
            start = max(start, since)
        return [value for ts, value in self._samples if ts >= start]

    def update(self, now: float, raw: float | None, running: bool, raw_liters: float | None = None, key=None) -> None:
        """Новые показания. key - метка данных: повторный вызов с той же меткой ничего не делает."""
        if key is not None:
            if key == self._last_key:
                return
            self._last_key = key
        if raw_liters is not None and raw is not None and raw > 5:
            self.liters_per_percent = round(raw_liters / raw, 3)
        if raw is None:
            return
        self.raw = raw
        self._samples.append((now, raw))
        while self._samples and self._samples[0][0] < now - REST_WINDOW:
            self._samples.popleft()

        if running != self.running or self.mode_since is None:
            if running and not self.running:
                # Пуск: стартовый уровень - последний уровень в покое
                self.start_level = self.level if self.level is not None else raw
                self.baseline = None
            self.running = running
            self.mode_since = now

        if self.running:
            self._update_running(now)
        else:
            self._update_rest(now)

    def _update_running(self, now: float) -> None:
        if self.start_level is None:
            self.start_level = self.level if self.level is not None else self.raw
        if self.baseline is None:
            if now - self.mode_since < BASELINE:
                self.level = self.start_level
                return
            self.baseline = median(self._window(now, BASELINE, since=self.mode_since))
        current = median(self._window(now, WINDOW, since=self.mode_since))
        value = self.start_level - max(0.0, self.baseline - current)
        self.level = round(min(self.level, value) if self.level is not None else value, 1)

    def _update_rest(self, now: float) -> None:
        if self.level is not None and now - self.mode_since < SETTLE:
            return
        values = self._window(now, REST_WINDOW, since=self.mode_since + SETTLE if self.level is not None else None)
        if not values:
            return
        value = round(median(values), 1)
        # Датчик меняется ступенями ~0.6 %: соседние ступени не дёргают значение
        if self.level is None or abs(value - self.level) >= HYSTERESIS:
            self.level = value

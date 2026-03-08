"""Minimal subset of freezegun used in this repository's tests."""

from __future__ import annotations

import datetime as _dt
import time as _time


class _FrozenTime:
    def __init__(self, initial: float):
        self._current = initial
        self._original_time = None

    def __enter__(self):
        self._original_time = _time.time
        _time.time = lambda: self._current
        return self

    def __exit__(self, exc_type, exc, tb):
        _time.time = self._original_time

    def tick(self, delta: float | _dt.timedelta = 1.0):
        if isinstance(delta, _dt.timedelta):
            self._current += delta.total_seconds()
        else:
            self._current += float(delta)


def freeze_time(value=None):
    if value is None:
        initial = _time.time()
    elif isinstance(value, str):
        initial = _dt.datetime.fromisoformat(value.replace(" ", "T")).timestamp()
    elif isinstance(value, _dt.datetime):
        initial = value.timestamp()
    else:
        initial = float(value)
    return _FrozenTime(initial)

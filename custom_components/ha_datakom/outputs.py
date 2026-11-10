"""Виходи контролера (реле 1-8 і модулі розширення 9-40): функція і стан з /device/io.

Listener читає їх Modbus-запитами через зʼєднання контролера приблизно раз на хвилину (функції - раз на
10 хв), у телеметрії їх немає. Функції - як у Rainbow Plus («Crank», «Fuel», «Remote Control Out 1»...)."""
from __future__ import annotations

# Функції «Remote Control Out 1..16» у списку функцій виходу: користувацький вихід N = 80 + N - 1
REMOTE_CONTROL_OUT_FIRST = 80
STANDARD_OUTPUTS = 8
ALL_OUTPUTS = 40


def io_outputs(data: dict | None) -> list[dict]:
    return ((data or {}).get("io") or {}).get("outputs") or []


def output_info(data: dict | None, number: int) -> dict | None:
    return next((o for o in io_outputs(data) if o.get("output") == number), None)


def shown_outputs(data: dict | None) -> list[int]:
    """Реле контролера 1-8 завжди, виходи модулів розширення - лише налаштовані як Remote Control Out."""
    outputs = io_outputs(data)
    if not outputs:
        return []
    return [
        o["output"] for o in outputs
        if o["output"] <= STANDARD_OUTPUTS
        or REMOTE_CONTROL_OUT_FIRST <= o.get("function_index", -1) < REMOTE_CONTROL_OUT_FIRST + 16
    ]


def remote_control_outputs(data: dict | None, user_output: int) -> list[dict]:
    """Фізичні виходи, на які призначено «Remote Control Out N» (ними керує користувацький вихід N)."""
    index = REMOTE_CONTROL_OUT_FIRST + user_output - 1
    return [o for o in io_outputs(data) if o.get("function_index") == index]

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class RollResult:
    formula: str
    total: int
    rolls: list[int]


def roll(formula: str) -> RollResult:
    """
    v1 지원: NdM(+/-X)  ex) 2d6+3, 1d20-1
    """
    expr = formula.lower().replace(" ", "")
    # 파싱
    try:
        left, mod = (
            (expr.split("+", 1) + ["0"])[:2] if "+" in expr else (expr.split("-", 1) + ["0"])
        )
        sign = 1 if "+" in expr else (-1 if "-" in expr else 0)
        n, m = left.split("d")
        n, m = int(n), int(m)
        modifier = int(mod) * (1 if sign == 1 else (-1 if sign == -1 else 0))
    except Exception as e:
        raise ValueError(f"Invalid formula: {formula}") from e

    if n <= 0 or m <= 0:
        raise ValueError("N and M must be positive")

    rolls = [random.randint(1, m) for _ in range(n)]
    total = sum(rolls) + modifier
    return RollResult(formula=formula, total=total, rolls=rolls)

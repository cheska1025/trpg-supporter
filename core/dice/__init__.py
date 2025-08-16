from __future__ import annotations

import random
import re
from typing import Dict, List

__all__ = ["roll"]

# NdM(+/-K) 형태만 지원하는 최소 파서
_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)


class RollResult(dict):
    """dict처럼도, 속성처럼도 접근 가능한 결과 객체"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__dict__ = self  # r.total / r["total"] 모두 허용


def roll(formula: str) -> RollResult:
    """
    예:
      roll("2d6+3") -> {"formula":"2d6+3","total":13,"detail":[4,6],"rolls":[4,6],"crit":False,"fumble":False}
      roll("1d20")  -> 20/1에 대해 crit/fumble 플래그 설정
    """
    m = _DICE_RE.match(formula)
    if not m:
        raise ValueError(f"Invalid dice formula: {formula!r}")

    n = int(m.group(1))
    sides = int(m.group(2))
    mod = int(m.group(3).replace(" ", "")) if m.group(3) else 0

    detail: List[int] = [random.randint(1, sides) for _ in range(n)]
    total = sum(detail) + mod

    crit = False
    fumble = False
    if n == 1 and sides == 20:
        crit = (detail[0] == 20)
        fumble = (detail[0] == 1)

    # rolls = detail 별칭(같은 리스트 객체)로 노출
    return RollResult(
        formula=formula,
        total=total,
        detail=detail,
        rolls=detail,   # ← 테스트 호환을 위해 추가
        crit=crit,
        fumble=fumble,
    )
from __future__ import annotations

import random
import re
from typing import Any

__all__ = ["roll"]

# NdM(+/-K) 형태만 지원하는 최소 파서
_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)


class RollResult(dict[str, Any]):
    """dict처럼도, 속성처럼도 접근 가능한 결과 객체

    - 키/속성 동시 접근 지원: r["total"] 및 r.total 모두 가능
    - 기본 키 보장: formula, total, rolls
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # 테스트/타입 안정성을 위해 기본 키를 보장
        self.setdefault("formula", "")
        self.setdefault("total", 0)
        self.setdefault("rolls", [])

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        # 핵심 필드는 dict 키와 동기화
        if name in {"formula", "total", "rolls"}:
            self[name] = value
        # 기본 객체 속성 설정도 유지
        super().__setattr__(name, value)


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

    detail: list[int] = [random.randint(1, sides) for _ in range(n)]
    total = sum(detail) + mod

    crit = False
    fumble = False
    if n == 1 and sides == 20:
        crit = detail[0] == 20
        fumble = detail[0] == 1

    # rolls = detail 별칭(같은 리스트 객체)로 노출 (테스트 호환)
    return RollResult(
        formula=formula,
        total=total,
        detail=detail,
        rolls=detail,
        crit=crit,
        fumble=fumble,
    )

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.log import LogManager, append_markdown


def test_roll_simple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRPG_HOME", "/dev/null")
    lm = LogManager(session_id="S1")
    lm.append_system(event="dice", data={"actor": "Rogue", "formula": "1d20+5", "total": 17})
    out_md = lm.export("md")
    assert "# Session S1" in out_md


def test_roll_crit_and_fumble_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRPG_HOME", "/dev/null")
    lm = LogManager(session_id="S2")
    lm.append_system(event="dice", data={"actor": "Rogue", "formula": "1d20+5", "total": 25})
    lm.append_system(event="dice", data={"actor": "Rogue", "formula": "1d20+5", "total": 6})
    out_json = lm.export("json")
    data = json.loads(out_json)
    assert len(data) == 2


def test_roll_pool_and_modifier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRPG_HOME", "/dev/null")
    lm = LogManager(session_id="S3")
    lm.append_system(
        event="dice",
        data={
            "actor": "Mage",
            "formula": "4d6+2",
            "detail": {"dice": [4, 4, 3, 6], "mod": 2},
            "total": 19,
        },
    )
    assert "Mage" in lm.export("md")


def test_log_export_unsupported_format_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TRPG_HOME", str(tmp_path))
    lm = LogManager(session_id="S4")
    with pytest.raises(ValueError):
        lm.export("txt")  # type: ignore[arg-type]


def test_append_markdown(tmp_path: Path) -> None:
    p = tmp_path / "exports" / "demo.md"
    append_markdown(p, "# title")
    append_markdown(p, "line")
    assert p.exists()
    text = p.read_text(encoding="utf-8").splitlines()
    assert text == ["# title", "line"]

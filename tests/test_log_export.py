from __future__ import annotations

import json
from pathlib import Path

from core.log import SessionLog


def test_log_export_md_and_json(tmp_path: Path):
    log = SessionLog()
    log.add("system", "턴 시작")
    log.add("narrative", "용사는 던전에 들어섰다")

    md_path = tmp_path / "session.md"
    json_path = tmp_path / "session.json"

    log.export_md(str(md_path))
    log.export_json(str(json_path))

    # MD 파일 내용 점검
    md_text = md_path.read_text(encoding="utf-8")
    assert "system" in md_text and "턴 시작" in md_text
    assert "narrative" in md_text and "용사는 던전에 들어섰다" in md_text

    # JSON 파일 내용 점검
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 2
    assert {e["channel"] for e in data} == {"system", "narrative"}
    assert any("턴 시작" in e["text"] for e in data)
    assert any("용사는 던전에 들어섰다" in e["text"] for e in data)

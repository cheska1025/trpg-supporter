from core.log import LogManager
from core.log import append_markdown
import json

def test_append_and_export_md_json(tmp_path, monkeypatch):
    monkeypatch.setenv("TRPG_HOME", str(tmp_path))
    lm = LogManager(session_id="S1")

    lm.append_system(event="dice", data={"actor":"Rogue", "formula":"1d20+5", "total":17})
    lm.append_narrative(text="Goblin과의 전투 개시", scene="prologue")

    out_md = lm.export("md")
    out_json = lm.export("json")

    # 경로 또는 반환 텍스트 확인 (구현에 따라 choose)
    # 1) 경로 반환 구현일 경우:
    if hasattr(out_md, "endswith"):
        assert str(out_md).endswith(".md")
    else:
        assert "# Session S1" in out_md or "Goblin" in out_md

    if hasattr(out_json, "endswith"):
        assert str(out_json).endswith(".json")
        data = json.loads(open(out_json, encoding="utf-8").read())
        assert any(item.get("type") == "system" for item in data)
    else:
        data = json.loads(out_json)
        assert any(item.get("type") == "system" for item in data)

def test_append_markdown(tmp_path):
    p = tmp_path / "exports" / "demo.md"
    append_markdown(p, "# title")
    append_markdown(p, "line")
    assert p.exists()
    text = p.read_text(encoding="utf-8").splitlines()
    assert text == ["# title", "line"]
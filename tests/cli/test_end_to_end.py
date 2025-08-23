from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli


def test_session_roll_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    monkeypatch.setenv("TRPG_HOME", str(tmp_path))

    r = runner.invoke(cli, ["session", "new", "Demo"])
    assert r.exit_code == 0

    assert runner.invoke(cli, ["enc", "start"]).exit_code == 0
    assert runner.invoke(cli, ["init", "add", "Rogue", "18"]).exit_code == 0
    assert runner.invoke(cli, ["init", "add", "Goblin", "12"]).exit_code == 0

    r = runner.invoke(cli, ["roll", "1d20+5", "--as", "Rogue"])
    assert r.exit_code == 0

    assert runner.invoke(cli, ["log", "add", "전투 개시"]).exit_code == 0
    assert runner.invoke(cli, ["export", "md"]).exit_code == 0

    assert (tmp_path / "exports").exists()

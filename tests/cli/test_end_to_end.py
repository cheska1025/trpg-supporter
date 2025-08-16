from click.testing import CliRunner
from cli.main import cli  # pyproject: [tool.poetry.scripts] trpg = "cli.main:cli"

def test_session_roll_export(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("TRPG_HOME", str(tmp_path))

    # 1) 세션 생성
    r = runner.invoke(cli, ["session", "new", "Demo"])
    assert r.exit_code == 0

    # 2) 전투 & 이니시
    assert runner.invoke(cli, ["enc", "start"]).exit_code == 0
    assert runner.invoke(cli, ["init", "add", "Rogue", "18"]).exit_code == 0
    assert runner.invoke(cli, ["init", "add", "Goblin", "12"]).exit_code == 0

    # 3) 굴림
    r = runner.invoke(cli, ["roll", "1d20+5", "--as", "Rogue"])
    assert r.exit_code == 0

    # 4) 로그 추가 & 내보내기
    assert runner.invoke(cli, ["log", "add", "전투 개시"]).exit_code == 0
    assert runner.invoke(cli, ["export", "md"]).exit_code == 0

    # 산출물 확인
    assert (tmp_path / "exports").exists()
from pathlib import Path

from studyforge.cli import TerminalApp, build_parser, default_data_path
from studyforge.repository import JsonRepository
from studyforge.service import StudyForge


class ScriptedInput:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    def __call__(self, _prompt: str) -> str:
        return next(self.responses)


def test_cli_logs_session_and_exits(tmp_path) -> None:
    output: list[str] = []
    service = StudyForge(JsonRepository(tmp_path / "data.json"))
    app = TerminalApp(
        service,
        input_fn=ScriptedInput(["2", "Calculus", "45", "2026-09-14", "8"]),
        output=output.append,
    )
    app.run()
    assert service.total_minutes(subject="calculus") == 45
    assert any("Logged 45 minutes" in line for line in output)


def test_cli_quiz_records_result(tmp_path) -> None:
    output: list[str] = []
    service = StudyForge(JsonRepository(tmp_path / "data.json"))
    service.add_flashcard("Python", "Creator?", "Guido van Rossum")
    app = TerminalApp(
        service,
        input_fn=ScriptedInput(["6", "python", "guido van rossum", "8"]),
        output=output.append,
    )
    app.run()
    assert service.accuracy_by_subject() == {"Python": 100.0}
    assert any("Quiz complete: 1/1" in line for line in output)


def test_parser_accepts_custom_data_path() -> None:
    args = build_parser().parse_args(["--data", "custom.json"])
    assert args.data == Path("custom.json")


def test_default_data_path_honors_environment(monkeypatch) -> None:
    monkeypatch.setenv("STUDYFORGE_DATA", "/tmp/custom-studyforge.json")
    assert default_data_path() == Path("/tmp/custom-studyforge.json")


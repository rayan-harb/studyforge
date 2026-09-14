import json

import pytest

from studyforge.models import Flashcard, QuizAttempt, StudySession
from studyforge.repository import DataFormatError, JsonRepository, StudyData


def test_missing_file_loads_empty_data(tmp_path) -> None:
    data = JsonRepository(tmp_path / "missing.json").load()
    assert data.sessions == []
    assert data.flashcards == []
    assert data.attempts == []


def test_repository_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "studyforge.json"
    session = StudySession.create("Python", 50, "2026-09-14", session_id="s1")
    card = Flashcard.create("Python", "Immutable sequence?", "tuple", card_id="c1")
    attempt = QuizAttempt.create(
        "c1", "Python", True, attempted_at="2026-09-14T12:00:00+00:00"
    )
    repository = JsonRepository(path)
    repository.save(StudyData([session], [card], [attempt]))

    loaded = repository.load()
    assert loaded.sessions == [session]
    assert loaded.flashcards == [card]
    assert loaded.attempts == [attempt]
    assert json.loads(path.read_text())["schema_version"] == 1


def test_repository_rejects_malformed_json(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(DataFormatError, match="could not read valid"):
        JsonRepository(path).load()


def test_repository_rejects_unknown_schema(tmp_path) -> None:
    path = tmp_path / "future.json"
    path.write_text('{"schema_version": 99}', encoding="utf-8")
    with pytest.raises(DataFormatError, match="unsupported"):
        JsonRepository(path).load()


def test_save_leaves_no_temporary_file(tmp_path) -> None:
    path = tmp_path / "studyforge.json"
    JsonRepository(path).save(StudyData())
    assert [item.name for item in tmp_path.iterdir()] == ["studyforge.json"]


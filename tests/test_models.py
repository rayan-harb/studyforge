from datetime import date, datetime

import pytest

from studyforge.models import Flashcard, QuizAttempt, StudySession


def test_session_accepts_real_iso_date() -> None:
    session = StudySession.create("Calculus", 45, "2026-09-14", session_id="session-1")
    assert session.studied_on == date(2026, 9, 14)
    assert session.to_dict()["studied_on"] == "2026-09-14"


@pytest.mark.parametrize("value", ["2026-02-30", "14-09-2026", "", "tomorrow"])
def test_session_rejects_invalid_dates(value: str) -> None:
    with pytest.raises(ValueError, match="real calendar date"):
        StudySession.create("Calculus", 30, value)


@pytest.mark.parametrize("minutes", [0, -5, 1.5, True])
def test_session_rejects_invalid_minutes(minutes: object) -> None:
    with pytest.raises(ValueError, match="positive whole number"):
        StudySession.create("Physics", minutes, date.today())  # type: ignore[arg-type]


def test_flashcard_cleans_text_and_checks_answers_case_insensitively() -> None:
    card = Flashcard.create("  Linear   Algebra ", " Identity   matrix? ", "  I  ")
    assert card.subject == "Linear Algebra"
    assert card.question == "Identity matrix?"
    assert card.accepts(" i ")


def test_flashcard_round_trip() -> None:
    original = Flashcard.create("Chemistry", "Symbol for sodium?", "Na", card_id="card-1")
    assert Flashcard.from_dict(original.to_dict()) == original


def test_quiz_attempt_round_trip() -> None:
    timestamp = datetime.fromisoformat("2026-09-14T12:00:00+00:00")
    original = QuizAttempt.create("card-1", "Chemistry", True, attempted_at=timestamp)
    assert QuizAttempt.from_dict(original.to_dict()) == original


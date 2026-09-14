import random
from datetime import date, datetime

import pytest

from studyforge.models import QuizAttempt
from studyforge.repository import JsonRepository
from studyforge.service import StudyForge


@pytest.fixture
def app(tmp_path) -> StudyForge:
    return StudyForge(JsonRepository(tmp_path / "data.json"))


def test_additions_are_persisted(app) -> None:
    app.add_session("Algorithms", 40, "2026-09-10")
    app.add_flashcard("Algorithms", "Binary search complexity?", "O(log n)")
    reloaded = StudyForge(app.repository)
    assert reloaded.total_minutes() == 40
    assert len(reloaded.flashcards()) == 1


def test_subject_filter_is_case_insensitive(app) -> None:
    app.add_session("Linear Algebra", 25, "2026-09-10")
    app.add_session("linear algebra", 35, "2026-09-11")
    assert app.total_minutes(subject="LINEAR ALGEBRA") == 60
    assert app.subject_totals() == {"Linear Algebra": 60}


def test_date_range_is_inclusive(app) -> None:
    app.add_session("Physics", 10, "2026-09-01")
    app.add_session("Physics", 20, "2026-09-02")
    app.add_session("Physics", 30, "2026-09-03")
    assert app.total_minutes(start=date(2026, 9, 2), end=date(2026, 9, 3)) == 50


def test_invalid_date_range_is_rejected(app) -> None:
    with pytest.raises(ValueError, match="start date"):
        app.sessions(start=date(2026, 9, 3), end=date(2026, 9, 2))


def test_subject_totals_are_sorted_by_minutes(app) -> None:
    app.add_session("Writing", 20, "2026-09-01")
    app.add_session("Calculus", 60, "2026-09-01")
    assert list(app.subject_totals()) == ["Calculus", "Writing"]


def test_weekly_totals_include_empty_weeks(app) -> None:
    app.add_session("Design", 30, "2026-09-01")
    app.add_session("Design", 45, "2026-09-14")
    assert app.weekly_totals(3, today=date(2026, 9, 14)) == {
        "2026-08-31": 30,
        "2026-09-07": 0,
        "2026-09-14": 45,
    }


def test_quiz_order_can_be_reproduced(app) -> None:
    for number in range(5):
        app.add_flashcard("Python", f"Question {number}?", str(number))
    first = [card.id for card in app.quiz_cards(rng=random.Random(7))]
    second = [card.id for card in app.quiz_cards(rng=random.Random(7))]
    assert first == second
    assert first != [card.id for card in app.flashcards()]


def test_record_answer_updates_accuracy(app) -> None:
    card = app.add_flashcard("Databases", "Query language?", "SQL")
    assert app.record_answer(card, "sql") is True
    assert app.record_answer(card, "Python") is False
    assert app.accuracy_by_subject() == {"Databases": 50.0}


def test_low_accuracy_drives_recommendation(app) -> None:
    card = app.add_flashcard("Thermodynamics", "Unit of energy?", "joule")
    app.data.attempts.append(
        QuizAttempt.create(
            card.id,
            card.subject,
            False,
            attempted_at=datetime.fromisoformat("2026-09-14T10:00:00+00:00"),
        )
    )
    assert app.recommendation(today=date(2026, 9, 14)) == (
        "Review Thermodynamics: current quiz accuracy is 0.0%."
    )


def test_study_balance_drives_recommendation_without_quiz_history(app) -> None:
    app.add_session("Calculus", 120, "2026-09-14")
    app.add_flashcard("Programming", "Language used here?", "Python")
    assert app.recommendation(today=date(2026, 9, 14)) == (
        "Focus on Programming: only 0 minutes logged in the last 7 days."
    )


def test_empty_account_gets_onboarding_recommendation(app) -> None:
    assert "Add a study session" in app.recommendation(today=date(2026, 9, 14))


def test_remove_and_reset(app) -> None:
    session = app.add_session("Economics", 20, "2026-09-14")
    card = app.add_flashcard("Economics", "Opportunity cost?", "next best alternative")
    assert app.remove_session(session.id)
    assert app.remove_flashcard(card.id)
    assert not app.remove_flashcard("missing")
    app.add_session("Economics", 15, "2026-09-14")
    app.reset()
    assert app.total_minutes() == 0


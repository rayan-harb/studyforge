"""Application logic for study tracking, quizzes, analytics, and recommendations."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta

from .models import Flashcard, QuizAttempt, StudySession
from .repository import JsonRepository, StudyData


def _subject_key(subject: str) -> str:
    return " ".join(subject.split()).casefold()


class StudyForge:
    def __init__(self, repository: JsonRepository) -> None:
        self.repository = repository
        self.data = repository.load()

    def save(self) -> None:
        self.repository.save(self.data)

    def add_session(self, subject: str, minutes: int, studied_on: date | str) -> StudySession:
        session = StudySession.create(subject, minutes, studied_on)
        self.data.sessions.append(session)
        self.save()
        return session

    def remove_session(self, session_id: str) -> bool:
        before = len(self.data.sessions)
        self.data.sessions = [item for item in self.data.sessions if item.id != session_id]
        changed = len(self.data.sessions) != before
        if changed:
            self.save()
        return changed

    def add_flashcard(self, subject: str, question: str, answer: str) -> Flashcard:
        card = Flashcard.create(subject, question, answer)
        self.data.flashcards.append(card)
        self.save()
        return card

    def remove_flashcard(self, card_id: str) -> bool:
        before = len(self.data.flashcards)
        self.data.flashcards = [item for item in self.data.flashcards if item.id != card_id]
        changed = len(self.data.flashcards) != before
        if changed:
            self.save()
        return changed

    def sessions(
        self,
        *,
        subject: str | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[StudySession]:
        if start and end and start > end:
            raise ValueError("start date cannot be after end date")
        subject_key = _subject_key(subject) if subject else None
        matches = [
            item
            for item in self.data.sessions
            if (subject_key is None or _subject_key(item.subject) == subject_key)
            and (start is None or item.studied_on >= start)
            and (end is None or item.studied_on <= end)
        ]
        return sorted(matches, key=lambda item: (item.studied_on, item.subject.casefold()))

    def total_minutes(self, **filters: object) -> int:
        return sum(item.minutes for item in self.sessions(**filters))

    def subject_totals(
        self, *, start: date | None = None, end: date | None = None
    ) -> dict[str, int]:
        totals: dict[str, int] = defaultdict(int)
        display_names: dict[str, str] = {}
        for session in self.sessions(start=start, end=end):
            key = _subject_key(session.subject)
            display_names.setdefault(key, session.subject)
            totals[key] += session.minutes
        return {
            display_names[key]: minutes
            for key, minutes in sorted(totals.items(), key=lambda pair: (-pair[1], pair[0]))
        }

    def weekly_totals(self, weeks: int = 6, *, today: date | None = None) -> dict[str, int]:
        if weeks <= 0:
            raise ValueError("weeks must be positive")
        anchor = today or date.today()
        current_monday = anchor - timedelta(days=anchor.weekday())
        first_monday = current_monday - timedelta(weeks=weeks - 1)
        totals = {
            (first_monday + timedelta(weeks=offset)).isoformat(): 0 for offset in range(weeks)
        }
        for session in self.sessions(start=first_monday, end=anchor):
            monday = session.studied_on - timedelta(days=session.studied_on.weekday())
            totals[monday.isoformat()] += session.minutes
        return totals

    def flashcards(self, subject: str | None = None) -> list[Flashcard]:
        cards = self.data.flashcards
        if subject:
            key = _subject_key(subject)
            cards = [card for card in cards if _subject_key(card.subject) == key]
        return list(cards)

    def quiz_cards(
        self,
        subject: str | None = None,
        *,
        limit: int | None = None,
        rng: random.Random | None = None,
    ) -> list[Flashcard]:
        cards = self.flashcards(subject)
        (rng or random.SystemRandom()).shuffle(cards)
        return cards[:limit] if limit is not None else cards

    def record_answer(self, card: Flashcard, response: str) -> bool:
        correct = card.accepts(response)
        self.data.attempts.append(QuizAttempt.create(card.id, card.subject, correct))
        self.save()
        return correct

    def accuracy_by_subject(self) -> dict[str, float]:
        results: dict[str, list[bool]] = defaultdict(list)
        display_names: dict[str, str] = {}
        for attempt in self.data.attempts:
            key = _subject_key(attempt.subject)
            display_names.setdefault(key, attempt.subject)
            results[key].append(attempt.correct)
        return {
            display_names[key]: round(sum(values) / len(values) * 100, 1)
            for key, values in sorted(results.items())
        }

    def recommendation(self, *, today: date | None = None) -> str:
        """Recommend a subject using quiz accuracy first, then recent study balance."""
        accuracies = self.accuracy_by_subject()
        if accuracies:
            weakest, accuracy = min(accuracies.items(), key=lambda item: (item[1], item[0]))
            if accuracy < 80:
                return f"Review {weakest}: current quiz accuracy is {accuracy:.1f}%."

        anchor = today or date.today()
        recent = self.subject_totals(start=anchor - timedelta(days=6), end=anchor)
        known_subjects = self._known_subjects()
        if not known_subjects:
            return "Add a study session or flashcard to unlock a personalized recommendation."
        minutes_by_key = {_subject_key(name): minutes for name, minutes in recent.items()}
        recommended = min(
            known_subjects,
            key=lambda name: (minutes_by_key.get(_subject_key(name), 0), name.casefold()),
        )
        minutes = minutes_by_key.get(_subject_key(recommended), 0)
        return f"Focus on {recommended}: only {minutes} minutes logged in the last 7 days."

    def _known_subjects(self) -> list[str]:
        subjects: dict[str, str] = {}
        sources: Iterable[str] = (
            [item.subject for item in self.data.sessions]
            + [item.subject for item in self.data.flashcards]
        )
        for subject in sources:
            subjects.setdefault(_subject_key(subject), subject)
        return sorted(subjects.values(), key=str.casefold)

    def reset(self) -> None:
        self.data = StudyData()
        self.save()


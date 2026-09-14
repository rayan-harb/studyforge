"""Validated domain models used throughout StudyForge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any
from uuid import uuid4


def _clean_text(value: str, field_name: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("date must be a real calendar date in YYYY-MM-DD format") from exc


@dataclass(frozen=True, slots=True)
class StudySession:
    subject: str
    minutes: int
    studied_on: date
    id: str

    @classmethod
    def create(
        cls,
        subject: str,
        minutes: int,
        studied_on: date | str,
        *,
        session_id: str | None = None,
    ) -> StudySession:
        clean_subject = _clean_text(subject, "subject")
        if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes <= 0:
            raise ValueError("minutes must be a positive whole number")
        return cls(clean_subject, minutes, _parse_date(studied_on), session_id or uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["studied_on"] = self.studied_on.isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StudySession:
        return cls.create(
            str(payload["subject"]),
            payload["minutes"],
            payload["studied_on"],
            session_id=str(payload["id"]),
        )


@dataclass(frozen=True, slots=True)
class Flashcard:
    subject: str
    question: str
    answer: str
    id: str

    @classmethod
    def create(
        cls,
        subject: str,
        question: str,
        answer: str,
        *,
        card_id: str | None = None,
    ) -> Flashcard:
        return cls(
            _clean_text(subject, "subject"),
            _clean_text(question, "question"),
            _clean_text(answer, "answer"),
            card_id or uuid4().hex,
        )

    def accepts(self, response: str) -> bool:
        return " ".join(response.split()).casefold() == self.answer.casefold()

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Flashcard:
        return cls.create(
            str(payload["subject"]),
            str(payload["question"]),
            str(payload["answer"]),
            card_id=str(payload["id"]),
        )


@dataclass(frozen=True, slots=True)
class QuizAttempt:
    flashcard_id: str
    subject: str
    correct: bool
    attempted_at: datetime

    @classmethod
    def create(
        cls,
        flashcard_id: str,
        subject: str,
        correct: bool,
        *,
        attempted_at: datetime | str | None = None,
    ) -> QuizAttempt:
        if not flashcard_id:
            raise ValueError("flashcard_id cannot be empty")
        timestamp = attempted_at or datetime.now().astimezone()
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError as exc:
                raise ValueError("attempted_at must be an ISO-8601 timestamp") from exc
        return cls(flashcard_id, _clean_text(subject, "subject"), bool(correct), timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flashcard_id": self.flashcard_id,
            "subject": self.subject,
            "correct": self.correct,
            "attempted_at": self.attempted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> QuizAttempt:
        return cls.create(
            str(payload["flashcard_id"]),
            str(payload["subject"]),
            bool(payload["correct"]),
            attempted_at=str(payload["attempted_at"]),
        )


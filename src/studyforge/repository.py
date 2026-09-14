"""Atomic JSON persistence for StudyForge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile

from .models import Flashcard, QuizAttempt, StudySession

SCHEMA_VERSION = 1


class DataFormatError(RuntimeError):
    """Raised when a data file exists but cannot be safely loaded."""


@dataclass(slots=True)
class StudyData:
    sessions: list[StudySession] = field(default_factory=list)
    flashcards: list[Flashcard] = field(default_factory=list)
    attempts: list[QuizAttempt] = field(default_factory=list)


class JsonRepository:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> StudyData:
        if not self.path.exists():
            return StudyData()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != SCHEMA_VERSION:
                raise DataFormatError("unsupported StudyForge data version")
            return StudyData(
                sessions=[StudySession.from_dict(item) for item in payload["sessions"]],
                flashcards=[Flashcard.from_dict(item) for item in payload["flashcards"]],
                attempts=[QuizAttempt.from_dict(item) for item in payload.get("attempts", [])],
            )
        except DataFormatError:
            raise
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise DataFormatError(f"could not read valid StudyForge data from {self.path}") from exc

    def save(self, data: StudyData) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "sessions": [session.to_dict() for session in data.sessions],
            "flashcards": [card.to_dict() for card in data.flashcards],
            "attempts": [attempt.to_dict() for attempt in data.attempts],
        }
        serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.replace(self.path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()


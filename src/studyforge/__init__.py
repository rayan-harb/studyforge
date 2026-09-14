"""StudyForge: study sessions, flashcards, analytics, and recommendations."""

from .models import Flashcard, QuizAttempt, StudySession
from .repository import JsonRepository
from .service import StudyForge

__all__ = ["Flashcard", "JsonRepository", "QuizAttempt", "StudyForge", "StudySession"]
__version__ = "1.0.0"


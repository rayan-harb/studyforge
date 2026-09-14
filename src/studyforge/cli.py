"""Dependency-free interactive terminal interface for StudyForge."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from datetime import date
from pathlib import Path

from .repository import DataFormatError, JsonRepository
from .service import StudyForge

Input = Callable[[str], str]
Output = Callable[[str], None]


def default_data_path() -> Path:
    configured = os.environ.get("STUDYFORGE_DATA")
    return Path(configured) if configured else Path.cwd() / "data" / "studyforge.json"


def _ask_nonempty(prompt: str, input_fn: Input, output: Output) -> str:
    while True:
        value = input_fn(prompt).strip()
        if value:
            return value
        output("Please enter a value.")


def _ask_minutes(input_fn: Input, output: Output) -> int:
    while True:
        raw = input_fn("Minutes studied: ").strip()
        try:
            minutes = int(raw)
            if minutes <= 0:
                raise ValueError
            return minutes
        except ValueError:
            output("Enter a positive whole number.")


def _ask_date(input_fn: Input, output: Output) -> date:
    while True:
        raw = input_fn("Date (YYYY-MM-DD, blank for today): ").strip()
        if not raw:
            return date.today()
        try:
            return date.fromisoformat(raw)
        except ValueError:
            output("Enter a real calendar date in YYYY-MM-DD format.")


class TerminalApp:
    MENU = """
╭────────────────── STUDYFORGE ──────────────────╮
│  1  Dashboard       5  Browse flashcards       │
│  2  Log session     6  Start quiz              │
│  3  Session history 7  Personalized next step  │
│  4  Add flashcard   8  Exit                    │
╰─────────────────────────────────────────────────╯"""

    def __init__(
        self,
        service: StudyForge,
        *,
        input_fn: Input = input,
        output: Output = print,
    ) -> None:
        self.service = service
        self.input = input_fn
        self.output = output

    def run(self) -> None:
        self.output("Forge better study habits, one focused session at a time.")
        while True:
            self.output(self.MENU)
            choice = self.input("Choose 1–8: ").strip()
            actions = {
                "1": self.dashboard,
                "2": self.log_session,
                "3": self.session_history,
                "4": self.add_flashcard,
                "5": self.browse_flashcards,
                "6": self.quiz,
                "7": self.recommend,
            }
            if choice == "8":
                self.output("Progress saved. See you next session.")
                return
            action = actions.get(choice)
            if action:
                action()
            else:
                self.output("That option is not available. Choose a number from 1 to 8.")

    def dashboard(self) -> None:
        totals = self.service.subject_totals()
        total_minutes = sum(totals.values())
        self.output(f"\nTotal focused time: {total_minutes} minutes")
        if not totals:
            self.output("No sessions yet. Log your first focused block.")
        for subject, minutes in totals.items():
            self.output(f"  {subject:<24} {minutes:>5} min")
        accuracies = self.service.accuracy_by_subject()
        if accuracies:
            self.output("\nQuiz accuracy:")
            for subject, accuracy in accuracies.items():
                self.output(f"  {subject:<24} {accuracy:>5.1f}%")

    def log_session(self) -> None:
        subject = _ask_nonempty("Subject: ", self.input, self.output)
        minutes = _ask_minutes(self.input, self.output)
        studied_on = _ask_date(self.input, self.output)
        session = self.service.add_session(subject, minutes, studied_on)
        self.output(f"Logged {session.minutes} minutes of {session.subject}.")

    def session_history(self) -> None:
        subject = self.input("Filter by subject (blank for all): ").strip() or None
        sessions = self.service.sessions(subject=subject)
        if not sessions:
            self.output("No matching sessions.")
            return
        self.output("")
        for session in sessions:
            self.output(
                f"{session.studied_on.isoformat()}  {session.subject:<20} "
                f"{session.minutes:>4} min  [{session.id[:8]}]"
            )

    def add_flashcard(self) -> None:
        subject = _ask_nonempty("Subject: ", self.input, self.output)
        question = _ask_nonempty("Question: ", self.input, self.output)
        answer = _ask_nonempty("Answer: ", self.input, self.output)
        self.service.add_flashcard(subject, question, answer)
        self.output("Flashcard added.")

    def browse_flashcards(self) -> None:
        subject = self.input("Filter by subject (blank for all): ").strip() or None
        cards = self.service.flashcards(subject)
        if not cards:
            self.output("No matching flashcards.")
            return
        for index, card in enumerate(cards, start=1):
            self.output(f"\n{index}. [{card.subject}] {card.question}\n   → {card.answer}")

    def quiz(self) -> None:
        subject = self.input("Quiz subject (blank for all): ").strip() or None
        cards = self.service.quiz_cards(subject)
        if not cards:
            self.output("No matching flashcards. Add one first.")
            return
        correct = 0
        for index, card in enumerate(cards, start=1):
            response = self.input(f"\n{index}/{len(cards)}  {card.question}\n> ")
            if self.service.record_answer(card, response):
                correct += 1
                self.output("Correct.")
            else:
                self.output(f"Not quite. Answer: {card.answer}")
        percentage = correct / len(cards) * 100
        self.output(f"\nQuiz complete: {correct}/{len(cards)} ({percentage:.0f}%).")

    def recommend(self) -> None:
        self.output(f"\n{self.service.recommendation()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Study sessions, flashcards, and useful analytics."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=default_data_path(),
        help="path to the JSON data file (default: ./data/studyforge.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        app = TerminalApp(StudyForge(JsonRepository(args.data)))
    except DataFormatError as exc:
        print(f"StudyForge could not start: {exc}")
        return 2
    try:
        app.run()
    except (EOFError, KeyboardInterrupt):
        print("\nProgress saved. See you next session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

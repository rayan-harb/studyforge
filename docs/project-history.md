# Project history

StudyForge began as an individual programming project completed for MSE 121 at the University of Waterloo. The original terminal application included study-session logging, time calculations, subject and date filters, persistent flashcards, quizzes, and plain-text storage. Its original automated suite contained 19 passing tests.

This repository is a separate portfolio edition. It does not reproduce the private GitHub Classroom repository, course instructions, classroom configuration, or academic-integrity templates.

## Evolution into the portfolio edition

| Original implementation | Portfolio edition |
|---|---|
| Procedural terminal menus | Small CLI class over a reusable service layer |
| Delimiter-based text files | Versioned, structured JSON |
| Direct file replacement | Atomic save through a temporary file |
| Superficial date-format checks | Real calendar validation with `datetime` |
| Case-sensitive subject filters | Whitespace-normalized, case-insensitive matching |
| Flashcard questions in insertion order | Randomized quiz order |
| Correct/incorrect result shown once | Persistent attempts and accuracy by subject |
| Total-time calculations | Subject totals, date filters, and weekly trends |
| No prioritization rule | Explainable study recommendation |
| Course-specific documentation | Standalone product and architecture documentation |

The product idea and core user workflow remain the same; the implementation was reorganized and extended to demonstrate maintainability, data design, automated testing, and technical communication.


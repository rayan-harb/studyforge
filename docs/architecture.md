# Architecture

StudyForge separates input/output, application behavior, domain rules, and persistence so each concern can evolve independently.

## Components

| Component | Responsibility |
|---|---|
| `cli.py` | Prompts, terminal formatting, argument parsing, and graceful exit behavior |
| `service.py` | Session and flashcard operations, aggregations, quiz recording, and recommendations |
| `models.py` | Validated immutable domain objects and JSON conversion |
| `repository.py` | Versioned JSON loading and atomic persistence |

The CLI depends on the service, and the service depends on a repository. Tests can therefore use a temporary repository and exercise the real application behavior without writing to a user's files.

## Data model

The persisted document is intentionally readable and versioned:

```json
{
  "schema_version": 1,
  "sessions": [
    {
      "subject": "Calculus",
      "minutes": 45,
      "studied_on": "2026-09-14",
      "id": "unique-session-id"
    }
  ],
  "flashcards": [],
  "attempts": []
}
```

Dates use ISO 8601. Session and flashcard IDs allow precise deletion without relying on list positions or duplicated text.

## Persistence safety

Saving does not overwrite the active data file in place. The repository writes and flushes a temporary file in the same directory, then atomically replaces the destination. If writing fails early, the previous file remains intact.

Malformed JSON, invalid records, and unknown schema versions stop the application with a clear error rather than silently discarding data.

## Recommendation rule

The current recommender is deterministic and explainable:

1. If any subject has quiz accuracy below 80%, recommend the lowest-accuracy subject.
2. Otherwise, recommend the known subject with the fewest minutes over the last seven days.
3. If there is no activity, explain how to unlock the recommendation.

This is intentionally a transparent heuristic, not a claim of machine learning or artificial intelligence.


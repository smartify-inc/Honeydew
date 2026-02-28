# Python Tools

The `tools/kanban_tools.py` module provides a Python interface for agents and scripts to interact with the HoneyDew API. It wraps the REST API with typed methods, config-aware profile handling, and convenience shortcuts.

---

## Setup

```python
from kanban_tools import KanbanTools, Priority

kanban = KanbanTools()
```

The constructor accepts an optional `base_url` (default: `http://localhost:8000`). Override via the `SMARTIFY_API_URL` environment variable or pass it directly:

```python
kanban = KanbanTools(base_url="http://192.168.1.50:8000")
```

`KanbanTools` supports context manager usage:

```python
with KanbanTools() as kanban:
    board = kanban.get_board(1)
```

---

## Configuration

Profile IDs, display names, and board definitions are loaded from `config.json` at the project root (or the path set in `SMARTIFY_CONFIG`). These drive default behavior:

- `create_card()` defaults to the **user** profile.
- `create_task()` defaults to the **agent** profile.
- `assign_to_user()` and `assign_to_agent()` use the configured profile IDs.
- `transfer_card()` validates against the configured profiles.

---

## Priority Enum

```python
class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
```

Use `Priority` values when creating or updating cards:

```python
card = kanban.create_task(title="Fix bug", priority=Priority.URGENT)
kanban.set_priority(card["id"], Priority.LOW)
```

---

## Board Operations

### `list_boards() -> list[dict]`

List all available boards.

### `get_board(board_id, profile=None) -> dict`

Get a board with all columns and cards. Pass `profile` to filter cards by profile ID.

### `create_board(name) -> dict`

Create a new board with default columns (To Do, In Progress, Done).

### `delete_board(board_id) -> None`

Delete a board and all its columns and cards.

---

## Column Operations

### `create_column(board_id, name, position=None) -> dict`

Create a new column in a board. Appends to end if `position` is omitted.

### `update_column(column_id, name=None, position=None) -> dict`

Update a column's name or position.

### `delete_column(column_id) -> None`

Delete a column and all its cards.

---

## Card Operations

### `list_cards(board_id=None, column_id=None, priority=None, has_due_date=None) -> list[dict]`

List cards with optional filters.

### `get_card(card_id) -> dict`

Get a card's details including labels.

### `create_card(column_id, title, description=None, priority=Priority.MEDIUM, due_date=None, profile=None) -> dict`

Create a new card in the specified column. Defaults to the **user** profile from config.

### `update_card(card_id, title=None, description=None, priority=None, due_date=None, *, agent_tokens_used=None, agent_model=None, agent_execution_time_seconds=None, agent_started_at=None, agent_completed_at=None) -> dict`

Update an existing card. Only provided fields are changed. The keyword-only `agent_*` parameters let you attach completion metadata (see [Agent Completion Metadata](#agent-completion-metadata)).

### `move_card(card_id, column_id, position=0) -> dict`

Move a card to a different column and/or position.

### `delete_card(card_id) -> None`

Delete a card.

---

## Transfer & Handoff

### `transfer_card(card_id, target_profile) -> dict`

Transfer a card to a different profile. Validates against configured profiles.

### `assign_to_user(card_id) -> dict`

Transfer a card to the human user profile (from config).

### `assign_to_agent(card_id) -> dict`

Transfer a card to the AI agent profile (from config).

---

## Movement Helpers

### `get_column_by_name(board_id, name) -> dict | None`

Find a column by name within a board (case-insensitive).

### `move_card_to_column(card_id, board_id, column_name) -> dict`

Move a card to a column by name. Raises `ValueError` if the column is not found.

### `move_card_to_board(card_id, board_id, column_name=None) -> dict`

Move a card to another board. The API resolves the target column: explicit `column_name` if provided, else match by current column name, else first column.

---

## Status Shortcuts

These move a card to a well-known column by name. All accept `board_id` (default: `1`).

### `mark_todo(card_id, board_id=1) -> dict`

Move a card to the "To Do" column.

### `mark_in_progress(card_id, board_id=1) -> dict`

Move a card to the "In Progress" column.

### `mark_blocked(card_id, board_id=1) -> dict`

Move a card to the "Blocked" column.

### `mark_done(card_id, board_id=1, *, agent_tokens_used=None, agent_model=None, agent_execution_time_seconds=None, agent_started_at=None, agent_completed_at=None) -> dict`

Move a card to the "Done" column. If any `agent_*` keyword arguments are provided, the card is also PATCHed with agent completion metadata.

---

## Label Operations

### `list_labels() -> list[dict]`

List all available labels.

### `create_label(name, color="#6366f1") -> dict`

Create a new label with an optional hex color.

### `add_label_to_card(card_id, label_id) -> dict`

Add a label to a card.

### `remove_label_from_card(card_id, label_id) -> None`

Remove a label from a card.

---

## Convenience Methods

### `create_task(title, description=None, priority=Priority.MEDIUM, due_date=None, board_id=None, profile=None) -> dict`

Quick task creation. Places the card in the first column of the specified board (or first board if omitted). Defaults to the **agent** profile — designed for agents creating their own work items.

### `get_board_summary(board_id=1) -> dict`

Returns a summary with card counts per column:

```python
{
    "id": 1,
    "name": "My Board",
    "total_cards": 12,
    "columns": {
        "To Do": 4,
        "In Progress": 3,
        "Done": 5
    }
}
```

### `get_overdue_cards(board_id=1) -> list[dict]`

Get all cards with due dates in the past, excluding cards in the Done column.

### `get_urgent_cards(board_id=1) -> list[dict]`

Get all HIGH and URGENT priority cards, excluding Done. Sorted by priority descending.

### `get_cards_in_column(column_name, board_id=1) -> list[dict]`

Get all cards in a specific column by name.

### `set_priority(card_id, priority) -> dict`

Update a card's priority level.

### `set_due_date(card_id, due_date) -> dict`

Update a card's due date.

---

## Complete Example

```python
from kanban_tools import KanbanTools, Priority
from datetime import date, timedelta

with KanbanTools() as kanban:
    # Agent creates a task for itself
    card = kanban.create_task(
        title="Refactor auth module",
        description="Extract middleware, add unit tests",
        priority=Priority.HIGH,
        due_date=date.today() + timedelta(days=3),
    )
    print(f"Created card #{card['id']}: {card['title']}")

    # Move to In Progress
    kanban.mark_in_progress(card["id"])

    # Done — hand it to the human for review
    kanban.mark_done(card["id"])
    kanban.assign_to_user(card["id"])

    # Check the board
    summary = kanban.get_board_summary()
    print(f"Board: {summary['name']} — {summary['total_cards']} cards")
    for col, count in summary["columns"].items():
        print(f"  {col}: {count}")

    # Check for overdue work
    overdue = kanban.get_overdue_cards()
    if overdue:
        print(f"\n{len(overdue)} overdue card(s)!")
        for c in overdue:
            print(f"  - {c['title']} (due: {c['due_date']})")
```

---

## Comments

### `add_comment(card_id, body, profile=None) -> dict`

Add a comment to a card. Defaults to the agent profile from config if `profile` is not provided.

```python
kanban.add_comment(card["id"], "Finished the first pass, needs review.")
```

### `get_comments(card_id) -> list[dict]`

List all comments on a card, ordered by creation time.

---

## Agent Completion Metadata

When an agent completes a task, it can report metadata (tokens used, model, execution time, timestamps) that HoneyDew displays in the task detail UI. Pass these as keyword-only arguments to `update_card` or `mark_done`:

```python
kanban.mark_done(
    card["id"],
    agent_tokens_used=4200,
    agent_model="gpt-4o",
    agent_execution_time_seconds=12.8,
    agent_started_at="2026-02-22T10:30:00Z",
    agent_completed_at="2026-02-22T10:30:12Z",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_tokens_used` | `int` | Total tokens consumed. |
| `agent_model` | `str` | Model identifier (e.g. `gpt-4o`). |
| `agent_execution_time_seconds` | `float` | Wall-clock time in seconds. |
| `agent_started_at` | `str` | ISO 8601 datetime (e.g. `2026-02-22T10:30:00Z`). |
| `agent_completed_at` | `str` | ISO 8601 datetime. |

All fields are optional. Only fields that are provided are stored and displayed.

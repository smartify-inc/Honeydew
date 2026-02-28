# For Agents

This page is a condensed reference for AI agents interacting with HoneyDew. You can drop this content into a system prompt or attach it as context.

---

## When to Use

Use the HoneyDew API when the user asks you to:

- Create, update, move, or delete tasks (cards)
- List boards, columns, or cards
- Transfer cards between user and agent profiles
- Manage labels (create, assign, remove)
- Check board summaries, overdue cards, or urgent items
- Move cards across boards

---

## Tracking Tasks

The user can open the HoneyDew board in their browser (`http://localhost:5173`) to see all tasks, their status, and what work you have completed. Encourage the user to check the board regularly for updates.

## Assigning Work to the User

When you need something from the user — a review, approval, input, or any manual step — create a task (or transfer an existing one) to the user's profile so it appears on their board. Let the user know you have assigned them a task and they should check HoneyDew.

---

## Connection

| Property | Value |
|----------|-------|
| Base URL | `http://localhost:8000` (override with env `SMARTIFY_API_URL`) |
| Auth | None — no API key required |
| Health check | `GET /health` → `{"status": "healthy"}` |

If the API is unreachable, ask the user to start HoneyDew: `./start.sh` in the project root.

---

## Priority Values

| Value | Name |
|-------|------|
| 1 | Low |
| 2 | Medium (default) |
| 3 | High |
| 4 | Urgent |

---

## API Quick Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/config | Get user/agent profile configuration |
| GET | /api/boards | List all boards |
| POST | /api/boards | Create a board (optional `columns` array) |
| GET | /api/boards/{id} | Get board with columns and cards (optional `?profile=` filter) |
| DELETE | /api/boards/{id} | Delete a board |
| POST | /api/columns | Create a column (`board_id`, `name`) |
| PATCH | /api/columns/{id} | Update column name or position |
| DELETE | /api/columns/{id} | Delete a column |
| GET | /api/cards | List cards (filters: `board_id`, `column_id`, `profile`, `priority`, `has_due_date`) |
| POST | /api/cards | Create a card (`column_id`, `title`, `priority`, `profile`, optional `description`, `due_date`) |
| GET | /api/cards/{id} | Get card details |
| PATCH | /api/cards/{id} | Update card fields |
| DELETE | /api/cards/{id} | Delete a card |
| POST | /api/cards/{id}/move | Move card (`column_id`, `position`) |
| POST | /api/cards/{id}/move-to-board | Move card to another board (`board_id`, optional `column_name`) |
| POST | /api/cards/{id}/transfer | Transfer card to another profile (`target_profile`) |
| GET | /api/labels | List all labels |
| POST | /api/labels | Create a label (`name`, `color`) |
| POST | /api/cards/{id}/labels/{label_id} | Add label to card |
| DELETE | /api/cards/{id}/labels/{label_id} | Remove label from card |
| GET | /api/cards/{id}/comments | List comments on a card |
| POST | /api/cards/{id}/comments | Add a comment (`body`, optional `profile`) |

---

## Task Comments

Both users and agents can add comments to any task. Comments appear in the task detail view in the UI. **Always add a comment when:**

- **You are blocked**: Explain specifically what you need from the user (e.g. "Need API credentials for the staging environment before I can proceed").
- **You complete a task**: Leave a brief summary of what you did and any decisions you made (e.g. "Refactored auth module into middleware, added 12 unit tests, all passing").
- **You need review or input**: Describe what to look at and any open questions.
- **You hand off work**: Note the current state so the next person (user or agent) has context.

```bash
curl -X POST http://localhost:8000/api/cards/3/comments \
  -H "Content-Type: application/json" \
  -d '{"body": "Finished the first pass, needs review.", "profile": "jarvis"}'
```

---

## Examples

### Create a task

```bash
curl -X POST http://localhost:8000/api/cards \
  -H "Content-Type: application/json" \
  -d '{"column_id": 1, "title": "Write docs", "priority": 2, "profile": "jarvis"}'
```

### Get the board to find column IDs

```bash
curl http://localhost:8000/api/boards/1
```

### Move a card to "In Progress"

```bash
curl -X POST http://localhost:8000/api/cards/3/move \
  -H "Content-Type: application/json" \
  -d '{"column_id": 2, "position": 0}'
```

### Move a card to another board

```bash
curl -X POST http://localhost:8000/api/cards/3/move-to-board \
  -H "Content-Type: application/json" \
  -d '{"board_id": 2, "column_name": "To Do"}'
```

### Transfer a card to the user

```bash
curl -X POST http://localhost:8000/api/cards/3/transfer \
  -H "Content-Type: application/json" \
  -d '{"target_profile": "tony"}'
```

### Create a label and attach it

```bash
# Create label
curl -X POST http://localhost:8000/api/labels \
  -H "Content-Type: application/json" \
  -d '{"name": "frontend", "color": "#06b6d4"}'

# Attach label (id 1) to card (id 3)
curl -X POST http://localhost:8000/api/cards/3/labels/1
```

---

## Python Tools (optional)

If you have access to the HoneyDew repo, `tools/kanban_tools.py` provides convenience methods:

```python
from kanban_tools import KanbanTools, Priority

kanban = KanbanTools()
card = kanban.create_task(title="Write docs", priority=Priority.HIGH)
kanban.move_card_to_column(card["id"], board_id=1, column_name="In Progress")
kanban.assign_to_user(card["id"])
kanban.mark_done(card["id"])
```

Key methods: `create_task`, `assign_to_user`, `assign_to_agent`, `move_card_to_column`, `move_card_to_board`, `mark_todo`, `mark_in_progress`, `mark_blocked`, `mark_done`, `get_board_summary`, `get_overdue_cards`, `get_urgent_cards`.

See [Python Tools](python-tools.md) for the full reference.

---

## Agent Completion Metadata

When you complete a task, you can report completion metadata so the user sees it in HoneyDew. Send any of these optional fields with `PATCH /api/cards/{id}`:

| Field | Type | Description |
|-------|------|-------------|
| `agent_tokens_used` | int | Total tokens consumed. |
| `agent_model` | string | Model name (e.g. `gpt-4o`). |
| `agent_execution_time_seconds` | float | Wall-clock execution time. |
| `agent_started_at` | string | ISO 8601 datetime when work started. |
| `agent_completed_at` | string | ISO 8601 datetime when work finished. |

Example — mark done and report metadata:

```bash
# Move to Done
curl -X POST http://localhost:8000/api/cards/5/move \
  -H "Content-Type: application/json" \
  -d '{"column_id": 3, "position": 0}'

# Attach completion metadata
curl -X PATCH http://localhost:8000/api/cards/5 \
  -H "Content-Type: application/json" \
  -d '{
    "agent_tokens_used": 4200,
    "agent_model": "gpt-4o",
    "agent_execution_time_seconds": 12.8,
    "agent_started_at": "2026-02-22T10:30:00Z",
    "agent_completed_at": "2026-02-22T10:30:12Z"
  }'
```

With Python tools:

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

These fields are optional and only displayed on the task when provided.

# Configuration

HoneyDew is configured through a `config.json` file at the project root. It defines who you are, who your agent is, and what boards to create on first run.

---

## Where Config Lives

| Item | Location |
|------|----------|
| Config file | `config.json` (project root) |
| Template | `config.example.json` |
| Env override | `SMARTIFY_CONFIG` — set to an absolute path to use a different config file |

If `config.json` is missing, HoneyDew falls back to `config.example.json` in the project root. The `install.sh` script creates `config.json` interactively (prompting for names) if it doesn't exist. The `start.sh` script copies the example to `config.json` on first run so you always have an editable config.

### Validating Your Config

Run the validation check without starting any servers:

```bash
./start.sh --validate-config
```

This verifies that the active config file (either `config.json` or `config.example.json`) is valid JSON with all required fields. Exit code `0` means valid, `1` means invalid.

---

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user.profile_id` | string | Yes | Profile ID for the human user. Used in the API and database. |
| `user.display_name` | string | Yes | Display name shown in the UI header and profile switcher. |
| `agent.profile_id` | string | Yes | Profile ID for the AI agent. Used in the API and database. |
| `agent.display_name` | string | Yes | Display name shown in the UI header and profile switcher. |
| `boards` | array | No | Board definitions. Each entry has `name` (string) and `columns` (array of column name strings; order = position). |

### Board defaults

If `boards` is omitted or empty, **no boards are created** at startup. You can add boards later via the API (`POST /api/boards`) or by adding entries to `config.json` and restarting.

!!! tip
    The `install.sh` script creates a `config.json` with two boards (one for you, one for your agent) when run for the first time, so most users start with boards already configured.

---

## Config Examples

### Minimal — profiles and one board

The simplest useful config defines both profiles and a single board.

```json
{
  "user": {
    "profile_id": "dylan",
    "display_name": "Dylan"
  },
  "agent": {
    "profile_id": "jarvis",
    "display_name": "Jarvis"
  },
  "boards": [
    {
      "name": "Dylan & Jarvis's Board",
      "columns": ["To Do", "In Progress", "Done"]
    }
  ]
}
```

If you omit `boards`, no boards will be created on startup — you would need to create them via the API.

### One board with custom columns

Add a `Blocked` column or rename columns to match your workflow.

```json
{
  "user": {
    "profile_id": "dylan",
    "display_name": "Dylan"
  },
  "agent": {
    "profile_id": "jarvis",
    "display_name": "Jarvis"
  },
  "boards": [
    {
      "name": "Dylan & Jarvis's Board",
      "columns": ["To Do", "In Progress", "Done", "Blocked"]
    }
  ]
}
```

### Multiple boards

Use separate boards for different workstreams or ownership.

```json
{
  "user": {
    "profile_id": "tony",
    "display_name": "Tony"
  },
  "agent": {
    "profile_id": "jarvis",
    "display_name": "Jarvis"
  },
  "boards": [
    {
      "name": "Tony's Board",
      "columns": ["To Do", "In Progress", "Done", "Blocked"]
    },
    {
      "name": "Jarvis's Board",
      "columns": ["To Do", "In Progress", "Done", "Blocked"]
    }
  ]
}
```

### Backlog workflow

Add a separate backlog board alongside your main board.

```json
{
  "user": {
    "profile_id": "alex",
    "display_name": "Alex"
  },
  "agent": {
    "profile_id": "claw",
    "display_name": "Claw"
  },
  "boards": [
    {
      "name": "Sprint Board",
      "columns": ["To Do", "In Progress", "Review", "Done"]
    },
    {
      "name": "Backlog",
      "columns": ["Ideas", "Groomed", "Ready"]
    }
  ]
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SMARTIFY_CONFIG` | `./config.json` | Override the path to the config file. |
| `SMARTIFY_API_URL` | `http://localhost:8000` | Base URL for the API (used by the Python tools module and agents). |
| `SMARTIFY_DOCS_URL` | `http://localhost:8001` | URL (host:port) for the documentation site when running `./start.sh --docs`. Override to bind to a different address (e.g. `http://0.0.0.0:8001`). |

---

## Moving Cards Between Boards

When you move a card to another board (via the UI **Move to board** action or `POST /api/cards/{id}/move-to-board`), the target column is resolved as follows:

1. If you pass a `column_name` that exists on the target board, that column is used.
2. Otherwise, the card's current column name is matched on the target board (case-insensitive).
3. If no match is found, the first column of the target board is used.

This means boards with the same column names (e.g. both have "In Progress") will preserve a card's status when moving between them.

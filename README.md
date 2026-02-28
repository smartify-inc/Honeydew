# HoneyDew by Smartify

<p align="center">
  <img src="docs/assets/honeydew-logo-2.png" alt="HoneyDew logo" width="400" />
</p>

**Your shared task board with your AI assistant.**

HoneyDew turns a one-off chat into an ongoing working relationship. It's a live Kanban workspace where you and your AI agent collaborate on real work — assigning tasks, tracking progress, reviewing outputs, and closing the loop, together.

> Built for [OpenClaw](https://docs.openclaw.ai) users. Works with any agent via the REST API.

---

## Why HoneyDew

Most AI interactions are ephemeral — you ask, it answers, the context vanishes. HoneyDew gives your agent a persistent workspace alongside you, so nothing gets lost and nothing goes unfinished.

- **A shared source of truth.** Both you and your agent read and write the same board. No more copy-pasting outputs into a tracker you maintain alone.
- **Work while you sleep** With a simple board check on each heartbeat, your agent will work on its todo list while you're out of office.
- **Real handoffs.** Assign a card to your agent, let it work, then have it hand the result back to you (or ask you for help!) — with full history on the card.
- **Works the way you think.** Kanban columns (To Do → In Progress → Done), priority levels, due dates, labels, and multi-board support. It's a simple task board, but one your agent actually uses.
- **Zero friction to start.** Two shell commands, no cloud account, no API key. Runs entirely on localhost.
- **Open API, open tools.** A full REST API, a Python tools module, and an OpenClaw skill — wire it up however you work.

---

## How It Works

Here's a typical flow once everything is running:

1. **You assign a task.** Open the board, create a card — "Refactor the auth module, add tests" — and assign it to your agent. You can also instruct your agent to assign itself tasks!
2. **Your agent picks it up.** Via OpenClaw (or any agent with API access), it reads the board, moves the card to In Progress, and gets to work.
3. **It posts its output.** When done, the agent updates the card description with results and moves it to Done (or flags it as Blocked if it hit a snag).
4. **You review and iterate.** You see the result right on the card, leave a note, reassign if needed, or close it out.
5. **Bonus! Your agent independently checks for new tasks** Simply instruct your agent to check HoneyDew for incomplete tasks and feel free to step away!

That's the loop. Assign → Work → Review → Done.

---

## Screenshot

> Run `./start.sh` and open `http://localhost:5173` to see the board live.

---

## Get Started

### 1. Clone

```bash
git clone https://github.com/smartify-inc/Honeydew.git honeydew
cd honeydew
```

### 2. Install

```bash
./install.sh
```

Installs backend and frontend dependencies. If `config.json` doesn't exist, the installer prompts for your name and your agent's name and creates `config.json` with two boards. If it already exists, prompts are skipped.

Edit `config.json` to further customize profiles, boards, and columns:

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
    { "name": "Tony's Board", "columns": ["To Do", "In Progress", "Done", "Blocked"] },
    { "name": "Jarvis's Board", "columns": ["To Do", "In Progress", "Done", "Blocked"] }
  ]
}
```

You can validate your config without starting the servers: `./start.sh --validate-config`.

### 3. Start

```bash
./start.sh
```

Launches both servers. Open the board at **`http://localhost:5173`** — the API is at **`http://localhost:8000`**.

---

## Connect Your Agent

### Option A — OpenClaw Skill (recommended)

If you use [OpenClaw](https://docs.openclaw.ai), install the HoneyDew skill from ClawHub:

```bash
clawhub install honeydew
```

Your agent will immediately know how to create, move, transfer, and manage cards on your board. Ask it anything:

- _"Create a high-priority task: 'Deploy v2'."_
- _"Show me all overdue cards."_
- _"Move the 'Fix login bug' card to In Progress."_
- _"Mark everything in Done as closed and give me a summary."_

See [`skills/honeydew/README.md`](skills/honeydew/README.md) for details.

### Option B — Share the Skill Context Directly

Using a different agent? Share [`skills/honeydew/SKILL.md`](skills/honeydew/SKILL.md) directly as context. It contains everything your agent needs: the full API reference, endpoint list, priority values, and example calls. Drop it into your system prompt or attach it as a file — your agent will know what to do.

### Option C — Python Tools Module

For scripted or more structured integrations, `tools/kanban_tools.py` provides a higher-level Python interface:

```python
from kanban_tools import KanbanTools, Priority

kanban = KanbanTools()

# Agent picks up a task
card = kanban.create_task(title="Refactor auth module", priority=Priority.HIGH)
kanban.move_card_to_column(card["id"], board_id=1, column_name="In Progress")

# Agent hands it back to you for review
kanban.assign_to_user(card["id"])

# You close it out
kanban.mark_done(card["id"])
```

**Available methods:**

| Category | Methods |
|----------|---------|
| Boards | `list_boards()`, `get_board(id)`, `create_board(name)`, `delete_board(id)` |
| Columns | `create_column(board_id, name)`, `update_column(id, ...)`, `delete_column(id)` |
| Cards | `list_cards(...)`, `get_card(id)`, `create_card(...)`, `update_card(id, ...)`, `delete_card(id)` |
| Movement | `move_card(id, column_id)`, `move_card_to_column(id, board_id, name)`, `move_card_to_board(id, board_id)` |
| Handoffs | `assign_to_user(id)`, `assign_to_agent(id)`, `transfer_card(id, profile)` |
| Status | `mark_todo(id)`, `mark_in_progress(id)`, `mark_blocked(id)`, `mark_done(id)` |
| Labels | `list_labels()`, `create_label(name, color)`, `add_label_to_card(card_id, label_id)` |
| Shortcuts | `create_task(title, ...)`, `get_board_summary()`, `get_overdue_cards()`, `get_urgent_cards()` |

---

## REST API

All endpoints are prefixed with `/api`. No authentication required (local use).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Get application configuration |
| GET | `/api/boards` | List all boards |
| POST | `/api/boards` | Create a board |
| GET | `/api/boards/{id}` | Get board with columns and cards |
| DELETE | `/api/boards/{id}` | Delete a board |
| POST | `/api/columns` | Create a column |
| PATCH | `/api/columns/{id}` | Update column |
| DELETE | `/api/columns/{id}` | Delete a column |
| GET | `/api/cards` | List cards (filters: `board_id`, `column_id`, `priority`) |
| POST | `/api/cards` | Create a card |
| GET | `/api/cards/{id}` | Get card details |
| PATCH | `/api/cards/{id}` | Update card |
| DELETE | `/api/cards/{id}` | Delete a card |
| POST | `/api/cards/{id}/move` | Move card to column/position |
| POST | `/api/cards/{id}/move-to-board` | Move card to another board |
| POST | `/api/cards/{id}/transfer` | Transfer card to another profile |
| GET | `/api/labels` | List all labels |
| POST | `/api/labels` | Create a label |
| POST | `/api/cards/{id}/labels/{label_id}` | Add label to card |
| DELETE | `/api/cards/{id}/labels/{label_id}` | Remove label from card |

---

## Configuration

Profiles and boards are configured in `config.json` at the project root. The `install.sh` script creates it from `config.example.json` — edit it to match your setup.

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
    { "name": "Tony's Board", "columns": ["To Do", "In Progress", "Done", "Blocked"] },
    { "name": "Jarvis's Board", "columns": ["To Do", "In Progress", "Done", "Blocked"] }
  ]
}
```

| Field | Purpose |
|-------|---------|
| `user.profile_id` | Profile ID for the human user (used in the API and database) |
| `user.display_name` | Display name shown in the UI |
| `agent.profile_id` | Profile ID for the AI agent |
| `agent.display_name` | Display name shown in the UI |
| `boards` | Optional. Array of board definitions with `name` and `columns`. Defaults to one board with To Do / In Progress / Done. |

Override the config path with `SMARTIFY_CONFIG`. Override the API base URL for agents with `SMARTIFY_API_URL`.

---

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

---

## Project Structure

```
honeydew/
├── config.json              # Your local config (gitignored)
├── config.example.json      # Template
├── install.sh               # One-time setup
├── start.sh                 # Launch backend + frontend
├── backend/                 # FastAPI app (Python)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routers/
│   ├── tests/
│   └── requirements.txt
├── frontend/                # React + TypeScript UI
│   └── src/
├── tools/
│   └── kanban_tools.py      # Python agent tools
└── skills/
    └── honeydew/            # OpenClaw skill (publishable to ClawHub)
```

**Stack:** FastAPI · SQLAlchemy 2.0 · SQLite · React 18 · TypeScript · Vite · Tailwind CSS · @dnd-kit

---

## Security

HoneyDew is designed for **local and trusted-network use**. There is no built-in authentication — anyone who can reach the API can read and modify all data.

- Do not expose the API to the public internet without adding your own auth layer.
- CORS is restricted to `localhost:5173` by default.
- `config.json` and the SQLite database (`backend/kanban.db`) are gitignored and stay local.

---

## Documentation

The docs are published at **[https://honeydocs.smartify.ai](https://honeydocs.smartify.ai)** (built from `main` via GitHub Actions).

HoneyDew has a full documentation site built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). The easiest way to serve it locally is alongside the app:

```bash
./start.sh --docs
```

This launches the docs site at `http://localhost:8001` alongside the backend and frontend. Dependencies are installed automatically on first run. Override the docs URL with the `SMARTIFY_DOCS_URL` environment variable (e.g. `SMARTIFY_DOCS_URL=http://0.0.0.0:8001`).

To serve docs independently:

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

To build a static site: `mkdocs build` (output goes to `site/`).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

© Smartify Inc. | [https://smartify.ai](https://smartify.ai) | [dev@smartify.ai](mailto:dev@smartify.ai)

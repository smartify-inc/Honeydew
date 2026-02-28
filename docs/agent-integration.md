# Agent Integration

HoneyDew is designed to be used by AI agents as much as by humans. There are three ways to connect your agent, depending on your setup.

!!! info "Prerequisites"
    - HoneyDew must be running (`./start.sh`).
    - No API key is required — the API is open on localhost.
    - If your agent runs on a different host, set `SMARTIFY_API_URL` to the correct base URL.

---

## OpenClaw Skill

**Best for:** [OpenClaw](https://docs.openclaw.ai) users who want fully automatic agent integration.

Install the HoneyDew skill from ClawHub:

```bash
clawhub install honeydew
```

Once installed, your agent knows how to manage your board. Ask it anything:

- _"Create a high-priority task: 'Deploy v2'."_
- _"Show me all overdue cards."_
- _"Move the 'Fix login bug' card to In Progress."_
- _"Transfer everything in Done back to me for review."_
- _"What's on the board right now?"_

The agent calls the HoneyDew API automatically — no manual configuration needed beyond the install.

See the [skill README](https://github.com/smartify-inc/Honeydew/tree/main/skills/honeydew) for details on capabilities and troubleshooting.

---

## Share the Skill Context

**Best for:** Any agent (Claude, GPT, Cursor, Copilot, etc.) — just give it the context file.

The file `skills/honeydew/SKILL.md` contains everything an agent needs: when to use it, how to connect, the full API reference, priority values, and curl examples. Share it with your agent by:

- **Dropping it into your system prompt** as a context block.
- **Attaching it as a file** in a conversation.
- **Copying the relevant sections** into your agent's instructions.

Your agent will know how to call the API, create cards, move them between columns, transfer ownership, and more — with no additional setup.

??? example "What's in SKILL.md?"
    The file covers:

    - **When to use** — Creating, updating, moving, or deleting cards; managing boards and labels; checking overdue or urgent items.
    - **Connection** — Base URL (`http://localhost:8000`), env override (`SMARTIFY_API_URL`), health check (`GET /health`).
    - **Full API table** — Every endpoint with method, path, and required fields.
    - **Priority values** — 1 = Low, 2 = Medium, 3 = High, 4 = Urgent.
    - **Curl examples** — Create a card, move it, transfer it.
    - **Python tools** — Optional higher-level interface via `kanban_tools.py`.

---

## Python Tools Module

**Best for:** Scripted integrations or agents that run Python directly.

The `tools/kanban_tools.py` module provides a higher-level interface on top of the REST API:

```python
from kanban_tools import KanbanTools, Priority

kanban = KanbanTools()

# Agent creates a task for itself
card = kanban.create_task(title="Refactor auth module", priority=Priority.HIGH)

# Work on it
kanban.mark_in_progress(card["id"])

# Hand it back to the human for review
kanban.assign_to_user(card["id"])

# Human approves — mark done
kanban.mark_done(card["id"])
```

The module reads profile IDs and board config from `config.json` automatically. Override the API base URL with `SMARTIFY_API_URL` if the server isn't at `http://localhost:8000`.

For the full method reference, see [Python Tools](python-tools.md).

---

## Which Option Should I Use?

| Scenario | Recommendation |
|----------|---------------|
| You use OpenClaw | [Install the skill](#openclaw-skill) — one command, zero config. |
| You use a different AI agent (Claude, GPT, Cursor, etc.) | [Share SKILL.md](#share-the-skill-context) as context. |
| You want programmatic / scripted control | [Python tools module](#python-tools-module). |
| You want raw HTTP control | Use the [REST API](api-reference.md) directly. |

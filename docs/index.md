# HoneyDew

![HoneyDew](assets/honeydew-logo-only.png){ width="120" }

**Your shared task board with your AI assistant.**

HoneyDew is a live Kanban workspace where you and your AI agent collaborate on real work. Assign tasks, track progress, review outputs, and close the loop — together. It turns a one-off chat with your AI into an ongoing working relationship.

> Built for [OpenClaw](https://docs.openclaw.ai) users. Works with any agent that can call a REST API.

---

## Why HoneyDew

Most AI interactions are ephemeral — you ask, it answers, the context vanishes. HoneyDew gives your agent a persistent workspace alongside you, so nothing gets lost and nothing goes unfinished.

<div class="grid cards" markdown>

- **A shared source of truth** — Both you and your agent read and write the same board. No more copy-pasting outputs into a tracker you maintain alone.
- **Real handoffs** — Assign a card to your agent, let it work, then have it hand the result back to you — with full history on the card.
- **Work while you sleep** — With a simple board check on each heartbeat, your agent works on its todo list while you're out of office.
- **Works the way you think** — Kanban columns, priority levels, due dates, labels, and multi-board support. A task board your agent actually uses.
- **Zero friction** — Two shell commands, no cloud account, no API key. Runs entirely on localhost.
- **Open API, open tools** — A REST API, a Python tools module, and an OpenClaw skill. Wire it up however you work.

</div>

---

## How It Works

```
You create a task ─────► Agent picks it up ─────► Agent delivers results ─────► You review & close
     (To Do)              (In Progress)               (Done / Blocked)            (iterate or done)
```

1. **You assign a task.** Create a card — _"Refactor the auth module, add tests"_ — and assign it to your agent.
2. **Your agent picks it up.** It reads the board, moves the card to In Progress, and gets to work.
3. **It posts its output.** The agent updates the card with results and moves it to Done (or flags it as Blocked if it needs help).
4. **You review and iterate.** See the result on the card, leave a note, reassign, or close it out.

Your agent can also check for new tasks independently — instruct it to poll HoneyDew for incomplete work and step away.

---

## Getting Started

### 1. Clone

```bash
git clone https://github.com/smartify-inc/Honeydew.git honeydew
cd honeydew
```

### 2. Install

```bash
./install.sh
```

This installs backend and frontend dependencies and creates a `config.json` from the example. The installer will prompt you for your name and your agent's name.

### 3. Start

```bash
./start.sh
```

Both servers launch together:

| Service  | URL                        |
|----------|----------------------------|
| Board UI | `http://localhost:5173`     |
| API      | `http://localhost:8000`     |
| API Docs | `http://localhost:8000/docs`|

### 4. Connect your agent

Choose the path that fits your setup:

| Path | Best for |
|------|----------|
| [OpenClaw skill](agent-integration.md#openclaw-skill) | OpenClaw users — one command, fully automatic |
| [Share SKILL.md](agent-integration.md#share-the-skill-context) | Any agent — drop the context file into your system prompt |
| [Python tools](agent-integration.md#python-tools-module) | Scripted or structured integrations |

---

## What's Next

- [**Configuration**](configuration.md) — Customize profiles, board names, and columns.
- [**API Reference**](api-reference.md) — Every endpoint, request body, and query parameter.
- [**Agent Integration**](agent-integration.md) — Three ways to connect your agent.
- [**For Agents**](for-agents.md) — Condensed reference your agent can use directly.
- [**Python Tools**](python-tools.md) — Full `KanbanTools` method reference.
- [**Security**](security.md) — Deployment and trust model.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, @dnd-kit |
| Agent Tools | Python, httpx |

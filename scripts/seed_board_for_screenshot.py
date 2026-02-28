#!/usr/bin/env python3
"""
Seed the HoneyDew board with a "Ship the beta release" scenario for a clean
ClawHub skill listing screenshot. Creates user and agent tasks, agent-completed
cards with token/time badges, one blocked agent task, and one task transferred
back to the user.

Usage:
  ./start.sh   # ensure backend is running
  python scripts/seed_board_for_screenshot.py

Requires: backend at SMARTIFY_API_URL (default http://localhost:8000).
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("SMARTIFY_API_URL", "http://localhost:8000").rstrip("/")
USER_PROFILE = "tony"
AGENT_PROFILE = "jarvis"


def request(method: str, path: str, body: dict | None = None) -> dict | list:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        try:
            err = e.read().decode()
        except Exception:
            err = str(e)
        print(f"HTTP {e.code} {path}: {err}", file=sys.stderr)
        raise
    except URLError as e:
        print(f"Cannot reach {BASE_URL}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_boards() -> list:
    return request("GET", "/api/boards")


def get_board(board_id: int) -> dict:
    return request("GET", f"/api/boards/{board_id}")


def column_ids_by_name(board: dict) -> dict[str, int]:
    out = {}
    for col in board.get("columns", []):
        out[col["name"]] = col["id"]
    return out


def create_card(column_id: int, title: str, profile: str, priority: int = 2, description: str | None = None) -> dict:
    body = {
        "column_id": column_id,
        "title": title,
        "profile": profile,
        "priority": priority,
    }
    if description:
        body["description"] = description
    return request("POST", "/api/cards", body)


def move_card(card_id: int, column_id: int, position: int = 0) -> dict:
    return request("POST", f"/api/cards/{card_id}/move", {"column_id": column_id, "position": position})


def update_card(card_id: int, **kwargs) -> dict:
    return request("PATCH", f"/api/cards/{card_id}", kwargs)


def transfer_card(card_id: int, target_profile: str) -> dict:
    return request("POST", f"/api/cards/{card_id}/transfer", {"target_profile": target_profile})


def main() -> None:
    boards = get_boards()
    if not boards:
        print("No boards found. Add boards in config.json and restart the backend.", file=sys.stderr)
        sys.exit(1)
    board_id = boards[0]["id"]
    board = get_board(board_id)
    cols = column_ids_by_name(board)
    for name in ("To Do", "In Progress", "Done", "Blocked"):
        if name not in cols:
            print(f"Board missing column '{name}'. Expected To Do, In Progress, Done, Blocked.", file=sys.stderr)
            sys.exit(1)

    to_do = cols["To Do"]
    in_progress = cols["In Progress"]
    done = cols["Done"]
    blocked = cols["Blocked"]

    # Create all cards in target column with correct profile
    # To Do
    create_card(to_do, "Finalize release notes", USER_PROFILE)
    create_card(to_do, "Notify stakeholders", USER_PROFILE)
    create_card(to_do, "Run E2E test suite", AGENT_PROFILE)
    # In Progress
    create_card(in_progress, "Deploy to staging", AGENT_PROFILE)
    # Done (agent-completed will get PATCH; one transferred back to user)
    c_docs = create_card(done, "Update API docs", AGENT_PROFILE)
    c_bug = create_card(done, "Fix login bug", AGENT_PROFILE)
    c_review = create_card(done, "Review security scan", AGENT_PROFILE)
    # Blocked
    c_prov = create_card(
        blocked,
        "Provision production DB",
        AGENT_PROFILE,
        description="Waiting on credentials from ops.",
    )

    # Agent stats so badges show on card
    update_card(
        c_docs["id"],
        agent_tokens_used=12_400,
        agent_execution_time_seconds=45.2,
    )
    update_card(
        c_bug["id"],
        agent_tokens_used=3_100,
        agent_execution_time_seconds=8.2,
    )
    update_card(
        c_prov["id"],
        agent_tokens_used=500,
        agent_execution_time_seconds=2.1,
    )

    # "Review security scan" — agent completed it, then transferred to user for sign-off
    transfer_card(c_review["id"], USER_PROFILE)

    print(f"Created 8 cards on board '{board.get('name', board_id)}' (id={board_id}).")
    print("Open http://localhost:5173 to capture the screenshot.")


if __name__ == "__main__":
    main()

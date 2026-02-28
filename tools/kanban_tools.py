"""
HoneyDew — Kanban Board Tools for AI Agents

This module provides a simple interface for agents to interact with the Kanban board API.
All methods return dictionaries with the API response data.

User and agent profile names are loaded from config.json at the project root.

Usage:
    from kanban_tools import KanbanTools, Priority

    kanban = KanbanTools()

    # Get the board
    board = kanban.get_board(1)

    # Create a card
    card = kanban.create_card(
        column_id=1,
        title="Implement feature X",
        priority=Priority.HIGH,
    )

    # Move card to "In Progress"
    kanban.move_card(card["id"], column_id=2)
"""

import json
import os
import httpx
from pathlib import Path
from typing import Optional, List
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    """Card priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


def _find_config_path() -> Path:
    if env_path := os.environ.get("SMARTIFY_CONFIG"):
        return Path(env_path)
    return Path(__file__).resolve().parent.parent / "config.json"


def _parse_boards(data: dict) -> list[dict]:
    raw = data.get("boards")
    if not raw or not isinstance(raw, list):
        return [{"name": "My Board", "columns": ["To Do", "In Progress", "Done"]}]
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        columns = item.get("columns")
        if not name or not isinstance(columns, list):
            continue
        result.append({"name": str(name), "columns": [str(c) for c in columns]})
    return result if result else [{"name": "My Board", "columns": ["To Do", "In Progress", "Done"]}]


def _load_config() -> dict:
    default = {
        "user": {"profile_id": "user", "display_name": "User"},
        "agent": {"profile_id": "agent", "display_name": "Agent"},
        "boards": [{"name": "My Board", "columns": ["To Do", "In Progress", "Done"]}],
    }
    config_path = _find_config_path()
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
        return {
            "user": {
                "profile_id": data.get("user", {}).get("profile_id", default["user"]["profile_id"]),
                "display_name": data.get("user", {}).get("display_name", default["user"]["display_name"]),
            },
            "agent": {
                "profile_id": data.get("agent", {}).get("profile_id", default["agent"]["profile_id"]),
                "display_name": data.get("agent", {}).get("display_name", default["agent"]["display_name"]),
            },
            "boards": _parse_boards(data),
        }
    return default


_CONFIG = _load_config()

USER_PROFILE_ID: str = _CONFIG["user"]["profile_id"]
AGENT_PROFILE_ID: str = _CONFIG["agent"]["profile_id"]
USER_DISPLAY_NAME: str = _CONFIG["user"]["display_name"]
AGENT_DISPLAY_NAME: str = _CONFIG["agent"]["display_name"]
VALID_PROFILES: list[str] = [USER_PROFILE_ID, AGENT_PROFILE_ID]
BOARDS_CONFIG: list[dict] = _CONFIG.get("boards", [{"name": "My Board", "columns": ["To Do", "In Progress", "Done"]}])


class KanbanTools:
    """
    Tools for interacting with the Kanban board API.

    This class provides methods for managing boards, columns, cards, and labels
    through the Kanban board REST API.

    Attributes:
        base_url: The base URL of the Kanban board API server.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def close(self):
        """Close the HTTP client connection."""
        self.client.close()

    # ==================== Board Operations ====================

    def list_boards(self) -> List[dict]:
        """List all available boards."""
        response = self.client.get("/api/boards")
        response.raise_for_status()
        return response.json()

    def get_board(self, board_id: int, profile: Optional[str] = None) -> dict:
        """
        Get a board with all its columns and cards, optionally filtered by profile.

        Args:
            board_id: The ID of the board to retrieve.
            profile: Filter cards by profile ID. If None, returns all cards.
        """
        params = {}
        if profile:
            params["profile"] = profile
        response = self.client.get(f"/api/boards/{board_id}", params=params)
        response.raise_for_status()
        return response.json()

    def create_board(self, name: str) -> dict:
        """Create a new board with default columns (To Do, In Progress, Done)."""
        response = self.client.post("/api/boards", json={"name": name})
        response.raise_for_status()
        return response.json()

    def delete_board(self, board_id: int) -> None:
        """Delete a board and all its columns and cards."""
        response = self.client.delete(f"/api/boards/{board_id}")
        response.raise_for_status()

    # ==================== Column Operations ====================

    def create_column(
        self,
        board_id: int,
        name: str,
        position: Optional[int] = None,
    ) -> dict:
        """Create a new column in a board."""
        payload = {"board_id": board_id, "name": name}
        if position is not None:
            payload["position"] = position
        response = self.client.post("/api/columns", json=payload)
        response.raise_for_status()
        return response.json()

    def update_column(
        self,
        column_id: int,
        name: Optional[str] = None,
        position: Optional[int] = None,
    ) -> dict:
        """Update a column's name or position."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if position is not None:
            payload["position"] = position
        response = self.client.patch(f"/api/columns/{column_id}", json=payload)
        response.raise_for_status()
        return response.json()

    def delete_column(self, column_id: int) -> None:
        """Delete a column and all its cards."""
        response = self.client.delete(f"/api/columns/{column_id}")
        response.raise_for_status()

    # ==================== Card Operations ====================

    def list_cards(
        self,
        board_id: Optional[int] = None,
        column_id: Optional[int] = None,
        priority: Optional[Priority] = None,
        has_due_date: Optional[bool] = None,
    ) -> List[dict]:
        """List cards with optional filters."""
        params = {}
        if board_id is not None:
            params["board_id"] = board_id
        if column_id is not None:
            params["column_id"] = column_id
        if priority is not None:
            params["priority"] = int(priority)
        if has_due_date is not None:
            params["has_due_date"] = has_due_date
        response = self.client.get("/api/cards", params=params)
        response.raise_for_status()
        return response.json()

    def get_card(self, card_id: int) -> dict:
        """Get a card's details."""
        response = self.client.get(f"/api/cards/{card_id}")
        response.raise_for_status()
        return response.json()

    def create_card(
        self,
        column_id: int,
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[date] = None,
        profile: Optional[str] = None,
    ) -> dict:
        """
        Create a new card in the specified column.

        Args:
            column_id: The ID of the column to add the card to.
            title: The title of the card.
            description: Optional description text.
            priority: Priority level (default: MEDIUM).
            due_date: Optional due date.
            profile: The profile to create the card under. Defaults to the
                     user profile from config.
        """
        payload = {
            "column_id": column_id,
            "title": title,
            "priority": int(priority),
            "profile": profile or USER_PROFILE_ID,
        }
        if description is not None:
            payload["description"] = description
        if due_date is not None:
            payload["due_date"] = due_date.isoformat()
        response = self.client.post("/api/cards", json=payload)
        response.raise_for_status()
        return response.json()

    def update_card(
        self,
        card_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        due_date: Optional[date] = None,
        *,
        agent_tokens_used: Optional[int] = None,
        agent_model: Optional[str] = None,
        agent_execution_time_seconds: Optional[float] = None,
        agent_started_at: Optional[str] = None,
        agent_completed_at: Optional[str] = None,
    ) -> dict:
        """Update an existing card's details.

        The agent_* keyword arguments are optional completion metadata.
        Pass ISO datetime strings for agent_started_at / agent_completed_at.
        """
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if priority is not None:
            payload["priority"] = int(priority)
        if due_date is not None:
            payload["due_date"] = due_date.isoformat()
        if agent_tokens_used is not None:
            payload["agent_tokens_used"] = agent_tokens_used
        if agent_model is not None:
            payload["agent_model"] = agent_model
        if agent_execution_time_seconds is not None:
            payload["agent_execution_time_seconds"] = agent_execution_time_seconds
        if agent_started_at is not None:
            payload["agent_started_at"] = agent_started_at
        if agent_completed_at is not None:
            payload["agent_completed_at"] = agent_completed_at
        response = self.client.patch(f"/api/cards/{card_id}", json=payload)
        response.raise_for_status()
        return response.json()

    def move_card(
        self,
        card_id: int,
        column_id: int,
        position: int = 0,
    ) -> dict:
        """Move a card to a different column and/or position."""
        payload = {"column_id": column_id, "position": position}
        response = self.client.post(f"/api/cards/{card_id}/move", json=payload)
        response.raise_for_status()
        return response.json()

    def delete_card(self, card_id: int) -> None:
        """Delete a card."""
        response = self.client.delete(f"/api/cards/{card_id}")
        response.raise_for_status()

    def transfer_card(self, card_id: int, target_profile: str) -> dict:
        """
        Transfer a card to a different profile.

        Args:
            card_id: The ID of the card to transfer.
            target_profile: The target profile ID.
        """
        if target_profile not in VALID_PROFILES:
            raise ValueError(f"Profile must be one of: {VALID_PROFILES}")
        payload = {"target_profile": target_profile}
        response = self.client.post(f"/api/cards/{card_id}/transfer", json=payload)
        response.raise_for_status()
        return response.json()

    # ==================== Comment Operations ====================

    def get_comments(self, card_id: int) -> List[dict]:
        """List all comments on a card, ordered by creation time."""
        response = self.client.get(f"/api/cards/{card_id}/comments")
        response.raise_for_status()
        return response.json()

    def add_comment(self, card_id: int, body: str, profile: Optional[str] = None) -> dict:
        """Add a comment to a card. Defaults to the agent profile."""
        payload: dict = {"body": body}
        if profile:
            payload["profile"] = profile
        else:
            payload["profile"] = AGENT_PROFILE_ID
        response = self.client.post(f"/api/cards/{card_id}/comments", json=payload)
        response.raise_for_status()
        return response.json()

    # ==================== Label Operations ====================

    def list_labels(self) -> List[dict]:
        """List all available labels."""
        response = self.client.get("/api/labels")
        response.raise_for_status()
        return response.json()

    def create_label(self, name: str, color: str = "#6366f1") -> dict:
        """Create a new label."""
        payload = {"name": name, "color": color}
        response = self.client.post("/api/labels", json=payload)
        response.raise_for_status()
        return response.json()

    def add_label_to_card(self, card_id: int, label_id: int) -> dict:
        """Add a label to a card."""
        response = self.client.post(f"/api/cards/{card_id}/labels/{label_id}")
        response.raise_for_status()
        return response.json()

    def remove_label_from_card(self, card_id: int, label_id: int) -> None:
        """Remove a label from a card."""
        response = self.client.delete(f"/api/cards/{card_id}/labels/{label_id}")
        response.raise_for_status()

    # ==================== Convenience Methods ====================

    def get_column_by_name(self, board_id: int, name: str) -> Optional[dict]:
        """Find a column by name within a board (case-insensitive)."""
        board = self.get_board(board_id)
        name_lower = name.lower()
        for column in board["columns"]:
            if column["name"].lower() == name_lower:
                return column
        return None

    def move_card_to_column(
        self,
        card_id: int,
        board_id: int,
        column_name: str,
    ) -> dict:
        """Move a card to a column by name."""
        column = self.get_column_by_name(board_id, column_name)
        if not column:
            raise ValueError(f"Column '{column_name}' not found in board {board_id}")
        return self.move_card(card_id, column["id"])

    def move_card_to_board(
        self,
        card_id: int,
        board_id: int,
        column_name: Optional[str] = None,
    ) -> dict:
        """
        Move a card to another board. The target column is resolved by the API:
        if column_name is provided and exists on the target board, it is used;
        else the card's current column name is matched on the target board if present;
        otherwise the first column of the target board is used.
        """
        payload: dict = {"board_id": board_id}
        if column_name is not None:
            payload["column_name"] = column_name
        response = self.client.post(f"/api/cards/{card_id}/move-to-board", json=payload)
        response.raise_for_status()
        return response.json()

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[date] = None,
        board_id: Optional[int] = None,
        profile: Optional[str] = None,
    ) -> dict:
        """
        Create a new task in the first column of a board (simplified interface for agents).
        If board_id is omitted, uses the first board from the API. Uses the first column
        by position so it works with any column names from config.
        Defaults to the agent profile from config when no profile is specified.
        """
        if board_id is None:
            boards = self.list_boards()
            if not boards:
                raise ValueError("No boards found")
            board_id = boards[0]["id"]
        board = self.get_board(board_id)
        columns = sorted(board["columns"], key=lambda c: c.get("position", 0))
        if not columns:
            raise ValueError(f"Board {board_id} has no columns")
        first_column_id = columns[0]["id"]
        return self.create_card(
            column_id=first_column_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            profile=profile or AGENT_PROFILE_ID,
        )

    def assign_to_agent(self, card_id: int) -> dict:
        """Transfer a card to the AI agent profile."""
        return self.transfer_card(card_id, AGENT_PROFILE_ID)

    def assign_to_user(self, card_id: int) -> dict:
        """Transfer a card to the human user profile."""
        return self.transfer_card(card_id, USER_PROFILE_ID)

    def mark_in_progress(self, card_id: int, board_id: int = 1) -> dict:
        """Move a card to "In Progress" column."""
        return self.move_card_to_column(card_id, board_id, "In Progress")

    def mark_blocked(self, card_id: int, board_id: int = 1) -> dict:
        """Move a card to "Blocked" column."""
        return self.move_card_to_column(card_id, board_id, "Blocked")

    def mark_done(
        self,
        card_id: int,
        board_id: int = 1,
        *,
        agent_tokens_used: Optional[int] = None,
        agent_model: Optional[str] = None,
        agent_execution_time_seconds: Optional[float] = None,
        agent_started_at: Optional[str] = None,
        agent_completed_at: Optional[str] = None,
    ) -> dict:
        """Move a card to "Done" column, optionally recording agent completion metadata."""
        result = self.move_card_to_column(card_id, board_id, "Done")
        metadata = {
            k: v for k, v in {
                "agent_tokens_used": agent_tokens_used,
                "agent_model": agent_model,
                "agent_execution_time_seconds": agent_execution_time_seconds,
                "agent_started_at": agent_started_at,
                "agent_completed_at": agent_completed_at,
            }.items() if v is not None
        }
        if metadata:
            result = self.update_card(card_id, **metadata)
        return result

    def mark_todo(self, card_id: int, board_id: int = 1) -> dict:
        """Move a card back to "To Do" column."""
        return self.move_card_to_column(card_id, board_id, "To Do")

    def get_board_summary(self, board_id: int = 1) -> dict:
        """Get a summary of the board with card counts per column."""
        board = self.get_board(board_id)
        columns_summary = {col["name"]: len(col["cards"]) for col in board["columns"]}
        total_cards = sum(columns_summary.values())
        return {
            "id": board["id"],
            "name": board["name"],
            "total_cards": total_cards,
            "columns": columns_summary,
        }

    def get_overdue_cards(self, board_id: int = 1) -> List[dict]:
        """Get all cards with due dates in the past (excluding Done column)."""
        from datetime import date as date_type
        today = date_type.today()
        board = self.get_board(board_id)
        overdue = []
        for column in board["columns"]:
            if column["name"].lower() == "done":
                continue
            for card in column["cards"]:
                if card["due_date"]:
                    due = date_type.fromisoformat(card["due_date"])
                    if due < today:
                        overdue.append(card)
        return overdue

    def get_urgent_cards(self, board_id: int = 1) -> List[dict]:
        """Get all HIGH and URGENT priority cards (excluding Done column)."""
        board = self.get_board(board_id)
        urgent = []
        for column in board["columns"]:
            if column["name"].lower() == "done":
                continue
            for card in column["cards"]:
                if card["priority"] >= Priority.HIGH:
                    urgent.append(card)
        return sorted(urgent, key=lambda c: -c["priority"])

    def get_cards_in_column(self, column_name: str, board_id: int = 1) -> List[dict]:
        """Get all cards in a specific column by name."""
        column = self.get_column_by_name(board_id, column_name)
        if not column:
            return []
        return column["cards"]

    def set_priority(self, card_id: int, priority: Priority) -> dict:
        """Update a card's priority level."""
        return self.update_card(card_id, priority=priority)

    def set_due_date(self, card_id: int, due_date: date) -> dict:
        """Update a card's due date."""
        return self.update_card(card_id, due_date=due_date)


if __name__ == "__main__":
    kanban = KanbanTools()

    try:
        board = kanban.get_board(1)
        print(f"Board: {board['name']}")

        for column in board["columns"]:
            print(f"  {column['name']}: {len(column['cards'])} cards")

        todo_column = kanban.get_column_by_name(1, "To Do")
        if todo_column:
            card = kanban.create_card(
                column_id=todo_column["id"],
                title="Implement user authentication",
                description="Add JWT-based auth to the API",
                priority=Priority.HIGH,
            )
            print(f"\nCreated card: {card['title']} (ID: {card['id']})")

            in_progress = kanban.get_column_by_name(1, "In Progress")
            if in_progress:
                kanban.move_card(card["id"], in_progress["id"])
                print("Moved card to In Progress")

    finally:
        kanban.close()

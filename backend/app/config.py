"""Application configuration loaded from config.json at project root."""

import json
import os
from pathlib import Path
from typing import TypedDict


class ProfileConfig(TypedDict):
    profile_id: str
    display_name: str


class BoardConfig(TypedDict):
    name: str
    columns: list[str]


class AppConfig(TypedDict):
    user: ProfileConfig
    agent: ProfileConfig
    boards: list[BoardConfig]


_config: AppConfig | None = None

DEFAULT_CONFIG: AppConfig = {
    "user": {"profile_id": "user", "display_name": "User"},
    "agent": {"profile_id": "agent", "display_name": "Agent"},
    "boards": [],
}


def _find_config_path() -> Path:
    if env_path := os.environ.get("SMARTIFY_CONFIG"):
        return Path(env_path)
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "config.json"
    if config_path.exists():
        return config_path
    example_path = project_root / "config.example.json"
    if example_path.exists():
        return example_path
    return config_path


def _parse_boards(data: dict) -> list[BoardConfig]:
    raw = data.get("boards")
    if not raw or not isinstance(raw, list):
        return []
    result: list[BoardConfig] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        columns = item.get("columns")
        if not name or not isinstance(columns, list):
            continue
        result.append({"name": str(name), "columns": [str(c) for c in columns]})
    return result


def load_config() -> AppConfig:
    global _config
    config_path = _find_config_path()
    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
        _config = {
            "user": {
                "profile_id": data.get("user", {}).get("profile_id", DEFAULT_CONFIG["user"]["profile_id"]),
                "display_name": data.get("user", {}).get("display_name", DEFAULT_CONFIG["user"]["display_name"]),
            },
            "agent": {
                "profile_id": data.get("agent", {}).get("profile_id", DEFAULT_CONFIG["agent"]["profile_id"]),
                "display_name": data.get("agent", {}).get("display_name", DEFAULT_CONFIG["agent"]["display_name"]),
            },
            "boards": _parse_boards(data),
        }
    else:
        _config = DEFAULT_CONFIG
    return _config


def get_config() -> AppConfig:
    if _config is None:
        return load_config()
    return _config


def get_valid_profile_ids() -> list[str]:
    cfg = get_config()
    return [cfg["user"]["profile_id"], cfg["agent"]["profile_id"]]


def get_default_profile_id() -> str:
    return get_config()["user"]["profile_id"]


def get_boards_config() -> list[BoardConfig]:
    """Return the boards configuration (name + columns per board)."""
    return get_config()["boards"]

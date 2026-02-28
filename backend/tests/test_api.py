"""API integration tests for HoneyDew."""


# ── Helpers ──────────────────────────────────────────────────────────


def _create_board(client, name="Test Board", columns=None):
    body = {"name": name}
    if columns is not None:
        body["columns"] = columns
    r = client.post("/api/boards", json=body)
    assert r.status_code == 201
    return r.json()


def _first_column_id(board: dict) -> int:
    return board["columns"][0]["id"]


def _create_card(client, column_id, title="Task A", profile="tony", priority=2):
    r = client.post(
        "/api/cards",
        json={
            "column_id": column_id,
            "title": title,
            "profile": profile,
            "priority": priority,
        },
    )
    assert r.status_code == 201
    return r.json()


# ── Health & Config ──────────────────────────────────────────────────


class TestMeta:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "HoneyDew" in r.json()["message"]

    def test_config(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200
        data = r.json()
        assert "user" in data and "agent" in data
        assert data["user"]["profile_id"]
        assert data["agent"]["profile_id"]


# ── Boards ───────────────────────────────────────────────────────────


class TestBoards:
    def test_create_board_default_columns(self, client):
        board = _create_board(client)
        col_names = [c["name"] for c in board["columns"]]
        assert col_names == ["To Do", "In Progress", "Done"]

    def test_create_board_custom_columns(self, client):
        board = _create_board(client, columns=["Backlog", "Active", "Shipped"])
        col_names = [c["name"] for c in board["columns"]]
        assert col_names == ["Backlog", "Active", "Shipped"]

    def test_list_boards(self, client):
        _create_board(client, name="B1")
        _create_board(client, name="B2")
        r = client.get("/api/boards")
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_get_board(self, client):
        board = _create_board(client)
        r = client.get(f"/api/boards/{board['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == board["name"]

    def test_get_board_not_found(self, client):
        r = client.get("/api/boards/9999")
        assert r.status_code == 404

    def test_delete_board(self, client):
        board = _create_board(client)
        r = client.delete(f"/api/boards/{board['id']}")
        assert r.status_code == 204
        r = client.get(f"/api/boards/{board['id']}")
        assert r.status_code == 404

    def test_update_board_name(self, client):
        board = _create_board(client, name="Old")
        r = client.patch(f"/api/boards/{board['id']}", json={"name": "New"})
        assert r.status_code == 200
        assert r.json()["name"] == "New"


# ── Columns ──────────────────────────────────────────────────────────


class TestColumns:
    def test_create_column(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/columns", json={"board_id": board["id"], "name": "Review"}
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Review"

    def test_update_column(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        r = client.patch(f"/api/columns/{col_id}", json={"name": "Renamed"})
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed"

    def test_delete_column(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        r = client.delete(f"/api/columns/{col_id}")
        assert r.status_code == 204

    def test_reorder_column(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        r = client.patch(f"/api/columns/{col_id}", json={"position": 2})
        assert r.status_code == 200
        assert r.json()["position"] == 2


# ── Cards ────────────────────────────────────────────────────────────


class TestCards:
    def test_create_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        assert card["title"] == "Task A"
        assert card["profile"] == "tony"

    def test_create_card_invalid_profile(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/cards",
            json={
                "column_id": _first_column_id(board),
                "title": "Bad",
                "profile": "nonexistent",
            },
        )
        assert r.status_code == 400
        assert "Profile" in r.json()["detail"]

    def test_get_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        r = client.get(f"/api/cards/{card['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == card["id"]

    def test_get_card_not_found(self, client):
        r = client.get("/api/cards/9999")
        assert r.status_code == 404

    def test_update_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        r = client.patch(
            f"/api/cards/{card['id']}",
            json={"title": "Updated", "priority": 3},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"
        assert r.json()["priority"] == 3

    def test_update_card_invalid_profile(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        r = client.patch(
            f"/api/cards/{card['id']}", json={"profile": "hacker"}
        )
        assert r.status_code == 400

    def test_delete_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        r = client.delete(f"/api/cards/{card['id']}")
        assert r.status_code == 204
        r = client.get(f"/api/cards/{card['id']}")
        assert r.status_code == 404

    def test_list_cards(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        _create_card(client, col_id, title="X")
        _create_card(client, col_id, title="Y")
        r = client.get("/api/cards")
        assert r.status_code == 200
        assert len(r.json()) >= 2

    def test_list_cards_filter_profile(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        _create_card(client, col_id, title="D", profile="tony")
        _create_card(client, col_id, title="U", profile="jarvis")
        r = client.get("/api/cards", params={"profile": "tony"})
        assert all(c["profile"] == "tony" for c in r.json())


# ── Card Movement ────────────────────────────────────────────────────


class TestCardMovement:
    def test_move_card_within_column(self, client):
        board = _create_board(client)
        col_id = _first_column_id(board)
        c1 = _create_card(client, col_id, title="First")
        _create_card(client, col_id, title="Second")
        r = client.post(
            f"/api/cards/{c1['id']}/move",
            json={"column_id": col_id, "position": 1},
        )
        assert r.status_code == 200
        assert r.json()["position"] == 1

    def test_move_card_across_columns(self, client):
        board = _create_board(client)
        cols = board["columns"]
        card = _create_card(client, cols[0]["id"])
        r = client.post(
            f"/api/cards/{card['id']}/move",
            json={"column_id": cols[1]["id"], "position": 0},
        )
        assert r.status_code == 200
        assert r.json()["column_id"] == cols[1]["id"]

    def test_move_to_board(self, client):
        b1 = _create_board(client, name="Board 1", columns=["To Do", "Done"])
        b2 = _create_board(client, name="Board 2", columns=["Backlog", "Done"])
        card = _create_card(client, _first_column_id(b1))
        r = client.post(
            f"/api/cards/{card['id']}/move-to-board",
            json={"board_id": b2["id"]},
        )
        assert r.status_code == 200

    def test_move_to_board_column_name_match(self, client):
        """Card in 'Done' on board 1 moves to 'Done' on board 2 via name resolution."""
        b1 = _create_board(client, name="B1", columns=["To Do", "Done"])
        b2 = _create_board(client, name="B2", columns=["Backlog", "Done"])
        done_col_b1 = next(c for c in b1["columns"] if c["name"] == "Done")
        card = _create_card(client, done_col_b1["id"])
        r = client.post(
            f"/api/cards/{card['id']}/move-to-board",
            json={"board_id": b2["id"]},
        )
        assert r.status_code == 200
        done_col_b2 = next(c for c in b2["columns"] if c["name"] == "Done")
        assert r.json()["column_id"] == done_col_b2["id"]

    def test_move_to_board_explicit_column(self, client):
        b1 = _create_board(client, name="B1", columns=["To Do", "Done"])
        b2 = _create_board(client, name="B2", columns=["Backlog", "Active", "Done"])
        card = _create_card(client, _first_column_id(b1))
        r = client.post(
            f"/api/cards/{card['id']}/move-to-board",
            json={"board_id": b2["id"], "column_name": "Active"},
        )
        assert r.status_code == 200
        active_col = next(c for c in b2["columns"] if c["name"] == "Active")
        assert r.json()["column_id"] == active_col["id"]

    def test_move_to_board_fallback_first_column(self, client):
        """No matching column name → lands in first column."""
        b1 = _create_board(client, name="B1", columns=["Alpha"])
        b2 = _create_board(client, name="B2", columns=["Beta", "Gamma"])
        card = _create_card(client, _first_column_id(b1))
        r = client.post(
            f"/api/cards/{card['id']}/move-to-board",
            json={"board_id": b2["id"]},
        )
        assert r.status_code == 200
        assert r.json()["column_id"] == b2["columns"][0]["id"]


# ── Card Transfer ────────────────────────────────────────────────────


class TestTransfer:
    def test_transfer_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board), profile="tony")
        r = client.post(
            f"/api/cards/{card['id']}/transfer",
            json={"target_profile": "jarvis"},
        )
        assert r.status_code == 200
        assert r.json()["profile"] == "jarvis"

    def test_transfer_card_invalid_profile(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        r = client.post(
            f"/api/cards/{card['id']}/transfer",
            json={"target_profile": "invalid"},
        )
        assert r.status_code == 400


# ── Labels ───────────────────────────────────────────────────────────


class TestLabels:
    def test_create_label(self, client):
        r = client.post("/api/labels", json={"name": "Bug", "color": "#ff0000"})
        assert r.status_code == 201
        assert r.json()["name"] == "Bug"
        assert r.json()["color"] == "#ff0000"

    def test_create_label_invalid_color(self, client):
        r = client.post("/api/labels", json={"name": "Bad", "color": "red"})
        assert r.status_code == 422

    def test_list_labels(self, client):
        client.post("/api/labels", json={"name": "A", "color": "#aaaaaa"})
        r = client.get("/api/labels")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_update_label(self, client):
        label = client.post(
            "/api/labels", json={"name": "Old", "color": "#111111"}
        ).json()
        r = client.patch(
            f"/api/labels/{label['id']}", json={"name": "New"}
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_delete_label(self, client):
        label = client.post(
            "/api/labels", json={"name": "Tmp", "color": "#000000"}
        ).json()
        r = client.delete(f"/api/labels/{label['id']}")
        assert r.status_code == 204

    def test_add_and_remove_label_on_card(self, client):
        board = _create_board(client)
        card = _create_card(client, _first_column_id(board))
        label = client.post(
            "/api/labels", json={"name": "Feature", "color": "#00ff00"}
        ).json()
        r = client.post(f"/api/cards/{card['id']}/labels/{label['id']}")
        assert r.status_code == 200
        assert any(l["id"] == label["id"] for l in r.json()["labels"])

        r = client.delete(f"/api/cards/{card['id']}/labels/{label['id']}")
        assert r.status_code == 204


# ── Input Validation ─────────────────────────────────────────────────


class TestValidation:
    def test_card_title_too_long(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/cards",
            json={
                "column_id": _first_column_id(board),
                "title": "x" * 256,
                "profile": "tony",
            },
        )
        assert r.status_code == 422

    def test_card_title_empty(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/cards",
            json={
                "column_id": _first_column_id(board),
                "title": "",
                "profile": "tony",
            },
        )
        assert r.status_code == 422

    def test_card_priority_out_of_range(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/cards",
            json={
                "column_id": _first_column_id(board),
                "title": "ok",
                "priority": 5,
                "profile": "tony",
            },
        )
        assert r.status_code == 422

    def test_board_name_empty(self, client):
        r = client.post("/api/boards", json={"name": ""})
        assert r.status_code == 422

    def test_label_color_bad_format(self, client):
        r = client.post("/api/labels", json={"name": "x", "color": "#gggggg"})
        assert r.status_code == 422

    def test_column_name_too_long(self, client):
        board = _create_board(client)
        r = client.post(
            "/api/columns",
            json={"board_id": board["id"], "name": "y" * 256},
        )
        assert r.status_code == 422

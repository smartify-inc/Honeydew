"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config, get_config, get_boards_config
from .database import engine, Base, SessionLocal
from .models import Board, BoardColumn
from .routers import boards, columns, cards, labels


_AGENT_META_COLUMNS = [
    ("agent_tokens_used", "INTEGER"),
    ("agent_model", "VARCHAR(120)"),
    ("agent_execution_time_seconds", "REAL"),
    ("agent_started_at", "DATETIME"),
    ("agent_completed_at", "DATETIME"),
]


def _migrate_cards_table(db):
    """Add missing agent metadata columns to an existing cards table."""
    rows = db.execute(text("PRAGMA table_info(cards)")).fetchall()
    existing = {row[1] for row in rows}
    for col_name, col_type in _AGENT_META_COLUMNS:
        if col_name not in existing:
            db.execute(text(f"ALTER TABLE cards ADD COLUMN {col_name} {col_type}"))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - creates tables and seeds data on startup."""
    load_config()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _migrate_cards_table(db)

        config_boards = get_boards_config()
        config_names = {b["name"] for b in config_boards}

        existing = {b.name: b for b in db.query(Board).all()}

        for board_cfg in config_boards:
            name = board_cfg["name"]
            if name not in existing:
                board = Board(name=name)
                db.add(board)
                db.flush()
                for pos, col_name in enumerate(board_cfg["columns"]):
                    db.add(BoardColumn(board_id=board.id, name=col_name, position=pos))

        for name, board in existing.items():
            if name not in config_names:
                db.delete(board)

        db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title="HoneyDew API",
    description="Get things done, the smart way - A locally-hosted task management API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boards.router, prefix="/api/boards", tags=["Boards"])
app.include_router(columns.router, prefix="/api/columns", tags=["Columns"])
app.include_router(cards.router, prefix="/api/cards", tags=["Cards"])
app.include_router(labels.router, prefix="/api/labels", tags=["Labels"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "HoneyDew API",
        "tagline": "Get things done, the smart way",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/api/config")
async def get_app_config():
    """Return the application configuration (user/agent names)."""
    return get_config()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

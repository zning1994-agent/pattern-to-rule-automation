from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from pra.core import RuleDraft


class ProposalStore:
    """Small SQLite-backed proposal store for MVP status tracking."""

    def __init__(self, db_path: str | Path = "pra.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    pattern_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def add(self, proposal: RuleDraft) -> None:
        payload = json.dumps(asdict(proposal))
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO proposals (id, pattern_id, status, payload) VALUES (?, ?, ?, ?)",
                (proposal.id, proposal.pattern_id, proposal.status, payload),
            )

    def list(self, status: str | None = None) -> list[dict]:
        query = "SELECT payload FROM proposals"
        params: tuple[str, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [json.loads(row[0]) for row in rows]

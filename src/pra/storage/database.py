from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pra.core import RuleDraft, RuleStatus, validate_status_transition


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
                    payload TEXT NOT NULL,
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    activated_at TEXT,
                    modified_at TEXT
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(proposals)").fetchall()}
            for column in ("reviewed_by", "reviewed_at", "activated_at", "modified_at"):
                if column not in columns:
                    conn.execute(f"ALTER TABLE proposals ADD COLUMN {column} TEXT")

    def add(self, proposal: RuleDraft) -> None:
        payload = json.dumps(asdict(proposal))
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO proposals (
                    id, pattern_id, status, payload, reviewed_by, reviewed_at, activated_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.id,
                    proposal.pattern_id,
                    proposal.status,
                    payload,
                    proposal.reviewed_by,
                    proposal.reviewed_at,
                    proposal.activated_at,
                    proposal.modified_at,
                ),
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

    def transition(self, proposal_id: str, status: str, reviewed_by: str | None = None) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, payload FROM proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
            if row is None:
                raise KeyError(proposal_id)

            current_status, raw_payload = row
            validate_status_transition(current_status, status)
            payload = json.loads(raw_payload)
            now = datetime.now(UTC).isoformat()
            payload["status"] = status

            fields: dict[str, str | None] = {"status": status}
            if status in {RuleStatus.APPROVED.value, RuleStatus.DEPRECATED.value}:
                fields["reviewed_by"] = reviewed_by
                fields["reviewed_at"] = now
                payload["reviewed_by"] = reviewed_by
                payload["reviewed_at"] = now
            if status == RuleStatus.ACTIVE.value:
                fields["activated_at"] = now
                payload["activated_at"] = now
            if status == RuleStatus.MODIFIED.value:
                fields["modified_at"] = now
                payload["modified_at"] = now

            conn.execute(
                """
                UPDATE proposals
                SET status = ?, payload = ?, reviewed_by = ?, reviewed_at = ?, activated_at = ?, modified_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    json.dumps(payload),
                    payload.get("reviewed_by"),
                    payload.get("reviewed_at"),
                    payload.get("activated_at"),
                    payload.get("modified_at"),
                    proposal_id,
                ),
            )
            return payload

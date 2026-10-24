"""Production SQLite repository for AI activity, sessions, conversations, and reports."""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from nexus.config import DB_PATH
from nexus.security.redaction import redact_secrets


class NexusDatabase:
    """
    Local SQLite storage handling:
    - Provider sessions and route changes
    - Imported conversations and user captures
    - Extension pairing credentials
    - Analysis reports and provenance
    - Local chat conversations
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._get_connection() as conn:
            # 1. Pairing tokens table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pairing_tokens (
                    token TEXT PRIMARY KEY,
                    pairing_code TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
                """
            )

            # 2. Tracked sessions
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracked_sessions (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    is_captured INTEGER NOT NULL DEFAULT 0,
                    is_analyzed INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            # 3. Session activity events log
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    provider TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT
                )
                """
            )

            # 4. Conversations (imported or explicitly captured)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_url TEXT,
                    import_method TEXT NOT NULL, -- 'capture', 'export_json', 'export_zip', 'text'
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_analyzed INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            # 5. Local chat history
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS local_chat_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )

            # 6. Analysis Reports
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    scenario_title TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    findings_count INTEGER NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )

            # 7. Application settings (key-value store for preferences like active provider)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # --- Settings Methods ---
    def get_setting(self, key: str, default_val: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default_val

    def set_setting(self, key: str, value: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()

    # --- Pairing Methods ---
    def generate_pairing_code(self) -> str:
        code = str(uuid.uuid4())[:8].upper()
        token = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO pairing_tokens (token, pairing_code, created_at, is_active) VALUES (?, ?, ?, 1)",
                (token, code, now),
            )
            conn.commit()
        return code

    def verify_and_claim_pairing_code(self, code: str) -> Optional[str]:
        code = code.strip().upper()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT token FROM pairing_tokens WHERE pairing_code = ? AND is_active = 1",
                (code,),
            )
            row = cursor.fetchone()
            if row:
                return row["token"]
        return None

    def validate_token(self, token: str) -> bool:
        if not token:
            return False
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM pairing_tokens WHERE token = ? AND is_active = 1",
                (token,),
            )
            return cursor.fetchone() is not None

    # --- Session Tracking Methods ---
    def record_session_event(self, provider: str, url: str, title: str, event_type: str = "navigation") -> Dict[str, Any]:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            # Check if session exists for this URL
            cursor = conn.execute("SELECT id FROM tracked_sessions WHERE url = ?", (url,))
            row = cursor.fetchone()
            if row:
                session_id = row["id"]
                conn.execute(
                    "UPDATE tracked_sessions SET last_seen = ?, title = CASE WHEN ? != '' THEN ? ELSE title END WHERE id = ?",
                    (now, title, title, session_id),
                )
            else:
                session_id = f"sess_{uuid.uuid4().hex[:12]}"
                clean_title = title if title.strip() else f"{provider.capitalize()} Session"
                conn.execute(
                    """
                    INSERT INTO tracked_sessions (id, provider, url, title, first_seen, last_seen, is_captured, is_analyzed)
                    VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                    """,
                    (session_id, provider, url, clean_title, now, now),
                )

            # Record event log
            event_id = f"evt_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO activity_events (id, session_id, provider, event_type, url, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, session_id, provider, event_type, url, now, json.dumps({"title": title})),
            )
            conn.commit()

        return {"session_id": session_id, "provider": provider, "url": url}

    def list_tracked_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tracked_sessions ORDER BY last_seen DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def list_activity_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM activity_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- Conversation Storage ---
    def store_conversation(
        self,
        provider: str,
        title: str,
        content: str,
        import_method: str = "capture",
        source_url: Optional[str] = None,
    ) -> str:
        cid = f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        redacted = redact_secrets(content)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, provider, title, source_url, import_method, content, created_at, is_analyzed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (cid, provider, title, source_url or "", import_method, redacted, now),
            )
            # If matching session URL, mark as captured
            if source_url:
                conn.execute("UPDATE tracked_sessions SET is_captured = 1 WHERE url = ?", (source_url,))
            conn.commit()
        return cid

    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, provider, title, source_url, import_method, created_at, is_analyzed, length(content) as content_len FROM conversations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_conversation(self, conv_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()
            return True

    def store_chat_message(self, conversation_id: str, role: str, content: str) -> str:
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        redacted = redact_secrets(content)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO local_chat_messages (id, conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (msg_id, conversation_id, role, redacted, now),
            )
            conn.commit()
        return msg_id

    def list_chat_messages(self, conversation_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM local_chat_messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
                (conversation_id, limit),
            )
            return [dict(r) for r in cursor.fetchall()]

    def clear_all(self) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tracked_sessions")
            conn.execute("DELETE FROM activity_events")
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM local_chat_messages")
            conn.execute("DELETE FROM analysis_reports")
            conn.commit()
            return True

import sqlite3
from datetime import datetime
from config.settings import DB_PATH


class ConversationHistory:
    def __init__(self):
        self.db_path = str(DB_PATH)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    def create_conversation(self, title="Nova Conversa"):
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
                (title, now)
            )
            conn.commit()
            return cursor.lastrowid

    def list_conversations(self, limit=50, offset=0):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, title, created_at FROM conversations ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def rename_conversation(self, conversation_id, new_title):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (new_title.strip(), conversation_id)
            )
            conn.commit()

    def delete_conversation(self, conversation_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()

    def add_message(self, conversation_id, role, content):
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, now)
            )
            conn.commit()

    def get_messages(self, conversation_id, limit=50, offset=0):
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT role, content, created_at FROM (
                    SELECT id, role, content, created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                ) ORDER BY id ASC
                """,
                (conversation_id, limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]
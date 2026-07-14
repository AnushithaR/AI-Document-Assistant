"""
database.py
------------
Handles all SQLite database operations for the AI Document Assistant.

Stores a persistent log of every question asked and answer generated,
along with which document(s) were involved and when. This turns the
app from a stateless demo into something with a real audit trail —
useful for showing usage history or debugging later.

SQLite is used because it's a single-file, zero-configuration database
built into Python's standard library — perfect for a lightweight
portfolio deployment that doesn't need a separate database server.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from config import Config


class Database:
    """
    Manages the SQLite connection and all read/write operations for
    logging Q&A interactions.
    """

    def __init__(self, db_path: Path = None):
        """
        Args:
            db_path: Path to the SQLite database file. Defaults to
                     Config.DATABASE_PATH if not provided.
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._create_tables_if_not_exist()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Opens a new SQLite connection. A new connection per operation is
        used rather than one long-lived connection, since FastAPI handles
        concurrent requests and SQLite connections aren't safely shared
        across threads — this keeps things simple and safe.
        """
        return sqlite3.connect(str(self.db_path))

    def _create_tables_if_not_exist(self) -> None:
        """
        Creates the qa_history table if it doesn't already exist.
        Safe to call every time the app starts — CREATE TABLE IF NOT EXISTS
        is a no-op if the table is already there.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qa_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_names TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize database: {e}") from e

    def log_interaction(self, pdf_names: List[str], question: str, answer: str) -> None:
        """
        Logs a single Q&A interaction to the database.

        Args:
            pdf_names: List of PDF filenames involved in this session.
            question: The user's question.
            answer: The AI-generated answer.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            pdf_names_str = ", ".join(pdf_names) if pdf_names else "Unknown"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO qa_history (pdf_names, question, answer, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (pdf_names_str, question, answer, timestamp),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[Database] Warning: Failed to log interaction: {e}")

    def get_history(self, limit: int = 50) -> List[Dict]:
        """
        Retrieves the most recent Q&A history entries, newest first.

        Args:
            limit: Maximum number of history rows to return.

        Returns:
            A list of dicts, each with keys: id, pdf_names, question,
            answer, timestamp. Empty list if no history exists or on error.
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, pdf_names, question, answer, timestamp
                FROM qa_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            print(f"[Database] Warning: Failed to fetch history: {e}")
            return []

    def clear_history(self) -> None:
        """
        Deletes all rows from the qa_history table.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM qa_history")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Database] Warning: Failed to clear history: {e}")
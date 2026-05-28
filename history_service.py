import sqlite3
import json
from datetime import datetime
from typing import Any


DB_PATH = "./rag_history.db"

def get_conn():
    return sqlite3.connect(DB_PATH)


def init_histofy_db() -> None:
    """
    初始化问答列表
    """

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        chunks_json TEXT,
        created_at TEXT NOT NULL
    )"""
    )

    conn.commit()
    conn.close()

def save_qa_history(
        question: str,
        answer: str,
        chunks: list[dict[str,Any]],
) -> None:
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO qa_history (question, answer, chunks_json, created_at)
    VALUES (?,?,?,?)""",
                (question,
                answer,
                json.dumps(chunks or [], ensure_ascii=True),
                datetime.now().strftime("%Y-%m-%d %h:%M:%S"))
    )

    history_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return history_id


def list_qa_history(limit: int = 50) -> list[dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, question, answer, chunks_json, created_at
        FROM qa_history
        ORDER BY id DESC LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    data = []

    for row in rows:
        data.append({
            "id": row[0],
            "question": row[1],
            "answer": row[2],
            "chunks": json.loads(row[3]),
            "created_at": row[4],
        })
    return data




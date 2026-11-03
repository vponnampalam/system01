import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request


app = Flask(__name__)
DATABASE = Path(__file__).with_name("messages.db")
MAX_MESSAGE_LENGTH = 500


def initialize_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL DEFAULT 'anonymous',
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )


@app.post("/messages")
def post_message():
    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.form

    message = payload.get("message", "") if hasattr(payload, "get") else ""
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="A non-empty 'message' is required."), 400

    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(error=f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer."), 400

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.execute(
            "INSERT INTO messages (author, body, created_at) VALUES (?, ?, ?)",
            ("anonymous", message, created_at),
        )

    return jsonify(id=cursor.lastrowid, message=message), 201


@app.get("/messages/count")
def message_count():
    with sqlite3.connect(DATABASE) as connection:
        count = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    return jsonify(count=count)


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

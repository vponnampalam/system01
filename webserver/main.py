import os
import sqlite3
from concurrent.futures import TimeoutError
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import GoogleAuthError
from google.cloud import pubsub_v1
from flask import Flask, jsonify, request


app = Flask(__name__)
DATABASE = Path(__file__).with_name("messages.db")
MAX_MESSAGE_LENGTH = 500


@lru_cache(maxsize=1)
def pubsub_publisher():
    return pubsub_v1.PublisherClient()


def publish_message(message):
    topic = os.environ.get("PUBSUB_TOPIC")
    if not topic:
        raise RuntimeError("PUBSUB_TOPIC environment variable is required.")

    future = pubsub_publisher().publish(topic, message.encode("utf-8"))
    return future.result(timeout=10)


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

    try:
        pubsub_message_id = publish_message(message)
    except (GoogleAPICallError, GoogleAuthError, RuntimeError, TimeoutError):
        app.logger.exception("Failed to publish message to Pub/Sub.")
        return jsonify(error="Failed to publish message to Pub/Sub."), 503

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.execute(
            "INSERT INTO messages (author, body, created_at) VALUES (?, ?, ?)",
            ("anonymous", message, created_at),
        )

    return jsonify(
        id=cursor.lastrowid,
        message=message,
        pubsub_message_id=pubsub_message_id,
    ), 201


@app.get("/messages/count")
def message_count():
    with sqlite3.connect(DATABASE) as connection:
        count = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    return jsonify(count=count)


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, url_for


app = Flask(__name__)
DATABASE = Path(__file__).with_name("messages.db")
MAX_MESSAGE_LENGTH = 500

PAGE = """<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta name="theme-color" content="#183c32">
	<title>Commonplace | A small message board</title>
	<style>
		:root {
			color-scheme: light;
			--ink: #1c3028;
			--muted: #66756d;
			--paper: #f5f4ed;
			--line: #d9ddd3;
			--green: #183c32;
			--lime: #d5ef83;
			--orange: #e48d57;
		}
		* { box-sizing: border-box; }
		body {
			margin: 0;
			color: var(--ink);
			background: var(--paper);
			font-family: "Trebuchet MS", "Segoe UI", sans-serif;
		}
		.masthead {
			padding: 3rem max(1.25rem, calc((100vw - 1060px) / 2)) 3.5rem;
			color: #f5f4ed;
			background-color: var(--green);
			background-image: linear-gradient(115deg, transparent 70%, rgba(213,239,131,.08) 70%),
				radial-gradient(rgba(245,244,237,.11) .7px, transparent .7px);
			background-size: auto, 9px 9px;
		}
		.masthead-inner, main { max-width: 1060px; margin: 0 auto; }
		.eyebrow {
			margin: 0 0 1.1rem;
			color: var(--lime);
			font-size: .75rem;
			font-weight: 700;
			letter-spacing: .12em;
			text-transform: uppercase;
		}
		h1 {
			margin: 0;
			font-family: Georgia, "Times New Roman", serif;
			font-size: 3.25rem;
			font-weight: 400;
			line-height: 1.05;
		}
		.intro { max-width: 32rem; margin: 1rem 0 0; color: #d1dcd4; line-height: 1.6; }
		main {
			display: grid;
			grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
			gap: 4rem;
			padding: 3rem 1.25rem 5rem;
		}
		.composer {
			align-self: start;
			padding: 1.5rem;
			border: 1px solid var(--line);
			border-top: 4px solid var(--orange);
			background: #fffefa;
		}
		h2 { margin: 0 0 1.25rem; font-size: 1.05rem; }
		label { display: block; margin: 1rem 0 .45rem; font-size: .82rem; font-weight: 700; }
		input, textarea {
			display: block;
			width: 100%;
			padding: .8rem .85rem;
			border: 1px solid #cbd2c8;
			border-radius: 2px;
			color: var(--ink);
			background: white;
			font: inherit;
		}
		input:focus, textarea:focus { outline: 2px solid #6c947c; outline-offset: 1px; }
		textarea { min-height: 145px; resize: vertical; line-height: 1.5; }
		button {
			width: 100%;
			margin-top: 1.1rem;
			padding: .9rem 1rem;
			border: 0;
			border-radius: 2px;
			color: #172c23;
			background: var(--lime);
			font: inherit;
			font-weight: 700;
			cursor: pointer;
		}
		button:hover { background: #c6e36d; }
		.hint { margin: .7rem 0 0; color: var(--muted); font-size: .75rem; line-height: 1.5; }
		.feed-heading {
			display: flex;
			align-items: baseline;
			justify-content: space-between;
			gap: 1rem;
			padding-bottom: .85rem;
			border-bottom: 1px solid var(--line);
		}
		.feed-heading h2 { margin: 0; font-family: Georgia, "Times New Roman", serif; font-size: 1.7rem; font-weight: 400; }
		.count { color: var(--muted); font-size: .78rem; }
		.message { padding: 1.35rem 0 1.5rem; border-bottom: 1px solid var(--line); }
		.message-meta { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; }
		.author { margin: 0; font-size: .88rem; font-weight: 700; }
		time { color: var(--muted); font-size: .73rem; white-space: nowrap; }
		.message-body { margin: .65rem 0 0; font-family: Georgia, "Times New Roman", serif; font-size: 1.08rem; line-height: 1.65; overflow-wrap: anywhere; white-space: pre-wrap; }
		.empty { padding: 2.5rem 0; color: var(--muted); line-height: 1.6; }
		.error { margin: 0 0 1rem; color: #a53e27; font-size: .85rem; }
		@media (max-width: 700px) {
			.masthead { padding-top: 2.25rem; padding-bottom: 2.5rem; }
			h1 { font-size: 2.65rem; }
			main { grid-template-columns: 1fr; gap: 2.5rem; padding-top: 2rem; }
		}
	</style>
</head>
<body>
	<header class="masthead">
		<div class="masthead-inner">
			<p class="eyebrow">A little corner of the internet</p>
			<h1>Commonplace</h1>
			<p class="intro">Leave a thought, a hello, or something worth passing along. The conversation is better with you in it.</p>
		</div>
	</header>
	<main>
		<section class="composer" aria-labelledby="compose-title">
			<h2 id="compose-title">Add to the board</h2>
			{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
			<form method="post" action="{{ url_for('post_message') }}">
				<label for="author">Your name</label>
				<input id="author" name="author" maxlength="60" required autocomplete="name" value="{{ author }}" placeholder="Name">
				<label for="message">Your message</label>
				<textarea id="message" name="message" maxlength="{{ max_length }}" required placeholder="Write a note...">{{ message }}</textarea>
				<button type="submit">Post message</button>
				<p class="hint">Messages are public. Keep it kind and under {{ max_length }} characters.</p>
			</form>
		</section>
		<section aria-labelledby="feed-title">
			<div class="feed-heading">
				<h2 id="feed-title">The board</h2>
				<span class="count">{{ messages|length }} {{ 'message' if messages|length == 1 else 'messages' }}</span>
			</div>
			{% if messages %}
				{% for item in messages %}
					<article class="message">
						<div class="message-meta">
							<p class="author">{{ item['author'] }}</p>
							<time>{{ item['created_at'] }} UTC</time>
						</div>
						<p class="message-body">{{ item['body'] }}</p>
					</article>
				{% endfor %}
			{% else %}
				<p class="empty">Nothing here just yet. Start the conversation with a note of your own.</p>
			{% endif %}
		</section>
	</main>
</body>
</html>"""


def initialize_database():
		with sqlite3.connect(DATABASE) as connection:
				connection.execute(
						"""CREATE TABLE IF NOT EXISTS messages (
								id INTEGER PRIMARY KEY AUTOINCREMENT,
								author TEXT NOT NULL,
								body TEXT NOT NULL,
								created_at TEXT NOT NULL
						)"""
				)


def load_messages():
		with sqlite3.connect(DATABASE) as connection:
				connection.row_factory = sqlite3.Row
				return connection.execute(
						"SELECT author, body, created_at FROM messages ORDER BY id DESC"
				).fetchall()


def render_board(error=None, author="", message="", status=200):
		return (
				render_template_string(
						PAGE,
						messages=load_messages(),
						error=error,
						author=author,
						message=message,
						max_length=MAX_MESSAGE_LENGTH,
				),
				status,
		)


@app.get("/")
def index():
		return render_board()


@app.post("/messages")
def post_message():
		author = request.form.get("author", "").strip()
		message = request.form.get("message", "").strip()

		if not author or not message:
				return render_board("Add your name and a message to post.", author, message, 400)
		if len(author) > 60:
				return render_board("Your name must be 60 characters or fewer.", author, message, 400)
		if len(message) > MAX_MESSAGE_LENGTH:
				return render_board(
						f"Your message must be {MAX_MESSAGE_LENGTH} characters or fewer.",
						author,
						message,
						400,
				)

		with sqlite3.connect(DATABASE) as connection:
				connection.execute(
						"INSERT INTO messages (author, body, created_at) VALUES (?, ?, ?)",
						(author, message, datetime.utcnow().strftime("%Y-%m-%d %H:%M")),
				)
		return redirect(url_for("index"), code=303)


initialize_database()


if __name__ == "__main__":
		app.run(host="0.0.0.0", port=5000)

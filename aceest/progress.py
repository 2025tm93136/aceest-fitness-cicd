"""v2.0.1 - Weekly adherence tracking persisted in SQLite."""
from flask import Blueprint, jsonify, request

from .db import find_client, get_db, is_int

bp = Blueprint("progress", __name__)


@bp.post("/clients/<name>/progress")
def add_progress(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    data = request.get_json(silent=True) or {}
    week = data.get("week")
    adherence = data.get("adherence")
    if not week or not is_int(adherence) or not 0 <= adherence <= 100:
        return jsonify(error="week is required and adherence must be an integer 0-100"), 400
    db = get_db()
    db.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (name, week, adherence),
    )
    db.commit()
    return jsonify(week=week, adherence=adherence), 201


def _entries(name):
    rows = get_db().execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    return [dict(r) for r in rows]


@bp.get("/clients/<name>/progress")
def get_progress(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    entries = _entries(name)
    average = round(sum(e["adherence"] for e in entries) / len(entries), 1) if entries else None
    return jsonify(entries=entries, average_adherence=average)


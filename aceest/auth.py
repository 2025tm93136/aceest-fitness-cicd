"""v3.1.2 - User login, AI-style program generator and client report."""
import os
import secrets

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .db import find_client, get_db

bp = Blueprint("auth", __name__)

PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"],
}


def ensure_admin():
    """Seed an admin user; the password comes from ADMIN_PASSWORD (never hard-coded)."""
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        return
    password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("admin", generate_password_hash(password), "Admin"),
    )
    db.commit()


@bp.post("/login")
def login():
    ensure_admin()
    data = request.get_json(silent=True) or {}
    row = get_db().execute(
        "SELECT password_hash, role FROM users WHERE username=?", (data.get("username", ""),)
    ).fetchone()
    if not row or not check_password_hash(row["password_hash"], data.get("password", "")):
        return jsonify(error="Invalid credentials"), 401
    return jsonify(username=data["username"], role=row["role"])


def pick_program(rng=secrets.SystemRandom()):
    program_type = rng.choice(sorted(PROGRAM_TEMPLATES))
    return program_type, rng.choice(PROGRAM_TEMPLATES[program_type])


@bp.post("/clients/<name>/generate-program")
def generate_program(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    program_type, detail = pick_program()
    db = get_db()
    db.execute("UPDATE clients SET program=? WHERE name=?", (detail, name))
    db.commit()
    return jsonify(client=name, program_type=program_type, program=detail)


@bp.get("/clients/<name>/report")
def report(name):
    client = find_client(name)
    if not client:
        return jsonify(error="Client not found"), 404
    db = get_db()
    workouts = db.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(duration_min), 0) AS minutes FROM workouts WHERE client_name=?",
        (name,),
    ).fetchone()
    adherence = db.execute(
        "SELECT AVG(adherence) AS avg FROM progress WHERE client_name=?", (name,)
    ).fetchone()
    return jsonify(
        client=dict(client),
        workouts_logged=workouts["n"],
        total_workout_minutes=workouts["minutes"],
        average_adherence=round(adherence["avg"], 1) if adherence["avg"] is not None else None,
    )

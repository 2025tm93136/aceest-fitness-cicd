"""v1.1 - Client profiles with calorie estimation."""
from flask import Blueprint, jsonify, request

from .db import find_client, get_db
from .programs import PROGRAMS

bp = Blueprint("clients", __name__)


def calculate_calories(weight_kg, program_code):
    """Daily calorie estimate = body weight (kg) x program calorie factor."""
    if program_code not in PROGRAMS:
        raise ValueError(f"Unknown program: {program_code}")
    if weight_kg is None or weight_kg <= 0:
        raise ValueError("Weight must be a positive number")
    return int(weight_kg * PROGRAMS[program_code]["calorie_factor"])


@bp.get("/clients")
def list_clients():
    rows = get_db().execute("SELECT * FROM clients ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/clients")
def create_client():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    program = (data.get("program") or "").upper()
    if not name:
        return jsonify(error="Client name is required"), 400
    try:
        weight = float(data.get("weight", 0))
        calories = calculate_calories(weight, program)
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    if find_client(name):
        return jsonify(error="Client already exists"), 409
    db = get_db()
    db.execute(
        "INSERT INTO clients (name, age, weight, program, calories, membership_end) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, data.get("age"), weight, program, calories, data.get("membership_end")),
    )
    db.commit()
    return jsonify(dict(find_client(name))), 201


@bp.get("/clients/<name>")
def get_client(name):
    client = find_client(name)
    if not client:
        return jsonify(error="Client not found"), 404
    return jsonify(dict(client))


@bp.delete("/clients/<name>")
def delete_client(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    db = get_db()
    for table in ("progress", "workouts", "metrics"):
        db.execute(f"DELETE FROM {table} WHERE client_name=?", (name,))  # nosec B608 - fixed table list
    db.execute("DELETE FROM clients WHERE name=?", (name,))
    db.commit()
    return "", 204

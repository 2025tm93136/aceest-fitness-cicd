"""v2.2.4 - Workout log, body metrics and BMI."""
from datetime import date

from flask import Blueprint, jsonify, request

from .db import find_client, get_db, is_int

bp = Blueprint("workouts", __name__)

WORKOUT_TYPES = {"Strength", "Hypertrophy", "Cardio", "Mobility"}


def calculate_bmi(weight_kg, height_cm):
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive")
    return round(weight_kg / (height_cm / 100) ** 2, 1)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


@bp.post("/bmi")
def bmi():
    data = request.get_json(silent=True) or {}
    try:
        value = calculate_bmi(float(data.get("weight", 0)), float(data.get("height", 0)))
    except (TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(bmi=value, category=bmi_category(value))


@bp.post("/clients/<name>/workouts")
def add_workout(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    data = request.get_json(silent=True) or {}
    workout_type = data.get("type")
    duration = data.get("duration_min")
    if workout_type not in WORKOUT_TYPES:
        return jsonify(error=f"type must be one of {sorted(WORKOUT_TYPES)}"), 400
    if not is_int(duration) or duration <= 0:
        return jsonify(error="duration_min must be a positive integer"), 400
    workout_date = data.get("date") or date.today().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, workout_date, workout_type, duration, data.get("notes", "")),
    )
    db.commit()
    return jsonify(date=workout_date, type=workout_type, duration_min=duration), 201


@bp.get("/clients/<name>/workouts")
def get_workouts(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    rows = get_db().execute(
        "SELECT date, workout_type, duration_min, notes FROM workouts "
        "WHERE client_name=? ORDER BY date DESC",
        (name,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/clients/<name>/metrics")
def add_metrics(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    data = request.get_json(silent=True) or {}
    try:
        weight = float(data["weight"])
        waist = float(data.get("waist", 0))
        bodyfat = float(data.get("bodyfat", 0))
    except (KeyError, TypeError, ValueError):
        return jsonify(error="weight is required; waist and bodyfat must be numbers"), 400
    if weight <= 0:
        return jsonify(error="weight must be positive"), 400
    metric_date = data.get("date") or date.today().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?, ?, ?, ?, ?)",
        (name, metric_date, weight, waist, bodyfat),
    )
    db.commit()
    return jsonify(date=metric_date, weight=weight, waist=waist, bodyfat=bodyfat), 201


@bp.get("/clients/<name>/metrics")
def get_metrics(name):
    if not find_client(name):
        return jsonify(error="Client not found"), 404
    rows = get_db().execute(
        "SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name=? ORDER BY date",
        (name,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])

"""v3.2.4 - Membership status and renewal."""
from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from .db import find_client, get_db, is_int

bp = Blueprint("membership", __name__)


def membership_is_active(status, end_date, today=None):
    if status != "Active":
        return False
    if not end_date:
        return True
    return date.fromisoformat(end_date) >= (today or date.today())


@bp.get("/clients/<name>/membership")
def membership(name):
    client = find_client(name)
    if not client:
        return jsonify(error="Client not found"), 404
    return jsonify(
        status=client["membership_status"],
        end=client["membership_end"],
        active=membership_is_active(client["membership_status"], client["membership_end"]),
    )


@bp.post("/clients/<name>/membership/renew")
def renew(name):
    client = find_client(name)
    if not client:
        return jsonify(error="Client not found"), 404
    data = request.get_json(silent=True) or {}
    months = data.get("months", 1)
    if not is_int(months) or not 1 <= months <= 24:
        return jsonify(error="months must be an integer 1-24"), 400
    start = date.today()
    if client["membership_end"] and date.fromisoformat(client["membership_end"]) > start:
        start = date.fromisoformat(client["membership_end"])
    new_end = (start + timedelta(days=30 * months)).isoformat()
    db = get_db()
    db.execute(
        "UPDATE clients SET membership_status='Active', membership_end=? WHERE name=?",
        (new_end, name),
    )
    db.commit()
    return jsonify(status="Active", end=new_end)

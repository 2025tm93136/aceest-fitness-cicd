"""v1.1.2 - Export client data as CSV."""
import csv
import io

from flask import Blueprint, Response

from .db import get_db

bp = Blueprint("exports", __name__)

COLUMNS = ("name", "age", "weight", "program", "calories", "membership_status")


@bp.get("/export/clients.csv")
def export_clients():
    rows = get_db().execute(
        "SELECT name, age, weight, program, calories, membership_status FROM clients ORDER BY name"
    ).fetchall()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for row in rows:
        writer.writerow([row[c] for c in COLUMNS])
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"},
    )

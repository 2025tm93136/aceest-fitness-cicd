import random

from aceest.auth import PROGRAM_TEMPLATES, pick_program


def test_login(monkeypatch, client):
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret-test")
    assert client.post("/login", json={"username": "admin", "password": "s3cret-test"}).get_json()["role"] == "Admin"
    assert client.post("/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    assert client.post("/login", json={}).status_code == 401


def test_pick_program_is_valid():
    program_type, detail = pick_program(random.Random(1))
    assert detail in PROGRAM_TEMPLATES[program_type]


def test_generate_program(client, member):
    body = client.post(f"/clients/{member}/generate-program").get_json()
    assert body["program"] in PROGRAM_TEMPLATES[body["program_type"]]
    assert client.get(f"/clients/{member}").get_json()["program"] == body["program"]
    assert client.post("/clients/Nobody/generate-program").status_code == 404


def test_report(client, member):
    client.post(f"/clients/{member}/workouts", json={"type": "Cardio", "duration_min": 30})
    client.post(f"/clients/{member}/progress", json={"week": "W1", "adherence": 90})
    body = client.get(f"/clients/{member}/report").get_json()
    assert body["workouts_logged"] == 1
    assert body["total_workout_minutes"] == 30
    assert body["average_adherence"] == 90.0
    assert client.get("/clients/Nobody/report").status_code == 404

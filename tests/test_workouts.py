import pytest

from aceest.workouts import bmi_category, calculate_bmi


def test_calculate_bmi():
    assert calculate_bmi(70, 175) == 22.9
    with pytest.raises(ValueError):
        calculate_bmi(70, 0)


@pytest.mark.parametrize("bmi,category", [(17, "Underweight"), (22, "Normal"), (27, "Overweight"), (32, "Obese")])
def test_bmi_category(bmi, category):
    assert bmi_category(bmi) == category


def test_bmi_endpoint(client):
    body = client.post("/bmi", json={"weight": 70, "height": 175}).get_json()
    assert body == {"bmi": 22.9, "category": "Normal"}
    assert client.post("/bmi", json={"weight": 70}).status_code == 400


def test_workouts(client, member):
    payload = {"type": "Strength", "duration_min": 60, "date": "2026-03-01"}
    res = client.post(f"/clients/{member}/workouts", json=payload)
    assert res.status_code == 201
    assert client.get(f"/clients/{member}/workouts").get_json()[0]["workout_type"] == "Strength"


@pytest.mark.parametrize("payload", [
    {"type": "Yoga", "duration_min": 30},
    {"type": "Cardio", "duration_min": 0},
    {"type": "Cardio", "duration_min": True},
])
def test_workout_validation(client, member, payload):
    assert client.post(f"/clients/{member}/workouts", json=payload).status_code == 400


def test_metrics(client, member):
    assert client.post(f"/clients/{member}/metrics",
                       json={"weight": 78.5, "waist": 84, "bodyfat": 18}).status_code == 201
    assert client.get(f"/clients/{member}/metrics").get_json()[0]["weight"] == 78.5
    assert client.post(f"/clients/{member}/metrics", json={"waist": 84}).status_code == 400
    assert client.post(f"/clients/{member}/metrics", json={"weight": -1}).status_code == 400

import pytest


def test_progress_average(client, member):
    client.post(f"/clients/{member}/progress", json={"week": "W1", "adherence": 80})
    client.post(f"/clients/{member}/progress", json={"week": "W2", "adherence": 90})
    body = client.get(f"/clients/{member}/progress").get_json()
    assert len(body["entries"]) == 2
    assert body["average_adherence"] == 85.0


def test_progress_empty_average_is_none(client, member):
    assert client.get(f"/clients/{member}/progress").get_json()["average_adherence"] is None


@pytest.mark.parametrize("payload", [
    {"week": "W1", "adherence": 150},
    {"adherence": 50},
])
def test_progress_validation(client, member, payload):
    assert client.post(f"/clients/{member}/progress", json=payload).status_code == 400


def test_progress_unknown_client(client):
    assert client.post("/clients/Nobody/progress", json={}).status_code == 404


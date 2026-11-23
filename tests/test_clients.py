import pytest

from aceest.clients import calculate_calories


@pytest.mark.parametrize("program,expected", [("FL", 1760), ("MG", 2800), ("BG", 2080)])
def test_calculate_calories(program, expected):
    assert calculate_calories(80, program) == expected


@pytest.mark.parametrize("weight,program", [(80, "XX"), (0, "FL"), (-3, "MG")])
def test_calculate_calories_rejects_bad_input(weight, program):
    with pytest.raises(ValueError):
        calculate_calories(weight, program)


def test_create_and_get_client(client):
    res = client.post("/clients", json={"name": "Priya", "weight": 60, "program": "BG"})
    assert res.status_code == 201
    assert res.get_json()["calories"] == 1560
    assert client.get("/clients/Priya").get_json()["program"] == "BG"


@pytest.mark.parametrize("payload", [
    {"weight": 60, "program": "BG"},
    {"name": "X", "weight": 60, "program": "ZZ"},
    {"name": "X", "weight": -5, "program": "FL"},
])
def test_create_client_validation(client, payload):
    assert client.post("/clients", json=payload).status_code == 400


def test_duplicate_client(client, member):
    assert client.post("/clients", json={"name": member, "weight": 80, "program": "FL"}).status_code == 409


def test_list_and_delete_client(client, member):
    assert [c["name"] for c in client.get("/clients").get_json()] == [member]
    assert client.delete(f"/clients/{member}").status_code == 204
    assert client.get(f"/clients/{member}").status_code == 404
    assert client.delete(f"/clients/{member}").status_code == 404

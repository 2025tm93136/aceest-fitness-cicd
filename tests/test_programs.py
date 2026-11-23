def test_list_programs(client):
    assert client.get("/programs").get_json() == {
        "FL": "Fat Loss", "MG": "Muscle Gain", "BG": "Beginner"
    }


def test_get_program_case_insensitive(client):
    body = client.get("/programs/mg").get_json()
    assert body["code"] == "MG"
    assert body["target_kcal"] == 3200


def test_unknown_program(client):
    assert client.get("/programs/XX").status_code == 404

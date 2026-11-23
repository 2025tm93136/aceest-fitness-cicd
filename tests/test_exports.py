def test_export_csv(client, member):
    res = client.get("/export/clients.csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    lines = res.get_data(as_text=True).strip().splitlines()
    assert lines[0] == "name,age,weight,program,calories,membership_status"
    assert lines[1].startswith(f"{member},28,80.0,FL,1760")


def test_export_csv_empty(client):
    lines = client.get("/export/clients.csv").get_data(as_text=True).strip().splitlines()
    assert len(lines) == 1

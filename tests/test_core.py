def test_health(client):
    assert client.get("/health").get_json() == {"status": "UP"}


def test_version_endpoint(app, client):
    body = client.get("/version").get_json()
    assert body["version"] == app.config["APP_VERSION"]
    assert "programs" in body["features"]


def test_index_page_shows_version(app, client):
    res = client.get("/")
    assert res.status_code == 200
    assert app.config["APP_VERSION"].encode() in res.data


def test_unknown_route_returns_json_404(client):
    res = client.get("/does-not-exist")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Not found"}


def test_deployment_track_from_env(monkeypatch, tmp_path):
    from aceest import create_app
    monkeypatch.setenv("DEPLOYMENT_TRACK", "canary")
    app = create_app({"DATABASE": str(tmp_path / "t.db")})
    assert app.test_client().get("/version").get_json()["track"] == "canary"


from datetime import date

import pytest

from aceest.membership import membership_is_active


def test_membership_is_active():
    today = date(2026, 1, 1)
    assert membership_is_active("Active", None, today)
    assert membership_is_active("Active", "2026-06-30", today)
    assert not membership_is_active("Active", "2025-12-31", today)
    assert not membership_is_active("Expired", None, today)


def test_membership_endpoint(client, member):
    body = client.get(f"/clients/{member}/membership").get_json()
    assert body["status"] == "Active" and body["active"] is True


def test_renew_membership(client, member):
    body = client.post(f"/clients/{member}/membership/renew", json={"months": 3}).get_json()
    assert body["status"] == "Active"
    assert date.fromisoformat(body["end"]) > date.today()


@pytest.mark.parametrize("months", [0, 25, True, "3"])
def test_renew_validation(client, member, months):
    assert client.post(f"/clients/{member}/membership/renew", json={"months": months}).status_code == 400


def test_membership_unknown_client(client):
    assert client.get("/clients/Nobody/membership").status_code == 404
    assert client.post("/clients/Nobody/membership/renew", json={}).status_code == 404

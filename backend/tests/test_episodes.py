from tests.conftest import auth_header


def test_create_episode(client):
    headers = auth_header(client)
    project_id = client.get("/api/projects", headers=headers).json()[0]["id"]
    res = client.post(
        "/api/episodes",
        headers=headers,
        json={"project_id": project_id, "number": 99, "title": "OVA: After Credits"},
    )
    assert res.status_code == 201
    assert res.json()["title"] == "OVA: After Credits"


def test_list_episodes_includes_risk(client):
    headers = auth_header(client)
    project_id = client.get("/api/projects", headers=headers).json()[0]["id"]
    res = client.get("/api/episodes", params={"project_id": project_id}, headers=headers)
    assert res.status_code == 200
    ep7 = next(e for e in res.json() if e["number"] == 7)
    assert ep7["risk_level"] in {"high", "critical"}
    assert ep7["scene_count"] >= 14

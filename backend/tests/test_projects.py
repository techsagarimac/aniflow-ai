from tests.conftest import auth_header


def test_list_and_get_project(client):
    headers = auth_header(client)
    res = client.get("/api/projects", headers=headers)
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1
    assert projects[0]["name"] == "Project Sakura"
    pid = projects[0]["id"]
    detail = client.get(f"/api/projects/{pid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["episode_count"] == 12


def test_create_project(client):
    headers = auth_header(client)
    res = client.post(
        "/api/projects",
        headers=headers,
        json={
            "name": "Project North Wind",
            "description": "Pilot shorts",
            "genre": "adventure",
            "studio": "Northwind Animation",
            "episode_count": 4,
            "status": "planning",
        },
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Project North Wind"

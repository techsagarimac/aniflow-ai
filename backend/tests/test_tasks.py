from tests.conftest import auth_header


def test_create_and_assign_task(client):
    headers = auth_header(client)
    users = client.get("/api/users", headers=headers).json()
    aki = next(u for u in users if u["email"] == "artist@aniflow.ai")
    project_id = client.get("/api/projects", headers=headers).json()[0]["id"]
    res = client.post(
        "/api/tasks",
        headers=headers,
        json={
            "project_id": project_id,
            "title": "Paint dusk BG for river path",
            "type": "background",
            "priority": "high",
            "assignee_id": aki["id"],
            "estimated_hours": 6,
        },
    )
    assert res.status_code == 201
    assert res.json()["assignee"]["id"] == aki["id"]

    artist_headers = auth_header(client, "artist@aniflow.ai")
    mine = client.get("/api/tasks", headers=artist_headers).json()
    assert any(t["title"] == "Paint dusk BG for river path" for t in mine)

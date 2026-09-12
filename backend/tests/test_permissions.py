from tests.conftest import auth_header


def test_artist_cannot_create_project(client):
    headers = auth_header(client, "artist@aniflow.ai")
    res = client.post("/api/projects", headers=headers, json={"name": "Hacked"})
    assert res.status_code == 403


def test_artist_cannot_view_unassigned_scene(client):
    manager = auth_header(client)
    scenes = client.get("/api/scenes", headers=manager).json()
    other = next(s for s in scenes if s["assigned_artist"] and s["assigned_artist"]["email"] != "artist@aniflow.ai")
    artist = auth_header(client, "artist@aniflow.ai")
    res = client.get(f"/api/scenes/{other['id']}", headers=artist)
    assert res.status_code == 403


def test_reviewer_can_create_revision(client):
    manager = auth_header(client)
    scene = next(s for s in client.get("/api/scenes", headers=manager).json() if s["scene_number"] == 42)
    reviewer = auth_header(client, "reviewer@aniflow.ai")
    res = client.post(
        "/api/revisions",
        headers=reviewer,
        json={"scene_id": scene["id"], "issue": "Eyeline is off.", "comment": "Look toward the stairwell."},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "open"

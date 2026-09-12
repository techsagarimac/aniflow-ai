from tests.conftest import auth_header


def test_list_scenes_and_scene_042(client):
    headers = auth_header(client)
    scenes = client.get("/api/scenes", headers=headers).json()
    assert len(scenes) >= 100
    scene = next(s for s in scenes if s["scene_number"] == 42)
    assert "rooftop" in scene["description"].lower()
    detail = client.get(f"/api/scenes/{scene['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["assigned_artist"]["full_name"] == "Aki Tanaka"


def test_create_scene(client):
    headers = auth_header(client)
    episode = client.get("/api/episodes", headers=headers).json()[0]
    res = client.post(
        "/api/scenes",
        headers=headers,
        json={
            "episode_id": episode["id"],
            "scene_number": 900,
            "description": "A quiet pan across empty desks.",
            "location": "Classroom",
            "duration_seconds": 6,
        },
    )
    assert res.status_code == 201
    assert res.json()["display_id"] == "SCN-900"


def test_move_scene_kanban(client):
    headers = auth_header(client)
    scene = next(s for s in client.get("/api/scenes", headers=headers).json() if s["scene_number"] == 81)
    res = client.patch(f"/api/scenes/{scene['id']}", headers=headers, json={"kanban_column": "animation"})
    assert res.status_code == 200
    assert res.json()["production_stage"] == "key_animation"
    assert res.json()["kanban_column"] == "animation"

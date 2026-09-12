from tests.conftest import auth_header


def test_revision_request_and_versions(client):
    headers = auth_header(client, "reviewer@aniflow.ai")
    manager = auth_header(client)
    scene = next(s for s in client.get("/api/scenes", headers=manager).json() if s["scene_number"] == 42)
    versions = client.get(f"/api/files/scene/{scene['id']}", headers=headers).json()
    assert len(versions) >= 3
    labels = {v["label"] for v in versions}
    assert "v01" in labels and "v02" in labels

    reviews = client.get("/api/reviews", params={"scene_id": scene["id"]}, headers=headers).json()
    assert any(r["status"] == "revision_required" for r in reviews)

    revs = client.get("/api/revisions", params={"scene_id": scene["id"]}, headers=headers).json()
    assert any("hand" in r["issue"].lower() for r in revs)

from app.ai.mock import MockAIService


def test_schedule_estimate_shape():
    result = MockAIService().estimate_schedule(
        {"episode_id": 1, "episode_number": 5, "scene_count": 12, "avg_complexity": 3, "available_artists": 4}
    )
    assert result["is_ai_estimate"] is True
    assert "disclaimer" in result
    assert result["estimated_working_days"] > 0
    assert "animation" in result["stages"]


def test_bottleneck_requires_approval():
    result = MockAIService().detect_bottlenecks(
        {
            "waiting_by_stage": {"key_animation": 14},
            "artist_workloads": [{"name": "Ren", "workload_percent": 105}],
            "overdue_count": 4,
            "episode_number": 7,
        }
    )
    item = result["bottlenecks"][0]
    assert item["requires_manager_approval"] is True
    assert item["risk_level"] in {"high", "critical", "medium"}


def test_artist_recommendation_is_manual():
    result = MockAIService().recommend_artist(
        {
            "scene": {"id": 1, "stage": "key_animation"},
            "artists": [
                {"user_id": 1, "name": "Aki", "artist_role": "key_animator", "skills": ["key animation"], "workload_percent": 60, "completed_similar": True},
                {"user_id": 2, "name": "Ren", "artist_role": "animator", "skills": ["in-between"], "workload_percent": 105, "completed_similar": False},
            ],
        }
    )
    assert result["requires_manager_approval"] is True
    assert result["recommended"]["name"] == "Aki"


def test_risk_calculation_high():
    result = MockAIService().calculate_risk(
        {"deadline_pressure": 80, "artist_workload": 92, "revision_rate": 50, "incomplete_ratio": 75}
    )
    assert result["risk_score"] >= 65
    assert result["risk_level"] in {"high", "critical"}
    assert "disclaimer" in result


def test_ai_schedule_endpoint(client):
    from tests.conftest import auth_header

    headers = auth_header(client)
    episodes = client.get("/api/episodes", headers=headers).json()
    ep = next(e for e in episodes if e["number"] == 7)
    res = client.post("/api/ai/schedule", headers=headers, json={"episode_id": ep["id"]})
    assert res.status_code == 200
    assert res.json()["is_ai_estimate"] is True


def test_ai_chat_uses_project_data(client):
    from tests.conftest import auth_header

    headers = auth_header(client)
    res = client.post("/api/ai/chat", headers=headers, json={"message": "Which episodes are at risk?"})
    assert res.status_code == 200
    assert "Episode" in res.json()["answer"]

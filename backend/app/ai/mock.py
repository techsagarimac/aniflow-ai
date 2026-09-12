from __future__ import annotations

from typing import Any

from app.ai.base import AIService
from app.models.enums import RiskLevel


def _risk_label(score: float) -> str:
    if score >= 85:
        return RiskLevel.CRITICAL.value
    if score >= 65:
        return RiskLevel.HIGH.value
    if score >= 40:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


class MockAIService(AIService):
    """Deterministic, data-driven estimates labeled as AI estimates."""

    def estimate_schedule(self, context: dict[str, Any]) -> dict[str, Any]:
        scenes = context.get("scene_count") or 10
        complexity = context.get("avg_complexity") or 3
        artists = max(context.get("available_artists") or 3, 1)
        hist = context.get("avg_hours_per_scene") or 10
        factor = (complexity / 3) * (hist / 8)
        per_scene_days = max(0.3, factor / artists)
        storyboard = round(max(1, scenes * 0.08 * factor), 1)
        layout = round(max(1, scenes * 0.06 * factor), 1)
        animation = round(max(2, scenes * per_scene_days * 0.45), 1)
        background = round(max(1, scenes * 0.12 * factor), 1)
        coloring = round(max(1, scenes * 0.1 * factor), 1)
        compositing = round(max(1, scenes * 0.08 * factor), 1)
        qc = round(max(1, scenes * 0.05 * factor), 1)
        total = round(storyboard + layout + animation + background + coloring + compositing + qc, 1)
        return {
            "is_ai_estimate": True,
            "disclaimer": "AI estimate based on current roster and historical averages. Not a guaranteed delivery date.",
            "episode_id": context.get("episode_id"),
            "episode_number": context.get("episode_number"),
            "episode_title": context.get("episode_title"),
            "stages": {
                "storyboard": {"days": storyboard},
                "layout": {"days": layout},
                "animation": {"days": animation},
                "background": {"days": background},
                "coloring": {"days": coloring},
                "compositing": {"days": compositing},
                "qc": {"days": qc},
            },
            "estimated_working_days": total,
            "assumptions": {
                "scene_count": scenes,
                "avg_complexity": complexity,
                "available_artists": artists,
                "historical_hours_per_scene": hist,
            },
        }

    def detect_bottlenecks(self, context: dict[str, Any]) -> dict[str, Any]:
        waiting = context.get("waiting_by_stage") or {}
        workloads = context.get("artist_workloads") or []
        overdue = context.get("overdue_count") or 0
        items = []
        for stage, count in sorted(waiting.items(), key=lambda kv: kv[1], reverse=True):
            if count >= 5:
                overloaded = [w for w in workloads if w.get("workload_percent", 0) >= 90]
                rec_count = min(3, max(1, count // 5))
                predicted = f"{max(2, count // 4)}–{max(3, count // 3)} days"
                items.append(
                    {
                        "stage": stage,
                        "episode_id": context.get("episode_id"),
                        "episode_number": context.get("episode_number"),
                        "reason": f"{count} scenes are waiting at {stage.replace('_', ' ')}.",
                        "artist_workload": overloaded[0]["workload_percent"] if overloaded else 0,
                        "predicted_delay": predicted,
                        "recommended_action": f"Reassign {rec_count} medium-priority scenes to artists with spare capacity.",
                        "requires_manager_approval": True,
                        "risk_level": _risk_label(min(100, 40 + count * 3 + overdue * 4)),
                    }
                )
        if not items:
            items.append(
                {
                    "stage": "none",
                    "reason": "No significant queue detected. Continue current assignments.",
                    "predicted_delay": "0 days",
                    "recommended_action": "No redistribution required.",
                    "requires_manager_approval": False,
                    "risk_level": "low",
                }
            )
        return {"is_ai_estimate": True, "bottlenecks": items[:4], "overdue_count": overdue}

    def recommend_artist(self, context: dict[str, Any]) -> dict[str, Any]:
        scene = context.get("scene") or {}
        artists = context.get("artists") or []
        needed = (scene.get("stage") or "key_animation").replace("_", " ")
        scored = []
        for artist in artists:
            skills = [s.lower() for s in artist.get("skills") or []]
            role = (artist.get("artist_role") or "").replace("_", " ")
            skill_match = 30 if needed.split()[0] in " ".join(skills + [role]) else 10
            if any(token in " ".join(skills) for token in needed.split()):
                skill_match = 40
            capacity = max(0, 100 - float(artist.get("workload_percent") or 0))
            similar = 15 if artist.get("completed_similar") else 5
            deadline_ok = 15 if capacity > 15 else 0
            score = skill_match + capacity * 0.4 + similar + deadline_ok
            reasons = []
            if skill_match >= 30:
                reasons.append(f"Strong {role} skills matched to {needed}")
            reasons.append(f"Available capacity: {round(capacity)}%")
            if similar >= 15:
                reasons.append("Similar scenes completed successfully")
            reasons.append("Deadline compatible" if deadline_ok else "Tight capacity vs deadline")
            scored.append(
                {
                    "artist_id": artist.get("user_id"),
                    "name": artist.get("name"),
                    "score": round(score, 1),
                    "reasons": reasons,
                    "workload_percent": artist.get("workload_percent"),
                    "availability": artist.get("availability"),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        primary = scored[0] if scored else None
        return {
            "is_ai_estimate": True,
            "disclaimer": "Recommendation only. A manager must approve any assignment.",
            "requires_manager_approval": True,
            "recommended": primary,
            "alternatives": scored[1:4],
            "scene_id": scene.get("id"),
        }

    def calculate_risk(self, context: dict[str, Any]) -> dict[str, Any]:
        deadline_pressure = min(100, context.get("deadline_pressure", 40))
        workload = min(100, context.get("artist_workload", 40))
        revision_rate = min(100, context.get("revision_rate", 20))
        incomplete = min(100, context.get("incomplete_ratio", 40))
        score = round(
            deadline_pressure * 0.3 + workload * 0.25 + revision_rate * 0.2 + incomplete * 0.25
        )
        level = _risk_label(score)
        recs = []
        if workload >= 90:
            recs.append("Redistribute overloaded artist work after manager approval.")
        if incomplete >= 60:
            recs.append("Prioritize blocking scenes in the current bottleneck stage.")
        if revision_rate >= 50:
            recs.append("Schedule a director review huddle to reduce revision loops.")
        if deadline_pressure >= 70:
            recs.append("Protect the next milestone; freeze non-critical polish.")
        if not recs:
            recs.append("Maintain current staffing. Recheck after the next review gate.")
        return {
            "is_ai_estimate": True,
            "disclaimer": "Risk score is an AI estimate, not a production guarantee.",
            "risk_score": score,
            "risk_level": level,
            "factors": {
                "deadline_pressure": round(deadline_pressure),
                "artist_workload": round(workload),
                "revision_rate": round(revision_rate),
                "incomplete_scenes": round(incomplete),
            },
            "recommendations": recs,
            "predicted_delay_days": f"{max(0, int((score - 40) / 12))}–{max(1, int((score - 30) / 10))}",
        }

    def answer_project_question(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        q = question.lower()
        episodes = context.get("episodes") or []
        artists = context.get("artists") or []
        overdue_tasks = context.get("overdue_tasks") or []
        waiting_review = context.get("waiting_review") or 0
        bottlenecks = context.get("bottlenecks") or []

        def ep_label(e):
            return f"Episode {e['number']:02d} — {e['title']} ({e['status']}, {e['progress']}% , risk {e.get('risk_level') or 'n/a'})"

        if "risk" in q or "at risk" in q:
            risky = [e for e in episodes if (e.get("risk_level") in {"high", "critical"}) or (e.get("risk_score") or 0) >= 65]
            text = "Episodes currently at risk:\n" + "\n".join(ep_label(e) for e in risky or episodes[:3])
        elif "overload" in q or "artist" in q and "workload" in q:
            busy = sorted(artists, key=lambda a: a.get("workload_percent") or 0, reverse=True)
            lines = [f"{a['name']}: {a['workload_percent']}% ({a['deadline_risk']} risk)" for a in busy[:6]]
            text = "Artist workload snapshot:\n" + "\n".join(lines)
        elif "review" in q:
            text = f"{waiting_review} scenes are waiting for review right now."
        elif "overdue" in q:
            lines = [f"- {t}" for t in overdue_tasks[:8]] or ["No overdue tasks."]
            text = "Overdue work:\n" + "\n".join(lines)
        elif "priorit" in q:
            text = (
                "Prioritize bottleneck scenes first: reduce queues in key animation, "
                "then unstick QC so completed animation can ship. High-priority overdue scenes next."
            )
        elif "episode 7" in q or "episode 07" in q or "ep 7" in q or "delayed" in q:
            match = next((e for e in episodes if e.get("number") == 7), None)
            bn = next((b for b in bottlenecks if b.get("episode_number") == 7), bottlenecks[0] if bottlenecks else None)
            if match:
                text = (
                    f"Episode 07 ({match['title']}) is {match['status']} at {match['progress']}% "
                    f"with risk {match.get('risk_level')} ({match.get('risk_score')}/100). "
                )
            else:
                text = "Episode 07 is the current animation bottleneck. "
            if bn:
                text += bn.get("reason", "") + " " + bn.get("recommended_action", "")
            text += " AI will not reassign work unless a manager approves."
        elif "estimate" in q or "completion" in q:
            text = (
                "Use the schedule estimator on the episode page for stage-by-stage working-day estimates. "
                "Those figures are AI estimates, not guaranteed dates."
            )
        else:
            top = sorted(episodes, key=lambda e: (e.get("risk_score") or 0), reverse=True)[:3]
            text = "Production snapshot:\n" + "\n".join(ep_label(e) for e in top)
            text += f"\n{waiting_review} scenes await review. {len(overdue_tasks)} overdue tasks."
        return {
            "is_ai_estimate": True,
            "answer": text.strip(),
            "sources": ["project database"],
        }

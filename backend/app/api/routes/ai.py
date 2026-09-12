import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.context import artist_rec_context, assistant_context, episode_ai_context, persist_analysis, risk_context
from app.ai.factory import get_ai_service
from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.ai import AIAnalysis, RiskAssessment
from app.models.enums import NotificationType, RiskLevel, UserRole
from app.models.production import Episode, Scene
from app.models.user import User
from app.schemas import (
    ApproveAnalysisRequest,
    AssignmentRecRequest,
    BottleneckRequest,
    ChatRequest,
    ScheduleEstimateRequest,
)
from app.services.notifications import notify
from app.services.serializers import parse_json_list, parse_json_obj

router = APIRouter(prefix="/ai", tags=["ai"])


def _episode(db: Session, episode_id: int) -> Episode:
    ep = db.get(Episode, episode_id)
    if not ep:
        raise HTTPException(404, "Episode not found")
    return ep


@router.post("/schedule")
def schedule(
    payload: ScheduleEstimateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    episode = _episode(db, payload.episode_id)
    result = get_ai_service().estimate_schedule(episode_ai_context(db, episode))
    persist_analysis(db, project_id=episode.project_id, episode_id=episode.id, analysis_type="schedule", payload=result)
    db.commit()
    return result


@router.post("/bottlenecks")
def bottlenecks(
    payload: BottleneckRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if payload.episode_id:
        episode = _episode(db, payload.episode_id)
        ctx = episode_ai_context(db, episode)
        result = get_ai_service().detect_bottlenecks(ctx)
        persist_analysis(
            db,
            project_id=episode.project_id,
            episode_id=episode.id,
            analysis_type="bottleneck",
            payload=result,
            requires_approval=True,
        )
        db.commit()
        return result

    episodes = db.scalars(select(Episode).order_by(Episode.number)).all()
    if payload.project_id:
        episodes = [e for e in episodes if e.project_id == payload.project_id]
    combined = {"waiting_by_stage": {}, "artist_workloads": [], "overdue_count": 0, "episode_number": None}
    items = []
    for ep in episodes:
        ctx = episode_ai_context(db, ep)
        part = get_ai_service().detect_bottlenecks(ctx)
        for b in part.get("bottlenecks") or []:
            if b.get("stage") != "none":
                b["episode_number"] = ep.number
                b["episode_id"] = ep.id
                items.append(b)
    result = {"is_ai_estimate": True, "bottlenecks": items[:6] or [{"stage": "none", "reason": "No bottlenecks", "risk_level": "low"}]}
    return result


@router.post("/assignment-recommendation")
def assignment_recommendation(
    payload: AssignmentRecRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scene = db.scalar(select(Scene).options(selectinload(Scene.episode)).where(Scene.id == payload.scene_id))
    if not scene:
        raise HTTPException(404, "Scene not found")
    result = get_ai_service().recommend_artist(artist_rec_context(db, scene))
    persist_analysis(
        db,
        project_id=scene.episode.project_id if scene.episode else None,
        episode_id=scene.episode_id,
        analysis_type="assignment",
        payload=result,
        requires_approval=True,
    )
    db.commit()
    return result


@router.post("/risk-analysis")
def risk_analysis(
    payload: BottleneckRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not payload.episode_id:
        raise HTTPException(400, "episode_id is required")
    episode = _episode(db, payload.episode_id)
    result = get_ai_service().calculate_risk(risk_context(db, episode))
    db.add(
        RiskAssessment(
            project_id=episode.project_id,
            episode_id=episode.id,
            risk_score=result.get("risk_score", 0),
            risk_level=RiskLevel(result.get("risk_level", "medium")),
            factors=json.dumps(result.get("factors") or {}),
            recommendations=json.dumps(result.get("recommendations") or []),
            predicted_delay_days=str(result.get("predicted_delay_days") or ""),
        )
    )
    persist_analysis(db, project_id=episode.project_id, episode_id=episode.id, analysis_type="risk", payload=result)
    if result.get("risk_level") in {"high", "critical"}:
        managers = db.scalars(select(User).where(User.role.in_([UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR]))).all()
        for mgr in managers:
            notify(
                db,
                user_id=mgr.id,
                ntype=NotificationType.AI_RISK_DETECTED,
                title=f"Episode {episode.number:02d} has entered {result['risk_level']}-risk status.",
                message=f"Risk score {result.get('risk_score')}/100. AI estimate only.",
                entity_type="episode",
                entity_id=episode.id,
            )
    db.commit()
    return result


@router.post("/chat")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    ctx = assistant_context(db, payload.project_id)
    result = get_ai_service().answer_project_question(payload.message, ctx)
    persist_analysis(db, project_id=payload.project_id, episode_id=None, analysis_type="chat", payload={"q": payload.message, **result})
    db.commit()
    return result


@router.get("/analyses")
def analyses(
    episode_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(AIAnalysis).order_by(AIAnalysis.created_at.desc())
    if episode_id:
        query = query.where(AIAnalysis.episode_id == episode_id)
    rows = db.scalars(query.limit(40)).all()
    return [
        {
            "id": r.id,
            "analysis_type": r.analysis_type,
            "summary": r.summary,
            "payload": parse_json_obj(r.payload) or parse_json_list(r.payload),
            "requires_approval": r.requires_approval,
            "approved": r.approved,
            "episode_id": r.episode_id,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/analyses/{analysis_id}/approve")
def approve_analysis(
    analysis_id: int,
    payload: ApproveAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    row = db.get(AIAnalysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    row.approved = payload.approved
    row.approved_by_id = user.id
    db.commit()
    return {"id": row.id, "approved": row.approved, "message": "Recorded. Work was not auto-reassigned."}

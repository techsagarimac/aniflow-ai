from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config import get_settings
from app.models.ai import AIAnalysis, Notification, RiskAssessment
from app.models.enums import (
    ArtistRole,
    Availability,
    EpisodeStatus,
    ExperienceLevel,
    FileKind,
    NotificationType,
    Priority,
    ProductionStage,
    ProjectStatus,
    ReviewStatus,
    RevisionStatus,
    RiskLevel,
    SceneStatus,
    TaskStatus,
    TaskType,
    UserRole,
)
from app.models.files import Comment, FileAsset, FileVersion, Review, RevisionRequest
from app.models.production import Character, Episode, Project, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import Assignment, ProductionMilestone, Task
from app.services.production import recompute_episode_progress, stage_progress
from app.storage import storage

DEMO_EMAILS = [
    "admin@aniflow.ai",
    "manager@aniflow.ai",
    "director@aniflow.ai",
    "reviewer@aniflow.ai",
    "artist@aniflow.ai",
]

EPISODE_META = [
    (1, "The Thread Appears", EpisodeStatus.COMPLETED, 100),
    (2, "Rooftop Promise", EpisodeStatus.COMPLETED, 100),
    (3, "Festival Lights", EpisodeStatus.COMPLETED, 100),
    (4, "The Quiet Classroom", EpisodeStatus.QC, 92),
    (5, "Wind Over the Gym", EpisodeStatus.POST_PRODUCTION, 82),
    (6, "Night Train Sketch", EpisodeStatus.ANIMATION, 48),
    (7, "Broken Flow", EpisodeStatus.ANIMATION, 38),
    (8, "Letters in the Rain", EpisodeStatus.STORYBOARD, 18),
    (9, "The Empty Clubroom", EpisodeStatus.PLANNING, 6),
    (10, "Twin Rivers", EpisodeStatus.PLANNING, 4),
    (11, "Last Summer Bell", EpisodeStatus.PLANNING, 3),
    (12, "Sakura, After", EpisodeStatus.PLANNING, 2),
]

SCENE_RANGES = {
    1: range(1, 11),
    2: range(11, 21),
    3: range(21, 31),
    4: range(31, 41),
    5: range(41, 53),
    6: range(53, 65),
    7: range(65, 81),
    8: range(81, 91),
    9: range(91, 97),
    10: range(97, 103),
    11: range(103, 109),
    12: range(109, 115),
}

EPISODE_STAGE = {
    1: ProductionStage.COMPLETED,
    2: ProductionStage.COMPLETED,
    3: ProductionStage.COMPLETED,
    4: ProductionStage.QC,
    5: ProductionStage.COMPOSITING,
    6: ProductionStage.KEY_ANIMATION,
    7: ProductionStage.KEY_ANIMATION,
    8: ProductionStage.STORYBOARD,
    9: ProductionStage.SCRIPT,
    10: ProductionStage.SCRIPT,
    11: ProductionStage.SCRIPT,
    12: ProductionStage.SCRIPT,
}

LOCATIONS = [
    "School rooftop",
    "West staircase",
    "Clubroom 2-B",
    "River path",
    "Train platform",
    "Sakura's kitchen",
    "Gymnasium",
    "Festival street",
    "Library annex",
    "Bus stop at dusk",
]

SCENE_BEATS = [
    "Sakura notices a faint gold thread between two classmates.",
    "Ken asks if she is alright after she freezes mid-sentence.",
    "A cat spirit crosses the hallway unnoticed by everyone except Sakura.",
    "Rain hits the clubroom windows while they sort old yearbooks.",
    "Sakura runs across the school rooftop while Ken follows her.",
    "The festival lanterns blur as the flow between the crowd tightens.",
    "Ken sketches the night train from the platform bench.",
    "A thread snaps during argument — the first visible break.",
    "Sakura's mother pretends not to see the glow on the kitchen table.",
    "Empty desks after last bell. Wind turns the leftover worksheets.",
]


def _dt(days: int, hour: int = 18) -> datetime:
    base = datetime(2026, 9, 2, hour, 0, tzinfo=timezone.utc)
    return base + timedelta(days=days)


def _svg(title: str, subtitle: str, hue: int) -> bytes:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="hsl({hue},42%,18%)"/>
      <stop offset="100%" stop-color="hsl({hue + 30},36%,10%)"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#g)"/>
  <text x="64" y="320" fill="#f4efe6" font-size="42" font-family="Georgia">{title}</text>
  <text x="64" y="380" fill="#c9bfae" font-size="22" font-family="Georgia">{subtitle}</text>
  <text x="64" y="660" fill="#8b8376" font-size="16">Northwind Animation — original production board</text>
</svg>""".encode()


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count(User.id))) or 0
    if count:
        return
    seed_demo(db)


def seed_demo(db: Session) -> None:
    settings = get_settings()
    password = hash_password(settings.demo_password)

    admin = User(
        email="admin@aniflow.ai",
        hashed_password=password,
        full_name="Yuna Sato",
        role=UserRole.ADMIN,
        avatar_color="#7C9CFF",
    )
    manager = User(
        email="manager@aniflow.ai",
        hashed_password=password,
        full_name="Hana Mori",
        role=UserRole.PRODUCTION_MANAGER,
        avatar_color="#F0A05A",
    )
    director = User(
        email="director@aniflow.ai",
        hashed_password=password,
        full_name="Kenji Hayashi",
        role=UserRole.DIRECTOR,
        avatar_color="#E85D4C",
    )
    reviewer = User(
        email="reviewer@aniflow.ai",
        hashed_password=password,
        full_name="Rina Okabe",
        role=UserRole.REVIEWER,
        avatar_color="#3DDC97",
    )
    db.add_all([admin, manager, director, reviewer])
    db.flush()

    artist_specs = [
        ("Aki Tanaka", "artist@aniflow.ai", ArtistRole.KEY_ANIMATOR, ["key animation", "action", "rooftop"], ExperienceLevel.SENIOR, Availability.BUSY, "#FF7A59"),
        ("Mika Fujii", "mika@aniflow.ai", ArtistRole.BACKGROUND_ARTIST, ["backgrounds", "schools", "dusk"], ExperienceLevel.MID, Availability.AVAILABLE, "#7C9CFF"),
        ("Ren Saito", "ren@aniflow.ai", ArtistRole.ANIMATOR, ["in-between", "walk cycles", "crowds"], ExperienceLevel.MID, Availability.OVERLOADED, "#FF5C7A"),
        ("Sora Nishida", "sora@aniflow.ai", ArtistRole.COLOR_ARTIST, ["coloring", "sunset palettes"], ExperienceLevel.MID, Availability.AVAILABLE, "#F5C451"),
        ("Yuki Endo", "yuki@aniflow.ai", ArtistRole.COMPOSITOR, ["compositing", "glow", "particles"], ExperienceLevel.SENIOR, Availability.BUSY, "#A78BFA"),
        ("Nao Ishikawa", "nao@aniflow.ai", ArtistRole.STORYBOARD_ARTIST, ["storyboard", "pacing"], ExperienceLevel.LEAD, Availability.AVAILABLE, "#2DD4BF"),
        ("Toma Kawai", "toma@aniflow.ai", ArtistRole.CHARACTER_DESIGNER, ["character design", "sakura", "uniforms"], ExperienceLevel.SENIOR, Availability.AVAILABLE, "#FB7185"),
        ("Emi Hoshino", "emi@aniflow.ai", ArtistRole.COLOR_ARTIST, ["coloring", "night scenes"], ExperienceLevel.JUNIOR, Availability.AVAILABLE, "#86EFAC"),
        ("Haru Watanabe", "haru@aniflow.ai", ArtistRole.ANIMATOR, ["animation", "subtle acting"], ExperienceLevel.MID, Availability.BUSY, "#93C5FD"),
        ("Lio Arai", "lio@aniflow.ai", ArtistRole.KEY_ANIMATOR, ["key animation", "effects", "wind"], ExperienceLevel.SENIOR, Availability.AVAILABLE, "#FDBA74"),
    ]
    artists: list[User] = []
    for name, email, role, skills, exp, avail, color in artist_specs:
        user = User(
            email=email,
            hashed_password=password,
            full_name=name,
            role=UserRole.ARTIST,
            avatar_color=color,
        )
        db.add(user)
        db.flush()
        db.add(
            ArtistProfile(
                user_id=user.id,
                artist_role=role,
                skills=json.dumps(skills),
                experience_level=exp,
                availability=avail,
                avg_completion_hours=7.5 if exp in {ExperienceLevel.SENIOR, ExperienceLevel.LEAD} else 10,
            )
        )
        artists.append(user)
    aki, mika, ren, sora, yuki, nao, toma, emi, haru, lio = artists

    project = Project(
        name="Project Sakura",
        description=(
            "Original coming-of-age series about Sakura Amane, a first-year who can see the "
            "'flow' — luminous threads that connect people. When a thread snaps at school, "
            "she and her classmate Ken Amemiya try to repair it before summer ends."
        ),
        genre="Coming of age / supernatural slice of life",
        studio="Northwind Animation",
        director_id=director.id,
        production_manager_id=manager.id,
        start_date=date(2026, 3, 2),
        target_completion_date=date(2026, 11, 20),
        episode_count=12,
        status=ProjectStatus.PRODUCTION,
    )
    db.add(project)
    db.flush()

    chars = [
        Character(project_id=project.id, name="Sakura Amane", description="First-year who can see the flow between people.", role="protagonist"),
        Character(project_id=project.id, name="Ken Amemiya", description="Quiet classmate who sketches trains and rooftops.", role="deuteragonist"),
        Character(project_id=project.id, name="Natsu", description="Cat-shaped spirit that follows broken threads.", role="supporting"),
        Character(project_id=project.id, name="Mrs. Amane", description="Sakura's mother, a night-shift nurse.", role="supporting"),
        Character(project_id=project.id, name="Principal Iida", description="Keeps the old observatory locked.", role="supporting"),
    ]
    db.add_all(chars)
    db.flush()
    sakura_c, ken_c, natsu_c, mom_c, prin_c = chars

    episodes: dict[int, Episode] = {}
    for number, title, status, progress in EPISODE_META:
        ep = Episode(
            project_id=project.id,
            number=number,
            title=title,
            description=f"Episode {number:02d} of Project Sakura — {title}.",
            target_release_date=date(2026, 10, 3) + timedelta(days=(number - 1) * 7),
            status=status,
            progress=progress,
            director_id=director.id,
            production_manager_id=manager.id,
        )
        db.add(ep)
        db.flush()
        episodes[number] = ep

    stage_artists = {
        ProductionStage.STORYBOARD: nao,
        ProductionStage.LAYOUT: haru,
        ProductionStage.KEY_ANIMATION: aki,
        ProductionStage.IN_BETWEEN: ren,
        ProductionStage.BACKGROUND: mika,
        ProductionStage.COLORING: sora,
        ProductionStage.COMPOSITING: yuki,
        ProductionStage.QC: haru,
        ProductionStage.COMPLETED: aki,
        ProductionStage.SCRIPT: nao,
    }

    scenes_by_number: dict[int, Scene] = {}
    for ep_no, numbers in SCENE_RANGES.items():
        ep = episodes[ep_no]
        default_stage = EPISODE_STAGE[ep_no]
        for idx, scene_no in enumerate(numbers):
            stage = default_stage
            # Episode 5 compositing mix; scene 042 still in animation for the demo walkthrough
            if scene_no == 42:
                stage = ProductionStage.KEY_ANIMATION
            elif ep_no == 5 and scene_no in {43, 44}:
                stage = ProductionStage.QC
            elif ep_no == 6 and idx < 4:
                stage = ProductionStage.IN_BETWEEN
            elif ep_no == 7:
                stage = ProductionStage.KEY_ANIMATION if idx < 14 else ProductionStage.LAYOUT
            elif ep_no == 4 and idx >= 8:
                stage = ProductionStage.COMPLETED

            if stage == ProductionStage.COMPLETED:
                status = SceneStatus.COMPLETED
                deadline = _dt(-20 + (scene_no % 5))
                assigned = aki if scene_no % 2 else haru
            elif stage == ProductionStage.KEY_ANIMATION:
                status = SceneStatus.IN_PROGRESS
                deadline = _dt(-2 + (idx % 8))
                assigned = ren if ep_no == 7 and idx % 3 != 0 else aki
                if ep_no == 7 and idx % 5 == 0:
                    assigned = haru
            elif stage == ProductionStage.STORYBOARD:
                status = SceneStatus.IN_PROGRESS
                deadline = _dt(10 + idx)
                assigned = nao
            elif stage == ProductionStage.SCRIPT:
                status = SceneStatus.BACKLOG
                deadline = _dt(24 + idx)
                assigned = None
            else:
                status = SceneStatus.IN_PROGRESS
                deadline = _dt(4 + idx)
                assigned = stage_artists.get(stage)

            if scene_no == 42:
                assigned = aki
                deadline = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)
                status = SceneStatus.REVISION

            beat = SCENE_BEATS[scene_no % len(SCENE_BEATS)]
            if scene_no == 42:
                beat = "Sakura runs across the school rooftop while Ken follows her."

            scene = Scene(
                episode_id=ep.id,
                scene_number=scene_no,
                description=beat,
                location=LOCATIONS[scene_no % len(LOCATIONS)],
                props=json.dumps(["school bag", "sketchbook"] if scene_no % 3 else ["lantern", "umbrella"]),
                duration_seconds=8 + (scene_no % 12),
                complexity=2 + (scene_no % 4),
                priority=Priority.HIGH if scene_no in {42, 70, 71, 72} or ep_no == 7 else (Priority.MEDIUM if scene_no % 4 else Priority.LOW),
                assigned_artist_id=assigned.id if assigned else None,
                deadline=deadline,
                status=status,
                production_stage=stage,
                revision_count=3 if scene_no == 42 else (1 if scene_no % 11 == 0 else 0),
                progress=stage_progress(stage),
            )
            db.add(scene)
            db.flush()
            chosen_chars = [sakura_c]
            if scene_no % 2 == 0:
                chosen_chars.append(ken_c)
            if scene_no % 5 == 0:
                chosen_chars.append(natsu_c)
            if "kitchen" in scene.location.lower():
                chosen_chars.append(mom_c)
            scene.characters = chosen_chars
            scenes_by_number[scene_no] = scene

            if assigned:
                db.add(
                    Assignment(
                        scene_id=scene.id,
                        artist_id=assigned.id,
                        assigned_by_id=manager.id,
                        notes="Seed assignment",
                    )
                )

    db.flush()
    scene042 = scenes_by_number[42]

    # Tasks — give Ren a crushing load, Aki a high load, Mika a moderate load
    def add_task(**kwargs):
        db.add(Task(**kwargs))

    for scene_no, scene in scenes_by_number.items():
        if scene.assigned_artist_id and scene.production_stage != ProductionStage.COMPLETED:
            overdue = scene.deadline.date() < date(2026, 9, 2) if scene.deadline else False
            add_task(
                project_id=project.id,
                episode_id=scene.episode_id,
                scene_id=scene.id,
                title=f"{scene.display_id} — {scene.production_stage.value.replace('_', ' ')}",
                description=scene.description,
                type={
                    ProductionStage.STORYBOARD: TaskType.STORYBOARD,
                    ProductionStage.KEY_ANIMATION: TaskType.KEY_ANIMATION,
                    ProductionStage.IN_BETWEEN: TaskType.IN_BETWEEN,
                    ProductionStage.BACKGROUND: TaskType.BACKGROUND,
                    ProductionStage.COLORING: TaskType.COLORING,
                    ProductionStage.COMPOSITING: TaskType.COMPOSITING,
                    ProductionStage.QC: TaskType.QC,
                    ProductionStage.LAYOUT: TaskType.LAYOUT,
                }.get(scene.production_stage, TaskType.GENERAL),
                priority=scene.priority,
                status=TaskStatus.REVISION if scene_no == 42 else (TaskStatus.IN_PROGRESS if not overdue else TaskStatus.IN_PROGRESS),
                assignee_id=scene.assigned_artist_id,
                start_date=date(2026, 8, 20),
                deadline=scene.deadline.date() if scene.deadline else date(2026, 9, 20),
                estimated_hours=6 if scene.assigned_artist_id != ren.id else 5,
                actual_hours=2,
            )

    # Extra tasks on Ren to push workload over 100%
    for i in range(6):
        add_task(
            project_id=project.id,
            episode_id=episodes[7].id,
            scene_id=scenes_by_number[65 + i].id,
            title=f"Cleanup pass — crowd {i + 1}",
            description="In-between cleanup for Episode 07 crowd shots.",
            type=TaskType.IN_BETWEEN,
            priority=Priority.HIGH,
            status=TaskStatus.TODO,
            assignee_id=ren.id,
            start_date=date(2026, 8, 28),
            deadline=date(2026, 9, 1) if i < 3 else date(2026, 9, 5),
            estimated_hours=8,
        )

    add_task(
        project_id=project.id,
        episode_id=episodes[5].id,
        scene_id=scene042.id,
        title="SCN-042 rooftop key animation",
        description=" sakura rooftop run — keys and follow-through on hair/skirt.",
        type=TaskType.KEY_ANIMATION,
        priority=Priority.HIGH,
        status=TaskStatus.REVISION,
        assignee_id=aki.id,
        start_date=date(2026, 8, 18),
        deadline=date(2026, 9, 8),
        estimated_hours=12,
        actual_hours=9,
    )

    db.flush()

    # Scene 042 file versions
    asset = FileAsset(
        project_id=project.id,
        scene_id=scene042.id,
        kind=FileKind.ANIMATION_PREVIEW,
        original_name="scene_042_rooftop.svg",
        uploaded_by_id=aki.id,
    )
    db.add(asset)
    db.flush()
    version_notes = [
        (1, "v01", "First keys. Timing feels late on the turn.", ReviewStatus.REVISION_REQUIRED, -18),
        (2, "v02", "Adjusted run cycle. Hand still clips the railing.", ReviewStatus.REVISION_REQUIRED, -10),
        (3, "v03", "Hair overlap improved. Awaiting director notes.", ReviewStatus.PENDING, -2),
    ]
    versions: list[FileVersion] = []
    for num, label, notes, rstatus, days in version_notes:
        filename = f"scene_042_{label}.svg"
        relative = storage.save(
            relative_dir=f"scenes/{scene042.id}",
            filename=filename,
            data=_svg(f"SCN-042 {label}", "Rooftop run — Sakura & Ken", 18 + num * 12),
        )
        ver = FileVersion(
            file_id=asset.id,
            scene_id=scene042.id,
            version_number=num,
            label=label,
            storage_path=relative,
            mime_type="image/svg+xml",
            size_bytes=len(_svg("x", "y", 1)),
            notes=notes,
            artist_id=aki.id,
            review_status=rstatus,
        )
        db.add(ver)
        db.flush()
        ver.created_at = _dt(days, 11)
        versions.append(ver)

    # Additional storyboard file for ep 8
    board_scene = scenes_by_number[81]
    board_asset = FileAsset(
        project_id=project.id,
        scene_id=board_scene.id,
        kind=FileKind.STORYBOARD,
        original_name="ep08_board_01.svg",
        uploaded_by_id=nao.id,
    )
    db.add(board_asset)
    db.flush()
    path = storage.save(
        relative_dir=f"scenes/{board_scene.id}",
        filename="scene_081_v01.svg",
        data=_svg("SCN-081 v01", "Letters in the rain — board", 200),
    )
    db.add(
        FileVersion(
            file_id=board_asset.id,
            scene_id=board_scene.id,
            version_number=1,
            label="v01",
            storage_path=path,
            mime_type="image/svg+xml",
            notes="First pass boards.",
            artist_id=nao.id,
            review_status=ReviewStatus.PENDING,
        )
    )

    r1 = Review(
        scene_id=scene042.id,
        file_version_id=versions[0].id,
        reviewer_id=reviewer.id,
        status=ReviewStatus.REVISION_REQUIRED,
        comments="Character hand position is incorrect on the railing grab.",
    )
    r2 = Review(
        scene_id=scene042.id,
        file_version_id=versions[1].id,
        reviewer_id=reviewer.id,
        status=ReviewStatus.REVISION_REQUIRED,
        comments="Hand still intersects the railing. Please correct and resubmit.",
    )
    r3 = Review(
        scene_id=scene042.id,
        file_version_id=versions[2].id,
        reviewer_id=reviewer.id,
        status=ReviewStatus.PENDING,
        comments="Holding for director pass.",
    )
    db.add_all([r1, r2, r3])
    db.flush()

    db.add(
        RevisionRequest(
            scene_id=scene042.id,
            review_id=r2.id,
            issue="Character hand position is incorrect.",
            priority=Priority.HIGH,
            comment="Please correct the hand position and resubmit.",
            assigned_to_id=aki.id,
            created_by_id=reviewer.id,
            status=RevisionStatus.OPEN,
        )
    )
    db.add(
        Comment(
            scene_id=scene042.id,
            user_id=director.id,
            body="Keep Sakura's eyeline on the west stairwell — that's where the thread leads.",
        )
    )
    db.add(
        Comment(
            scene_id=scene042.id,
            user_id=aki.id,
            body="Will fix the hand on v04 and push hair overlap one frame later.",
        )
    )

    # Milestones
    for ep in episodes.values():
        db.add(
            ProductionMilestone(
                project_id=project.id,
                episode_id=ep.id,
                title=f"Episode {ep.number:02d} lock",
                due_date=datetime.combine(ep.target_release_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                type="episode_deadline",
                status="completed" if ep.status == EpisodeStatus.COMPLETED else "upcoming",
            )
        )
    db.add(
        ProductionMilestone(
            project_id=project.id,
            episode_id=episodes[7].id,
            scene_id=scenes_by_number[70].id,
            title="Episode 07 animation gate",
            due_date=_dt(5),
            type="milestone",
            status="at_risk",
        )
    )
    db.add(
        ProductionMilestone(
            project_id=project.id,
            episode_id=episodes[5].id,
            scene_id=scene042.id,
            title="SCN-042 revision due",
            due_date=datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc),
            type="revision",
            status="upcoming",
        )
    )

    # Risk assessments
    risks = [
        (4, 41, RiskLevel.LOW, 1, {"deadline_pressure": 30, "artist_workload": 40, "revision_rate": 25, "incomplete_scenes": 20}),
        (6, 58, RiskLevel.MEDIUM, 2, {"deadline_pressure": 55, "artist_workload": 70, "revision_rate": 35, "incomplete_scenes": 52}),
        (7, 82, RiskLevel.HIGH, 4, {"deadline_pressure": 80, "artist_workload": 92, "revision_rate": 48, "incomplete_scenes": 78}),
        (8, 36, RiskLevel.LOW, 0, {"deadline_pressure": 25, "artist_workload": 40, "revision_rate": 10, "incomplete_scenes": 88}),
    ]
    for ep_no, score, level, delay, factors in risks:
        recs = []
        if ep_no == 7:
            recs = [
                "Reassign 3 medium-priority Episode 07 scenes (manager approval required).",
                "Protect Aki's rooftop shots; do not pile additional keys onto Ren.",
            ]
        db.add(
            RiskAssessment(
                project_id=project.id,
                episode_id=episodes[ep_no].id,
                risk_score=score,
                risk_level=level,
                factors=json.dumps(factors),
                recommendations=json.dumps(recs or ["Maintain current plan."]),
                predicted_delay_days=f"{delay}–{delay + 2}" if delay else "0",
            )
        )
        db.add(
            AIAnalysis(
                project_id=project.id,
                episode_id=episodes[ep_no].id,
                analysis_type="risk",
                payload=json.dumps({"risk_score": score, "risk_level": level.value, "factors": factors}),
                summary=f"Episode {ep_no:02d} risk {score}/100 ({level.value})",
                requires_approval=ep_no == 7,
            )
        )

    db.add(
        AIAnalysis(
            project_id=project.id,
            episode_id=episodes[7].id,
            analysis_type="bottleneck",
            payload=json.dumps(
                {
                    "stage": "key_animation",
                    "reason": "14 scenes are waiting for animation on Episode 07.",
                    "artist_workload": 105,
                    "predicted_delay": "3–5 days",
                    "recommended_action": "Reassign 3 medium-priority scenes to Lio Arai.",
                    "requires_manager_approval": True,
                }
            ),
            summary="Episode 07 key animation queue",
            requires_approval=True,
        )
    )

    notifications = [
        (manager.id, NotificationType.AI_RISK_DETECTED, "Episode 07 has entered high-risk status.", "Risk score 82/100. Animation queue is blocking the lock date.", "episode", episodes[7].id),
        (aki.id, NotificationType.REVISION_REQUESTED, "Revision requested for Scene 042.", "Hand position on the rooftop railing is incorrect.", "scene", scene042.id),
        (aki.id, NotificationType.DEADLINE_APPROACHING, "Scene 042 is due September 8.", "Rooftop run keys need a clean resubmit.", "scene", scene042.id),
        (ren.id, NotificationType.TASK_OVERDUE, "You have overdue cleanup passes.", "Three Episode 07 crowd cleanups were due September 1.", "episode", episodes[7].id),
        (reviewer.id, NotificationType.TASK_ASSIGNED, "SCN-042 v03 is ready for review.", "Aki submitted an updated rooftop preview.", "scene", scene042.id),
        (director.id, NotificationType.EPISODE_MILESTONE, "Episodes 01–03 are locked.", "Festival arc is complete. Focus shifts to the rooftop/flow break.", "project", project.id),
        (manager.id, NotificationType.TASK_OVERDUE, "Several Episode 07 scenes are overdue.", "12 scenes are waiting on key animation.", "episode", episodes[7].id),
    ]
    for uid, ntype, title, message, et, eid in notifications:
        db.add(
            Notification(
                user_id=uid,
                type=ntype,
                title=title,
                message=message,
                related_entity_type=et,
                related_entity_id=eid,
            )
        )

    for ep in episodes.values():
        recompute_episode_progress(db, ep)

    db.commit()

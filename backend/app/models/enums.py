import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    DIRECTOR = "director"
    ARTIST = "artist"
    REVIEWER = "reviewer"


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    POST_PRODUCTION = "post_production"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class EpisodeStatus(str, enum.Enum):
    PLANNING = "planning"
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    ANIMATION = "animation"
    POST_PRODUCTION = "post_production"
    QC = "qc"
    COMPLETED = "completed"


class SceneStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    COMPLETED = "completed"


class ProductionStage(str, enum.Enum):
    SCRIPT = "script"
    STORYBOARD = "storyboard"
    LAYOUT = "layout"
    KEY_ANIMATION = "key_animation"
    IN_BETWEEN = "in_between"
    BACKGROUND = "background"
    COLORING = "coloring"
    COMPOSITING = "compositing"
    QC = "qc"
    COMPLETED = "completed"


class KanbanColumn(str, enum.Enum):
    BACKLOG = "backlog"
    STORYBOARD = "storyboard"
    ANIMATION = "animation"
    COLOR = "color"
    COMPOSITING = "compositing"
    QC = "qc"
    COMPLETED = "completed"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    COMPLETED = "completed"


class TaskType(str, enum.Enum):
    STORYBOARD = "storyboard"
    LAYOUT = "layout"
    KEY_ANIMATION = "key_animation"
    IN_BETWEEN = "in_between"
    BACKGROUND = "background"
    COLORING = "coloring"
    COMPOSITING = "compositing"
    QC = "qc"
    REVISION = "revision"
    GENERAL = "general"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArtistRole(str, enum.Enum):
    ANIMATOR = "animator"
    KEY_ANIMATOR = "key_animator"
    BACKGROUND_ARTIST = "background_artist"
    COLOR_ARTIST = "color_artist"
    COMPOSITOR = "compositor"
    STORYBOARD_ARTIST = "storyboard_artist"
    CHARACTER_DESIGNER = "character_designer"
    SOUND_DESIGNER = "sound_designer"
    EDITOR = "editor"
    OTHER = "other"


class ExperienceLevel(str, enum.Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class Availability(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFF = "off"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    REJECTED = "rejected"


class RevisionStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FileKind(str, enum.Enum):
    STORYBOARD = "storyboard"
    CHARACTER_SHEET = "character_sheet"
    BACKGROUND = "background"
    ANIMATION_PREVIEW = "animation_preview"
    AUDIO = "audio"
    SCENE_RENDER = "scene_render"
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, enum.Enum):
    TASK_ASSIGNED = "task_assigned"
    DEADLINE_APPROACHING = "deadline_approaching"
    TASK_OVERDUE = "task_overdue"
    REVISION_REQUESTED = "revision_requested"
    SCENE_APPROVED = "scene_approved"
    EPISODE_MILESTONE = "episode_milestone"
    AI_RISK_DETECTED = "ai_risk_detected"


class MilestoneType(str, enum.Enum):
    EPISODE_DEADLINE = "episode_deadline"
    SCENE_DEADLINE = "scene_deadline"
    REVIEW = "review"
    REVISION = "revision"
    MILESTONE = "milestone"


STAGE_TO_KANBAN = {
    ProductionStage.SCRIPT: KanbanColumn.BACKLOG,
    ProductionStage.STORYBOARD: KanbanColumn.STORYBOARD,
    ProductionStage.LAYOUT: KanbanColumn.ANIMATION,
    ProductionStage.KEY_ANIMATION: KanbanColumn.ANIMATION,
    ProductionStage.IN_BETWEEN: KanbanColumn.ANIMATION,
    ProductionStage.BACKGROUND: KanbanColumn.COLOR,
    ProductionStage.COLORING: KanbanColumn.COLOR,
    ProductionStage.COMPOSITING: KanbanColumn.COMPOSITING,
    ProductionStage.QC: KanbanColumn.QC,
    ProductionStage.COMPLETED: KanbanColumn.COMPLETED,
}

KANBAN_TO_STAGE = {
    KanbanColumn.BACKLOG: ProductionStage.SCRIPT,
    KanbanColumn.STORYBOARD: ProductionStage.STORYBOARD,
    KanbanColumn.ANIMATION: ProductionStage.KEY_ANIMATION,
    KanbanColumn.COLOR: ProductionStage.COLORING,
    KanbanColumn.COMPOSITING: ProductionStage.COMPOSITING,
    KanbanColumn.QC: ProductionStage.QC,
    KanbanColumn.COMPLETED: ProductionStage.COMPLETED,
}

PRODUCTION_STAGES = list(ProductionStage)

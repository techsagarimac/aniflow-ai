from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai import Notification
from app.models.enums import NotificationType


def notify(
    db: Session,
    *,
    user_id: int,
    ntype: NotificationType,
    title: str,
    message: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> Notification:
    item = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        message=message,
        related_entity_type=entity_type,
        related_entity_id=entity_id,
    )
    db.add(item)
    return item

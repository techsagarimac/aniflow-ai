from fastapi import APIRouter

from app.api.routes import (
    ai,
    analytics,
    artists,
    auth,
    dashboard,
    episodes,
    files,
    notifications,
    projects,
    reviews,
    scenes,
    tasks,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(episodes.router)
api_router.include_router(scenes.router)
api_router.include_router(tasks.router)
api_router.include_router(artists.router)
api_router.include_router(reviews.router)
api_router.include_router(files.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(ai.router)

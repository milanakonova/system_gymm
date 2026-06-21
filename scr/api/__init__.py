from fastapi import APIRouter

from scr.api.gym_operations import router as gym_router
from scr.api.locker import router as locker_router

main_router = APIRouter(prefix="/api", tags=["main"])
main_router.include_router(locker_router)
main_router.include_router(gym_router)


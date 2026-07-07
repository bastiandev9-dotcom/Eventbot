"""
EventBot API v1
===============
Aggregator semua router v1.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .events import router as events_router
from .tickets import router as tickets_router
from .registrations import router as registrations_router
from .chatbot import router as chatbot_router
from .admin import router as admin_router
from .knowledge_base import router as knowledge_base_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(events_router)
router.include_router(tickets_router)
router.include_router(registrations_router)
router.include_router(chatbot_router)
router.include_router(admin_router)
router.include_router(knowledge_base_router)

__all__ = ["router"]

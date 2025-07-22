"""v1 API Router."""

from fastapi import APIRouter

from super_agent.api.agent.router import router as agent_router

router = APIRouter(prefix="/v1")
router.include_router(agent_router)
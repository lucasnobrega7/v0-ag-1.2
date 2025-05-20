from fastapi import APIRouter
from .agents import router as agents_router
from .chat import router as chat_router
from .webhooks import router as webhooks_router
from .users import router as users_router
from .integrations import router as integrations_router

# Criar router principal
api_router = APIRouter()

# Incluir sub-routers
api_router.include_router(agents_router)
api_router.include_router(chat_router)
api_router.include_router(webhooks_router)
api_router.include_router(users_router)
api_router.include_router(integrations_router)

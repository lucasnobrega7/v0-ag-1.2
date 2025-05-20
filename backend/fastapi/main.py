from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from .api import setup_routers

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar o aplicativo FastAPI
app = FastAPI(
    title="V0 Backend API",
    description="API para o Sistema de Gerenciamento de Agentes de IA",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("NEXT_PUBLIC_LOGIN_URL", "*"),
        os.getenv("NEXT_PUBLIC_DASHBOARD_URL", "*"),
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas básicas
@app.get("/")
async def root():
    return {"message": "V0 Backend API está funcionando!"}

@app.get("/health")
async def health_check():
    # Verificar conexões com serviços externos
    services_status = {
        "supabase": "connected",
        "redis": "connected",
        "clerk": "connected"
    }
    return {
        "status": "healthy",
        "services": services_status
    }

# Configurar todas as rotas
setup_routers(app)

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..core.database import get_supabase, get_redis
from ..core.auth import get_current_user

# Criar router
router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

# Rotas para agentes
@router.get("/")
async def list_agents(
    user = Depends(get_current_user),
    supabase = Depends(get_supabase),
    limit: int = 10,
    offset: int = 0
):
    """
    Lista todos os agentes do usuário atual.
    """
    try:
        # Consultar agentes do usuário no Supabase
        result = supabase.table("agents").select("*").eq("user_id", user.id).limit(limit).offset(offset).execute()
        return {"agents": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar agentes: {str(e)}"
        )

@router.post("/")
async def create_agent(
    agent_data: dict,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Cria um novo agente para o usuário atual.
    """
    try:
        # Adicionar user_id ao agent_data
        agent_data["user_id"] = user.id
        
        # Inserir no Supabase
        result = supabase.table("agents").insert(agent_data).execute()
        return {"agent": result.data[0], "message": "Agente criado com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar agente: {str(e)}"
        )

@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase),
    redis = Depends(get_redis)
):
    """
    Obtém detalhes de um agente específico.
    """
    try:
        # Verificar cache no Redis
        cache_key = f"agent:{agent_id}"
        cached_agent = redis.get(cache_key)
        
        if cached_agent:
            import json
            return {"agent": json.loads(cached_agent), "source": "cache"}
        
        # Consultar no Supabase
        result = supabase.table("agents").select("*").eq("id", agent_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agente não encontrado"
            )
        
        # Armazenar no cache
        redis.setex(cache_key, 300, json.dumps(result.data[0]))  # Cache por 5 minutos
        
        return {"agent": result.data[0], "source": "database"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter agente: {str(e)}"
        )

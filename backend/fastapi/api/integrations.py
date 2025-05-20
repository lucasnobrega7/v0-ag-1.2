from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..core.database import get_supabase, get_redis
from ..core.auth import get_current_user

# Criar router
router = APIRouter(
    prefix="/api/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)

# Rotas para integrações (WhatsApp, etc.)
@router.get("/")
async def list_integrations(
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Lista todas as integrações do usuário atual.
    """
    try:
        # Consultar integrações do usuário no Supabase
        result = supabase.table("integrations").select("*").eq("user_id", user.id).execute()
        return {"integrations": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar integrações: {str(e)}"
        )

@router.post("/whatsapp")
async def create_whatsapp_integration(
    integration_data: dict,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Cria uma nova integração com WhatsApp.
    """
    try:
        # Validar dados
        required_fields = ["name", "api_type", "api_url", "api_key"]
        for field in required_fields:
            if field not in integration_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Campo obrigatório ausente: {field}"
                )
        
        # Adicionar user_id e tipo
        integration_data["user_id"] = user.id
        integration_data["type"] = "whatsapp"
        
        # Inserir no Supabase
        result = supabase.table("integrations").insert(integration_data).execute()
        
        return {
            "message": "Integração com WhatsApp criada com sucesso",
            "integration": result.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar integração: {str(e)}"
        )

@router.get("/{integration_id}")
async def get_integration(
    integration_id: str,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Obtém detalhes de uma integração específica.
    """
    try:
        # Consultar no Supabase
        result = supabase.table("integrations").select("*").eq("id", integration_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integração não encontrada"
            )
        
        return {"integration": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter integração: {str(e)}"
        )

@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Remove uma integração específica.
    """
    try:
        # Verificar se a integração existe e pertence ao usuário
        result = supabase.table("integrations").select("*").eq("id", integration_id).eq("user_id", user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integração não encontrada"
            )
        
        # Excluir do Supabase
        supabase.table("integrations").delete().eq("id", integration_id).execute()
        
        return {"message": "Integração removida com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover integração: {str(e)}"
        )

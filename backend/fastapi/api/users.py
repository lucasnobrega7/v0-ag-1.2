from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..core.database import get_supabase
from ..core.auth import get_current_user

# Criar router
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Rotas para usuários
@router.get("/me")
async def get_current_user_info(
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Obtém informações do usuário atual.
    """
    try:
        # Consultar informações adicionais do usuário no Supabase
        result = supabase.table("users").select("*").eq("id", user.id).execute()
        
        if not result.data:
            # Se não existir no Supabase, criar registro básico
            user_data = {
                "id": user.id,
                "email": user.email_addresses[0].email_address if user.email_addresses else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at
            }
            
            supabase.table("users").insert(user_data).execute()
            
            return {
                "user_id": user.id,
                "email": user.email_addresses[0].email_address if user.email_addresses else None,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "profile": {}
            }
        
        # Combinar dados do Clerk e Supabase
        user_data = result.data[0]
        profile_data = user_data.get("profile", {})
        
        return {
            "user_id": user.id,
            "email": user.email_addresses[0].email_address if user.email_addresses else None,
            "name": f"{user.first_name} {user.last_name}".strip(),
            "profile": profile_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter informações do usuário: {str(e)}"
        )

@router.put("/profile")
async def update_user_profile(
    profile_data: dict,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """
    Atualiza o perfil do usuário atual.
    """
    try:
        # Verificar se o usuário existe no Supabase
        result = supabase.table("users").select("*").eq("id", user.id).execute()
        
        if not result.data:
            # Se não existir, criar registro básico
            user_data = {
                "id": user.id,
                "email": user.email_addresses[0].email_address if user.email_addresses else None,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at,
                "profile": profile_data
            }
            
            supabase.table("users").insert(user_data).execute()
        else:
            # Atualizar perfil
            supabase.table("users").update({"profile": profile_data}).eq("id", user.id).execute()
        
        return {
            "message": "Perfil atualizado com sucesso",
            "profile": profile_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar perfil: {str(e)}"
        )

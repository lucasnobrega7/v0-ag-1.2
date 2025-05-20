from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..core.database import get_supabase
from ..core.auth import get_current_user

# Criar router
router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"],
    responses={404: {"description": "Not found"}},
)

# Rotas para webhooks
@router.post("/clerk")
async def clerk_webhook(
    request_data: dict,
    supabase = Depends(get_supabase)
):
    """
    Webhook para eventos do Clerk.
    """
    try:
        # Extrair dados do evento
        event_type = request_data.get("type")
        data = request_data.get("data", {})
        
        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de evento não especificado"
            )
        
        # Processar eventos
        if event_type == "user.created":
            # Criar usuário no Supabase
            user_id = data.get("id")
            email = data.get("email_addresses", [{}])[0].get("email_address")
            
            if user_id and email:
                user_data = {
                    "id": user_id,
                    "email": email,
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "first_name": data.get("first_name"),
                    "last_name": data.get("last_name")
                }
                
                supabase.table("users").insert(user_data).execute()
                
                return {"message": "Usuário criado com sucesso"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dados de usuário incompletos"
                )
        
        elif event_type == "user.updated":
            # Atualizar usuário no Supabase
            user_id = data.get("id")
            
            if user_id:
                user_data = {
                    "updated_at": data.get("updated_at"),
                    "first_name": data.get("first_name"),
                    "last_name": data.get("last_name")
                }
                
                supabase.table("users").update(user_data).eq("id", user_id).execute()
                
                return {"message": "Usuário atualizado com sucesso"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de usuário não especificado"
                )
        
        elif event_type == "user.deleted":
            # Excluir usuário no Supabase
            user_id = data.get("id")
            
            if user_id:
                supabase.table("users").delete().eq("id", user_id).execute()
                
                return {"message": "Usuário excluído com sucesso"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID de usuário não especificado"
                )
        
        # Outros eventos
        return {"message": f"Evento {event_type} recebido, mas não processado"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar webhook: {str(e)}"
        )

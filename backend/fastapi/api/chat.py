from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..core.database import get_supabase, get_redis
from ..core.auth import get_current_user
import anthropic
import os

# Criar router
router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Inicializar cliente Anthropic
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Rotas para chat
@router.post("/")
async def create_chat_message(
    message_data: dict,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase),
    redis = Depends(get_redis)
):
    """
    Cria uma nova mensagem de chat e obtém resposta do agente.
    """
    try:
        # Extrair dados da mensagem
        agent_id = message_data.get("agent_id")
        content = message_data.get("content")
        
        if not agent_id or not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="agent_id e content são obrigatórios"
            )
        
        # Obter informações do agente
        agent_result = supabase.table("agents").select("*").eq("id", agent_id).eq("user_id", user.id).execute()
        
        if not agent_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agente não encontrado"
            )
        
        agent = agent_result.data[0]
        
        # Obter histórico de conversa
        conversation_key = f"conversation:{user.id}:{agent_id}"
        conversation_history = redis.get(conversation_key) or "[]"
        import json
        conversation = json.loads(conversation_history)
        
        # Adicionar mensagem do usuário
        conversation.append({"role": "user", "content": content})
        
        # Gerar resposta com Anthropic
        system_prompt = agent.get("system_prompt", "Você é um assistente útil.")
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation:
            messages.append(msg)
        
        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=messages
        )
        
        # Adicionar resposta do assistente
        assistant_message = {"role": "assistant", "content": response.content[0].text}
        conversation.append(assistant_message)
        
        # Salvar conversa atualizada
        redis.setex(conversation_key, 3600, json.dumps(conversation))  # Cache por 1 hora
        
        # Salvar mensagens no Supabase
        user_message = {
            "user_id": user.id,
            "agent_id": agent_id,
            "role": "user",
            "content": content
        }
        
        assistant_message_db = {
            "user_id": user.id,
            "agent_id": agent_id,
            "role": "assistant",
            "content": response.content[0].text
        }
        
        supabase.table("messages").insert([user_message, assistant_message_db]).execute()
        
        return {
            "message": "Mensagem processada com sucesso",
            "response": response.content[0].text
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )

@router.get("/history/{agent_id}")
async def get_chat_history(
    agent_id: str,
    user = Depends(get_current_user),
    supabase = Depends(get_supabase),
    limit: int = 50
):
    """
    Obtém o histórico de chat com um agente específico.
    """
    try:
        # Verificar se o agente existe e pertence ao usuário
        agent_result = supabase.table("agents").select("*").eq("id", agent_id).eq("user_id", user.id).execute()
        
        if not agent_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agente não encontrado"
            )
        
        # Obter mensagens
        messages_result = supabase.table("messages").select("*").eq("agent_id", agent_id).eq("user_id", user.id).order("created_at", desc=False).limit(limit).execute()
        
        return {"messages": messages_result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter histórico: {str(e)}"
        )

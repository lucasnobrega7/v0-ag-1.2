import os
from fastapi import Depends, HTTPException, status
from clerk_sdk_python import ClerkClient

# Configuração do Clerk
clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
clerk_webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")

# Inicialização do cliente Clerk
clerk_client = None

def initialize_clerk():
    global clerk_client
    
    # Inicializar Clerk
    if clerk_secret_key:
        clerk_client = ClerkClient(secret_key=clerk_secret_key)
    else:
        raise Exception("Variável de ambiente CLERK_SECRET_KEY não configurada")

# Dependência para injeção nos endpoints
def get_clerk():
    if not clerk_client:
        initialize_clerk()
    return clerk_client

# Funções de autenticação
async def validate_session_token(token: str):
    client = get_clerk()
    try:
        session = client.sessions.verify_token(token)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sessão inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(validate_session_token)):
    client = get_clerk()
    try:
        user = client.users.get(token.sub)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Verificação de webhook
def verify_webhook_signature(signature: str, body: bytes):
    import hmac
    import hashlib
    
    if not clerk_webhook_secret:
        raise Exception("Variável de ambiente CLERK_WEBHOOK_SECRET não configurada")
    
    computed_signature = hmac.new(
        clerk_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

import os
from fastapi import Depends, HTTPException, status
from supabase import create_client, Client
from redis import Redis
import json

# Configuração do Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

# Configuração do Redis
redis_url = os.getenv("REDIS_URL")

# Inicialização dos clientes
supabase: Client = None
redis_client: Redis = None

def initialize_clients():
    global supabase, redis_client
    
    # Inicializar Supabase
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
    else:
        raise Exception("Variáveis de ambiente do Supabase não configuradas")
    
    # Inicializar Redis
    if redis_url:
        redis_client = Redis.from_url(redis_url, decode_responses=True)
    else:
        raise Exception("Variável de ambiente REDIS_URL não configurada")

# Dependências para injeção nos endpoints
def get_supabase():
    if not supabase:
        initialize_clients()
    return supabase

def get_redis():
    if not redis_client:
        initialize_clients()
    return redis_client

# Funções auxiliares para Supabase
async def query_supabase(table, query=None):
    db = get_supabase()
    if query:
        result = db.table(table).select("*").execute()
    else:
        result = db.table(table).select("*").execute()
    return result.data

async def insert_supabase(table, data):
    db = get_supabase()
    result = db.table(table).insert(data).execute()
    return result.data

# Funções auxiliares para Redis
async def set_redis_key(key, value, expiration=None):
    r = get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    if expiration:
        r.setex(key, expiration, value)
    else:
        r.set(key, value)
    return True

async def get_redis_key(key):
    r = get_redis()
    value = r.get(key)
    try:
        return json.loads(value)
    except:
        return value

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

security = HTTPBearer(auto_error=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cdzidhmjduncdxauerut.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_MWpmReQE1qF7_qgcDms-1A_ZBcM-5Q1")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Initialize supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Simple memory cache to prevent rate-limiting from Supabase Auth API
# Maps token string to a tuple of (user_dict, timestamp)
_token_cache = {}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not SUPABASE_JWT_SECRET:
        # For local development without Supabase configured, bypass auth.
        return {"sub": "anonymous-dev-user"}
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    import time
    
    now = time.time()
    # Check cache (valid for 5 minutes)
    if token in _token_cache:
        cached_user, timestamp = _token_cache[token]
        if now - timestamp < 300:
            return cached_user
            
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        
        user_dict = {"sub": user_response.user.id, "email": user_response.user.email}
        # Save to cache
        _token_cache[token] = (user_dict, now)
        
        # Cleanup old cache entries occasionally
        if len(_token_cache) > 1000:
            keys_to_delete = [k for k, v in _token_cache.items() if now - v[1] > 300]
            for k in keys_to_delete:
                del _token_cache[k]
                
        return user_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
        )

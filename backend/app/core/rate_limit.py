# pyrefly: ignore [missing-import]
from slowapi import Limiter
# pyrefly: ignore [missing-import]
from slowapi.util import get_remote_address
from fastapi import Request
import os
from jose import jwt, JWTError

def get_user_id_or_ip(request: Request) -> str:
    """
    Custom key function for rate limiting.
    Uses the authenticated user ID if a valid JWT is present,
    otherwise falls back to the remote IP address.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        secret = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-replace-in-production")
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except JWTError:
            # Token is invalid or expired, fallback to IP
            pass
            
    # Fallback to IP address for unauthenticated requests
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_id_or_ip)

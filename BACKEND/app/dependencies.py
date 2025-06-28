# dependencies.py 
from fastapi import Header, HTTPException

def get_user_id(x_user_id: str = Header(..., description="Clerk user ID")):
    """
    Extract the Clerk user ID from X-User-Id header.
    In production, you’d verify a JWT; here we just trust the header.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header missing")
    return x_user_id

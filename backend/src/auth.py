import sys
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET, JWT_EXPIRY_HOURS
from src.logger import get_logger
from supabase import create_client

log = get_logger(__name__)
supabase = create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)

def hash_password(password:str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password:str,hashed:str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id:str,email:str) -> str:
    payload = {
        "sub": user_id,
        "email":email,
        "iat":datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token:str) -> dict:
    try:
        payload = jwt.decode(token,JWT_SECRET,algorithms=["HS256"])
        return {"valid": True, "user_id": payload["sub"], "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        return {"valid":False, "error": "Token epired"}
    except jwt.InvalidTokenError:
        return {"valid":False, "error": "Invalid Token"}

def register_user(email:str, password:str, full_name:str) -> dict:
    log.info(f"Register attempt :{email}")

    existing = supabase.table("users").select("id").eq("email",email).execute()
    if existing.data:
        log.warning(f"Register failed - email already exists: {email}")
        return {"success":False,"error":"Email already registered"}
    
    if len(password) < 8:
        return {"success": False, "error": "Password must be atleast 8 characters"}
    
    password_hash = hash_password(password)
    user = supabase.table("users").insert({
        "email":email,
        "password_hash":password_hash,
        "full_name":full_name
    }).execute()

    user_data = user.data[0]
    token = create_token(user_data["id"],email)

    log.info(f"User registered: {email}")
    return  {
        "success": True,
        "token": token,
        "user": {
            "id":user_data["id"],
            "email": email,
            "full_name": full_name
        }
    }

def login_user(email:str, password:str) -> dict:
    log.info(f"Login attempt: {email}")

    result = supabase.table("users").select("*").eq("email",email).execute()

    if not result.data:
        log.warning(f"Login failed - user not found: {email}")
        return {"success": False, "error": "Invalid email or password"}
    
    user  = result.data[0]
    if not verify_password(password,user["password_hash"]):
        log.warning(f"Login failed - wrong password: {email}")
        return {"success": False, "error": "Invalid email or password"}
    
    supabase.table("users").update({
        "last_login": datetime.now(timezone.utc).isoformat()
    }).eq("id",user["id"]).execute()

    token = create_token(user["id"],email)
    log.info(f"User logged in: {email}")

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "email": email,
            "full_name": user["full_name"]
        }
    }


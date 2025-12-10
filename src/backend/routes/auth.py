import os
import secrets
from fastapi import Request, HTTPException

# Compute absolute DB path relative to project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB = os.path.join(BASE_DIR, 'data', 'jessica.db')

try:
    from ..cloud.supabase_client import get_client
except ImportError:
    get_client = None

# We now use Supabase for Auth (or a 'tokens' table in Supabase if using API keys)
# For simplicity in this migration, we will check a 'tokens' table in Supabase
# mirroring the local logic, OR we can rely on Supabase Auth JWTs.
# Given the existing simple token structure, let's use a 'tokens' table in Supabase.


def _get_supa():
    return get_client() if get_client else None


def validate_token(token: str) -> bool:
    cli = _get_supa()
    if not cli:
        return False  # Fail safe
    try:
        # Check 'tokens' table in Supabase
        resp = cli.table("tokens").select("token").eq("token", token).execute()
        return len(resp.data) > 0
    except Exception:
        return False


def get_token_role(token: str) -> str | None:
    cli = _get_supa()
    if not cli:
        return None
    try:
        resp = cli.table("tokens").select("role").eq("token", token).execute()
        if resp.data:
            return resp.data[0].get("role")
    except Exception:
        pass
    return None


def make_token(role: str = "user") -> str:
    cli = _get_supa()
    if not cli:
        raise RuntimeError("No Cloud Connection")

    t = secrets.token_hex(32)
    try:
        cli.table("tokens").insert({
            "token": t,
            "role": role,
            # 'created_at' is auto
        }).execute()
        return t
    except Exception as e:
        print(f"Auth Error: {e}")
        return ""


def require_role(role: str):
    async def checker(request: Request):
        token = request.headers.get("Authorization") or request.headers.get("X-API-Token")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1]
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        r = get_token_role(token)
        if r is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # simple hierarchy: admin > user > skill (skill restricted)
        if role == "admin" and r != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        if role == "user" and r not in ("admin", "user"):
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

    return checker

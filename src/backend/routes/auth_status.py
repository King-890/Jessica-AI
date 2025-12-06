from fastapi import APIRouter, Request

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
async def auth_status(request: Request):
    """Report current identity inferred from request state.

    Returns:
    { source: 'supabase'|'dev'|'none', role: str|None, user_id: str|None }
    """
    role = getattr(request.state, "token_role", None)
    supa_user = getattr(request.state, "supabase_user", None)
    if supa_user:
        # supabase user carries id
        uid = getattr(supa_user, "id", None)
        return {"source": "supabase", "role": role, "user_id": uid}
    # If a dev token was validated it will carry a role, otherwise none
    if role:
        return {"source": "dev", "role": role, "user_id": None}
    return {"source": "none", "role": None, "user_id": None}
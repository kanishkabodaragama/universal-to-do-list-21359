from typing import Optional, Dict, Any
from fastapi import HTTPException
from src.services.supabase_client import SupabaseClient
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger()


class UserService:
    """Service to manage users via Supabase Auth and 'profiles' table."""

    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.settings = get_settings()
        # Table names (can be changed to match your Supabase schema)
        self.profiles_table = "profiles"

    async def register_user(self, email: str, password: str) -> Dict[str, Any]:
        redirect_to = f"{self.settings.SITE_URL}/auth/callback"
        try:
            result = await self.supabase.auth_sign_up(email=email, password=password, email_redirect_to=redirect_to)
        except Exception:
            raise HTTPException(status_code=400, detail="Registration failed")
        return result

    async def ensure_profile(self, auth_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure a row exists in the profiles table. The auth_result may include 'user' object.
        Fallback to email if id is missing.
        """
        user = auth_result.get("user") or auth_result
        user_id = user.get("id")
        email = user.get("email")
        if not email:
            # Some responses may have user under different key
            email = auth_result.get("email")
        if not email:
            raise HTTPException(status_code=500, detail="Auth result missing email")

        # Check existing profile
        rows = await self.supabase.select(self.profiles_table, "*", email=email)
        if rows:
            return rows[0]

        # Insert new profile
        to_insert = {"email": email}
        if user_id:
            to_insert["id"] = user_id
        inserted = await self.supabase.insert(self.profiles_table, [to_insert])
        if not inserted:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        return inserted[0]

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        auth = await self.supabase.auth_sign_in(email=email, password=password)
        if not auth:
            return None
        # Ensure profile exists
        prof = await self.get_user_by_email(email)
        if not prof:
            # Attempt to create profile with auth data if missing
            try:
                await self.ensure_profile(auth)
            except Exception:
                logger.warning("Profile creation post-login failed")
        return {"email": email, "id": auth.get("user", {}).get("id", "")}

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        rows = await self.supabase.select(self.profiles_table, "*", email=email)
        if rows:
            return rows[0]
        return None

    async def update_password(self, email: str, new_password: str) -> None:
        ok = await self.supabase.auth_update_user_password(email=email, new_password=new_password)
        if not ok:
            raise HTTPException(status_code=400, detail="Password update failed")

from typing import Any, Dict, List, Optional
import httpx
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger()


class SupabaseClient:
    """
    Minimal Supabase client wrapper using REST and Auth endpoints via httpx.
    Uses service role key for server-side operations.
    """

    def __init__(self, url: str, anon_key: str, service_role_key: str):
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.service_role_key = service_role_key
        self.rest_url = f"{self.url}/rest/v1"
        self.auth_url = f"{self.url}/auth/v1"
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self._client.aclose()

    # ---- Auth ----
    async def auth_sign_up(self, email: str, password: str, email_redirect_to: Optional[str] = None) -> Dict[str, Any]:
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"email": email, "password": password}
        if email_redirect_to:
            # Supabase expects options.emailRedirectTo
            payload["options"] = {"emailRedirectTo": email_redirect_to}
        resp = await self._client.post(f"{self.auth_url}/signup", headers=headers, json=payload)
        if resp.status_code >= 400:
            logger.error(f"Supabase signup error: {resp.status_code} {resp.text}")
            raise httpx.HTTPStatusError("Signup failed", request=resp.request, response=resp)
        return resp.json()

    async def auth_sign_in(self, email: str, password: str) -> Dict[str, Any]:
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        payload = {"email": email, "password": password}
        resp = await self._client.post(f"{self.auth_url}/token?grant_type=password", headers=headers, json=payload)
        if resp.status_code >= 400:
            logger.error(f"Supabase sign-in error: {resp.status_code} {resp.text}")
            return {}
        return resp.json()

    async def auth_update_user_password(self, email: str, new_password: str) -> bool:
        """
        Uses Admin endpoint with service role key to update a user's password.
        """
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        # Find user by email
        users_resp = await self._client.get(f"{self.auth_url}/admin/users", headers=headers, params={"email": email})
        if users_resp.status_code >= 400:
            logger.error(f"Admin users list error: {users_resp.status_code} {users_resp.text}")
            return False
        users = users_resp.json().get("users") or []
        if not users:
            logger.error("User not found for password update")
            return False
        user_id = users[0]["id"]
        update_resp = await self._client.put(
            f"{self.auth_url}/admin/users/{user_id}",
            headers=headers,
            json={"password": new_password},
        )
        if update_resp.status_code >= 400:
            logger.error(f"Admin user update error: {update_resp.status_code} {update_resp.text}")
        return update_resp.status_code < 400

    # ---- Database (REST) ----
    async def select(
        self, table: str, select: str = "*", **filters
    ) -> List[Dict[str, Any]]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        params = {"select": select}
        # Simple equality filters
        for k, v in filters.items():
            if v is None:
                continue
            params[k] = f"eq.{v}"
        resp = await self._client.get(f"{self.rest_url}/{table}", headers=headers, params=params)
        if resp.status_code >= 400:
            logger.error(f"Select error: {resp.status_code} {resp.text}")
            return []
        return resp.json()

    async def insert(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        resp = await self._client.post(f"{self.rest_url}/{table}", headers=headers, json=rows)
        if resp.status_code >= 400:
            logger.error(f"Insert error: {resp.status_code} {resp.text}")
            return []
        return resp.json()

    async def update(self, table: str, match_filters: Dict[str, Any], updates: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        params = {}
        for k, v in match_filters.items():
            params[k] = f"eq.{v}"
        resp = await self._client.patch(f"{self.rest_url}/{table}", headers=headers, params=params, json=updates)
        if resp.status_code >= 400:
            logger.error(f"Update error: {resp.status_code} {resp.text}")
            return []
        return resp.json()

    async def delete(self, table: str, match_filters: Dict[str, Any]) -> bool:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        params = {}
        for k, v in match_filters.items():
            params[k] = f"eq.{v}"
        resp = await self._client.delete(f"{self.rest_url}/{table}", headers=headers, params=params)
        if resp.status_code >= 400:
            logger.error(f"Delete error: {resp.status_code} {resp.text}")
            return False
        return True


# PUBLIC_INTERFACE
def get_supabase_client() -> SupabaseClient:
    """Create a SupabaseClient instance using environment settings."""
    settings = get_settings()
    return SupabaseClient(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, settings.SUPABASE_SERVICE_ROLE_KEY)

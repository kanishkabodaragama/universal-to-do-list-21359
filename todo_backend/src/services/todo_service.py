from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from src.services.supabase_client import SupabaseClient
from src.models.schemas import TodoCreate, TodoUpdate


class TodoService:
    """Service for CRUD operations on 'todos' table."""

    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.todos_table = "todos"

    async def create_todo(self, user_id: str, data: TodoCreate) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "title": data.title,
            "description": data.description,
            "completed": data.completed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        rows = await self.supabase.insert(self.todos_table, [payload])
        return rows[0] if rows else {}

    async def list_todos(self, user_id: str, completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        filters = {"user_id": user_id}
        if completed is not None:
            filters["completed"] = completed
        rows = await self.supabase.select(self.todos_table, "*", **filters)
        return rows

    async def get_todo(self, todo_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        rows = await self.supabase.select(self.todos_table, "*", id=todo_id, user_id=user_id)
        return rows[0] if rows else None

    async def update_todo(self, todo_id: str, user_id: str, data: TodoUpdate) -> Optional[Dict[str, Any]]:
        updates: Dict[str, Any] = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.description is not None:
            updates["description"] = data.description
        if data.completed is not None:
            updates["completed"] = data.completed
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        rows = await self.supabase.update(self.todos_table, {"id": todo_id, "user_id": user_id}, updates)
        return rows[0] if rows else None

    async def delete_todo(self, todo_id: str, user_id: str) -> bool:
        return await self.supabase.delete(self.todos_table, {"id": todo_id, "user_id": user_id})

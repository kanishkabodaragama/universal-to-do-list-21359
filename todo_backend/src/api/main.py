from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from starlette.responses import JSONResponse

from src.core.config import get_settings
from src.core.logging import get_logger
from src.services.supabase_client import get_supabase_client
from src.services.user_service import UserService
from src.services.todo_service import TodoService
from src.api.docs_info import get_docs_router
from src.models.schemas import (
    Token,
    TokenData,
    UserCreate,
    UserPublic,
    UserUpdatePassword,
    TodoCreate,
    TodoUpdate,
    TodoPublic,
)

# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance with CORS, routes, and metadata.
    """
    settings = get_settings()
    app = FastAPI(
        title="Universal ToDo Backend API",
        description="FastAPI backend for cross-platform todo app with Supabase integration.\n\nTheme: Ocean Professional",
        version="1.0.0",
        contact={"name": "Universal ToDo", "email": "support@example.com"},
        license_info={"name": "MIT"},
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        openapi_tags=[
            {"name": "health", "description": "Health and system endpoints"},
            {"name": "auth", "description": "User authentication: register, login, tokens"},
            {"name": "users", "description": "User profile and management"},
            {"name": "todos", "description": "CRUD operations for Todos"},
        ],
    )

    logger = get_logger()

    # Validate required configuration and log diagnostics
    missing = [name for name, ok in settings.validate_required() if not ok]
    if missing:
        logger.error(
            "Missing required environment variables: %s",
            ", ".join(missing),
        )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount docs helper router
    app.include_router(get_docs_router())

    # Security components
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/auth/token",
        scopes={"user": "Standard user access"}
    )
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Services
    supabase = get_supabase_client()
    user_service = UserService(supabase)
    todo_service = TodoService(supabase)

    # Utility functions
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def get_current_user(
        security_scopes: SecurityScopes,
        token: str = Depends(oauth2_scheme),
    ) -> UserPublic:
        """
        Resolve current user from JWT token and return public user model.
        Raises HTTP 401 if invalid/expired token.
        """
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            sub: str = payload.get("sub")
            if sub is None:
                raise credentials_exception
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(username=sub, scopes=token_scopes)
        except jwt.ExpiredSignatureError:
            logger.error("[Ocean:#2563EB] Token expired", extra={"color": "#EF4444"})
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.PyJWTError:
            logger.error("[Ocean:#2563EB] Token decode error", extra={"color": "#EF4444"})
            raise credentials_exception

        # Scope check (for future role-based access)
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=401,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )

        user = await user_service.get_user_by_email(token_data.username)
        if not user:
            raise credentials_exception
        return UserPublic(id=user["id"], email=user["email"], created_at=user.get("created_at"))

    @app.get("/", tags=["health"], summary="Health Check", description="Returns service health status and timestamp.")
    def health_check():
        cfg_status = {
            "SUPABASE_URL_set": bool(settings.SUPABASE_URL),
            "SUPABASE_ANON_KEY_set": bool(settings.SUPABASE_ANON_KEY),
            "SUPABASE_SERVICE_ROLE_KEY_set": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
            "JWT_secret_set": bool(settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "change-me"),
            "SITE_URL_set": bool(settings.SITE_URL),
        }
        return {"message": "Healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "config": cfg_status}

    @app.get(
        "/health/config",
        tags=["health"],
        summary="Configuration diagnostics",
        description="Returns configuration readiness flags for required environment variables (no secrets).",
    )
    def health_config():
        cfg_status = {
            "SUPABASE_URL_set": bool(settings.SUPABASE_URL),
            "SUPABASE_ANON_KEY_set": bool(settings.SUPABASE_ANON_KEY),
            "SUPABASE_SERVICE_ROLE_KEY_set": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
            "JWT_secret_set": bool(settings.JWT_SECRET_KEY and settings.JWT_SECRET_KEY != "change-me"),
            "JWT_algorithm_set": bool(settings.JWT_ALGORITHM),
            "SITE_URL_set": bool(settings.SITE_URL),
        }
        return {"config": cfg_status}

    @app.post(
        "/auth/register",
        tags=["auth"],
        response_model=UserPublic,
        status_code=201,
        summary="Register a new user",
        description="Registers a new user in Supabase Auth and creates a user profile record."
    )
    async def register_user(payload: UserCreate):
        # Create user in Supabase Auth via service
        try:
            auth_user = await user_service.register_user(email=payload.email, password=payload.password)
            # Create profile row (if using separate profile table)
            user_row = await user_service.ensure_profile(auth_user)
            return UserPublic(id=user_row["id"], email=user_row["email"], created_at=user_row.get("created_at"))
        except HTTPException:
            logger.error("[Ocean:#EF4444] Register error")
            raise
        except Exception:
            logger.exception("[Ocean:#EF4444] Unexpected register error")
            raise HTTPException(status_code=500, detail="Registration failed")

    @app.post(
        "/auth/token",
        tags=["auth"],
        response_model=Token,
        summary="Get access token",
        description="Login with email/password and receive a JWT access token."
    )
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        # Supabase Auth sign-in to verify credentials
        user = await user_service.authenticate_user(email=form_data.username, password=form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        access_token = create_access_token(
            data={"sub": user["email"], "scopes": ["user"]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return Token(access_token=access_token, token_type="bearer")

    @app.get(
        "/users/me",
        tags=["users"],
        response_model=UserPublic,
        summary="Get current user",
        description="Returns the current authenticated user's public profile."
    )
    async def read_users_me(current_user: UserPublic = Security(get_current_user, scopes=["user"])):
        return current_user

    @app.post(
        "/users/me/password",
        tags=["users"],
        status_code=204,
        summary="Update password",
        description="Updates the password of the current authenticated user via Supabase Auth."
    )
    async def update_password(
        payload: UserUpdatePassword,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        try:
            await user_service.update_password(email=current_user.email, new_password=payload.new_password)
        except HTTPException:
            raise
        except Exception:
            logger.exception("[Ocean:#EF4444] Unexpected password update error")
            raise HTTPException(status_code=500, detail="Password update failed")
        return JSONResponse(status_code=204, content=None)

    # Todos
    @app.post(
        "/todos",
        tags=["todos"],
        response_model=TodoPublic,
        status_code=201,
        summary="Create todo",
        description="Create a new todo item for the authenticated user."
    )
    async def create_todo(
        payload: TodoCreate,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        todo = await todo_service.create_todo(user_id=current_user.id, data=payload)
        return TodoPublic(**todo)

    @app.get(
        "/todos",
        tags=["todos"],
        response_model=List[TodoPublic],
        summary="List todos",
        description="List todos for the authenticated user. Supports optional filtering by 'completed'."
    )
    async def list_todos(
        completed: Optional[bool] = None,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        todos = await todo_service.list_todos(user_id=current_user.id, completed=completed)
        return [TodoPublic(**t) for t in todos]

    @app.get(
        "/todos/{todo_id}",
        tags=["todos"],
        response_model=TodoPublic,
        summary="Get todo",
        description="Get a single todo by its ID."
    )
    async def get_todo(
        todo_id: str,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        todo = await todo_service.get_todo(todo_id=todo_id, user_id=current_user.id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return TodoPublic(**todo)

    @app.put(
        "/todos/{todo_id}",
        tags=["todos"],
        response_model=TodoPublic,
        summary="Update todo",
        description="Update a todo by its ID."
    )
    async def update_todo(
        todo_id: str,
        payload: TodoUpdate,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        todo = await todo_service.update_todo(todo_id=todo_id, user_id=current_user.id, data=payload)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found or not owned by user")
        return TodoPublic(**todo)

    @app.delete(
        "/todos/{todo_id}",
        tags=["todos"],
        status_code=204,
        summary="Delete todo",
        description="Delete a todo by its ID."
    )
    async def delete_todo(
        todo_id: str,
        current_user: UserPublic = Security(get_current_user, scopes=["user"])
    ):
        deleted = await todo_service.delete_todo(todo_id=todo_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Todo not found or not owned by user")
        return JSONResponse(status_code=204, content=None)

    return app


# Instantiate for ASGI
app = create_app()

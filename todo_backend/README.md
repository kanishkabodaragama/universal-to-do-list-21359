# Universal ToDo Backend (FastAPI + Supabase)

Production-ready FastAPI backend providing:
- Auth: register, login (JWT), update password
- Todos: CRUD tied to authenticated user
- OpenAPI docs at `/docs`
- Ocean Professional themed logging

## Supabase configuration (required)

1) Set environment variables (see `.env.example`):
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - SUPABASE_SERVICE_ROLE_KEY
   - SITE_URL
   - JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
   - CORS_ALLOW_ORIGINS (comma-separated list)

2) In Supabase Dashboard:
   - Authentication > URL Configuration
     * Site URL: your deployment URL (e.g., https://yourapp.example.com)
     * Allowed Redirect URLs: 
       http://localhost:8000/**, http://localhost:3000/**, https://yourapp.example.com/**
   - Database > Table editor:
     * Ensure tables `profiles` and `todos` exist (auto-provisioned by this setup)
   - Database > Policies:
     * Ensure RLS is enabled and owner/service_role policies exist for profiles and todos (see assets/supabase.md)

3) Notes:
   - The backend uses service role key for server-side DB operations and Admin password updates.
   - Email redirects for signup go to `${SITE_URL}/auth/callback`.

## Run locally

1) Ensure environment variables are set (see `.env.example`).
2) Install dependencies:
   pip install -r requirements.txt
3) Start API:
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

## OpenAPI JSON
Regenerate interfaces/openapi.json by running:
   python -m src.api.generate_openapi

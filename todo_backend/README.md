# Universal ToDo Backend (FastAPI + Supabase)

Production-ready FastAPI backend providing:
- Auth: register, login (JWT), update password
- Todos: CRUD tied to authenticated user
- OpenAPI docs at `/docs`
- Ocean Professional themed logging

## Run locally

1) Ensure environment variables are set (see `.env.example`).
2) Install dependencies:
   pip install -r requirements.txt
3) Start API:
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

## OpenAPI JSON
Regenerate interfaces/openapi.json by running:
   python -m src.api.generate_openapi

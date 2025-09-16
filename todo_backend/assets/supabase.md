# Supabase Integration (Provisioned)

This backend uses Supabase for:
- Authentication (Supabase Auth)
- Database (Postgres via Supabase REST)

Status: CONFIGURED via automated provisioning.

## Environment variables
Set via your runtime environment (see `.env.example` in the root if provided by your orchestrator). Required:

- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- SITE_URL
- JWT_SECRET_KEY
- JWT_ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES

Notes:
- SITE_URL is used for email redirect links (signup -> `${SITE_URL}/auth/callback`).
- Service uses SUPABASE_SERVICE_ROLE_KEY server-side for REST and Admin operations.
- CORS origins are controlled via `CORS_ALLOW_ORIGINS` (comma-separated).

## Database schema (public)

Tables created:

1) public.profiles
- id uuid primary key default gen_random_uuid()
- email text unique not null
- created_at timestamptz default now()

Indexes/constraints:
- PRIMARY KEY (id)
- UNIQUE (email)

RLS:
- Enabled
- Policies:
  - profiles_select_own: FOR SELECT USING (auth.uid() = id)
  - profiles_insert_service: FOR INSERT WITH CHECK (auth.role() = 'service_role')
  - profiles_update_service: FOR UPDATE USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role')
  - profiles_delete_service: FOR DELETE USING (auth.role() = 'service_role')

2) public.todos
- id uuid primary key default gen_random_uuid()
- user_id uuid not null references public.profiles(id) on delete cascade
- title text not null
- description text
- completed boolean not null default false
- created_at timestamptz default now()
- updated_at timestamptz default now()

Indexes/constraints:
- PRIMARY KEY (id)
- FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE
- INDEX (user_id)

RLS:
- Enabled
- Policies:
  - todos_select_owner: FOR SELECT USING (auth.uid() = user_id)
  - todos_insert_owner: FOR INSERT WITH CHECK (auth.uid() = user_id)
  - todos_update_owner: FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id)
  - todos_delete_owner: FOR DELETE USING (auth.uid() = user_id)

Implementation details:
- Policies were created idempotently (existing policies dropped and recreated if necessary).
- RLS is enabled on both tables.

## Authentication and email redirects

- Registration uses Supabase Auth signup with:
  emailRedirectTo: `${SITE_URL}/auth/callback`

- Password updates use the Supabase Admin API (service role key), keeping least-privilege policies in DB.

Checklist in Supabase Dashboard:
1. Authentication > URL Configuration:
   - Site URL: set to your deployment URL (example: https://yourapp.example.com)
   - Allowed Redirect URLs:
     - http://localhost:8000/**
     - http://localhost:3000/**
     - https://yourapp.example.com/**
2. Authentication > Providers: enable only those needed.
3. Authentication > Email Templates: customize as desired; links will use Site URL and RedirectTo.
4. Database > Policies: you should see 4 policies on profiles and 4 on todos as listed above.
5. Database > Tables: profiles and todos exist in public schema with columns as specified.

## Backend integration alignment

The FastAPI backend already:
- Uses SUPABASE_SERVICE_ROLE_KEY for REST calls (select/insert/update/delete).
- Uses ANON key for end-user auth endpoints (sign up / sign in).
- Uses Admin endpoints with service role for password update.
- Creates user profile row in `profiles` upon registration (if not present).
- Enforces todo ownership at application layer as well (filters include user_id).

No code changes are required for basic Supabase integration beyond setting environment variables.

## Troubleshooting

- 401/redirect errors during email flows: ensure your redirect URLs are configured in Supabase as noted above.
- RLS permission errors with service role keys: ensure your server-side calls are using the service role key (Authorization: Bearer <service_role_key>), which the backend already does.
- Missing environment vars: service will not function correctly. See Required Environment Variables at top.

## SQL Reference

Policies and RLS were applied similar to:

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.todos ENABLE ROW LEVEL SECURITY;

-- profiles
CREATE POLICY profiles_select_own ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY profiles_insert_service ON public.profiles
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY profiles_update_service ON public.profiles
  FOR UPDATE USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY profiles_delete_service ON public.profiles
  FOR DELETE USING (auth.role() = 'service_role');

-- todos
CREATE POLICY todos_select_owner ON public.todos
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY todos_insert_owner ON public.todos
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY todos_update_owner ON public.todos
  FOR UPDATE USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY todos_delete_owner ON public.todos
  FOR DELETE USING (auth.uid() = user_id);

## Notes
- For production, you could rely on Supabase access tokens directly instead of issuing your own JWTs; current setup issues internal JWTs for the client after verifying credentials with Supabase Auth.

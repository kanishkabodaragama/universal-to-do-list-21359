# Supabase Integration

This backend uses Supabase for:
- Authentication (Supabase Auth)
- Database (Postgres via Supabase REST)

## Environment variables
See `.env.example`. Provide actual values in environment (.env managed by orchestrator).

- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- SITE_URL
- JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

## Database tables

Create the following tables in Supabase:

1) profiles
```
id uuid primary key default gen_random_uuid()
email text unique not null
created_at timestamp with time zone default now()
```

2) todos
```
id uuid primary key default gen_random_uuid()
user_id uuid not null references profiles(id) on delete cascade
title text not null
description text
completed boolean not null default false
created_at timestamp with time zone default now()
updated_at timestamp with time zone default now()
```

Ensure Row Level Security (RLS) is enabled and policies allow:
- profiles: users can select their own row by auth.uid() = id; insert by service role only
- todos: users can select/insert/update/delete rows where user_id = auth.uid()

This backend uses the service role key; still keep least privilege policies.

## Email redirect
On sign-up, the service sets `email_redirect_to` to `${SITE_URL}/auth/callback`.

## Notes
- The backend creates JWT for the client itself after verifying credentials with Supabase Auth.
- For production, consider using Supabase's access token directly instead of internal JWT.

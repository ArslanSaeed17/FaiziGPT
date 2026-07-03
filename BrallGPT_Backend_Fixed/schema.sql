-- =====================================================================
-- BrallGPT — Supabase schema
--
-- Run this in the Supabase SQL editor (Project -> SQL Editor -> New query)
-- on a fresh project before starting the backend.
--
-- The backend talks to Supabase using the SERVICE ROLE key only
-- (see app/core/supabase_client.py), which bypasses Row Level Security.
-- RLS is enabled below anyway as a safety net: if the anon/public key
-- were ever leaked or used by mistake, these tables stay locked down
-- because no policies are defined for the anon/authenticated roles.
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------
create table if not exists users (
  id                    uuid primary key default gen_random_uuid(),
  full_name             text not null,
  email                 text not null unique,
  password_hash         text not null,
  bio                   text,
  university            text,
  is_admin              boolean not null default false,
  plan                  text not null default 'free',
  daily_questions_used  integer not null default 0,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists idx_users_email on users (email);

alter table users enable row level security;

-- ---------------------------------------------------------------------
-- chats
-- ---------------------------------------------------------------------
create table if not exists chats (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users (id) on delete cascade,
  title       text not null default 'Untitled Chat',
  tool_type   text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists idx_chats_user_id on chats (user_id);
create index if not exists idx_chats_updated_at on chats (updated_at desc);

alter table chats enable row level security;

-- ---------------------------------------------------------------------
-- messages
-- ---------------------------------------------------------------------
create table if not exists messages (
  id          uuid primary key default gen_random_uuid(),
  chat_id     uuid not null references chats (id) on delete cascade,
  role        text not null check (role in ('user', 'assistant')),
  content     text not null,
  created_at  timestamptz not null default now()
);

create index if not exists idx_messages_chat_id on messages (chat_id);
create index if not exists idx_messages_created_at on messages (chat_id, created_at);

alter table messages enable row level security;

-- ---------------------------------------------------------------------
-- feedback
-- ---------------------------------------------------------------------
create table if not exists feedback (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users (id) on delete cascade,
  message     text not null,
  rating      integer check (rating between 1 and 5),
  created_at  timestamptz not null default now()
);

create index if not exists idx_feedback_user_id on feedback (user_id);

alter table feedback enable row level security;

-- ---------------------------------------------------------------------
-- password_reset_tokens
-- Only a SHA-256 hash of the raw token is ever stored (see
-- app/core/security.py::hash_reset_token). Tokens expire after 30
-- minutes (see user_service.RESET_TOKEN_TTL_MINUTES) and are single-use.
-- ---------------------------------------------------------------------
create table if not exists password_reset_tokens (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references users (id) on delete cascade,
  token_hash  text not null unique,
  expires_at  timestamptz not null,
  used        boolean not null default false,
  created_at  timestamptz not null default now()
);

create index if not exists idx_reset_tokens_hash on password_reset_tokens (token_hash);
create index if not exists idx_reset_tokens_user_id on password_reset_tokens (user_id);

alter table password_reset_tokens enable row level security;

-- ---------------------------------------------------------------------
-- Keep chats.updated_at fresh automatically as a belt-and-braces
-- measure (the backend also calls this explicitly via touch_chat()).
-- ---------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_chats_updated_at on chats;
create trigger trg_chats_updated_at
  before update on chats
  for each row
  execute function set_updated_at();

drop trigger if exists trg_users_updated_at on users;
create trigger trg_users_updated_at
  before update on users
  for each row
  execute function set_updated_at();

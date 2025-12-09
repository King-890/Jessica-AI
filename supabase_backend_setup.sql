-- Tokens table for Auth
create table if not exists tokens (
  token text primary key,
  role text default 'user',
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Settings table for Config
create table if not exists settings (
  key text primary key,
  value jsonb,
  updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- RLS: For now, allow public access (or anon key) to read/write tokens/settings
-- Security Warning: In production, securely manage this!
alter table tokens enable row level security;
alter table settings enable row level security;

create policy "Anon Access Tokens" on tokens for all using (true) with check (true);
create policy "Anon Access Settings" on settings for all using (true) with check (true);

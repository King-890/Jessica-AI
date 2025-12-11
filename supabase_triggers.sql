-- 1. Create Learning Logs Table (Audit Trail)
-- This table stores a record every time the AI learns something new.
create table if not exists public.learning_logs (
    id bigserial primary key,
    document_id bigint references public.documents(id),
    activity_type text default 'new_memory',
    details jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Enable RLS for Security
alter table public.learning_logs enable row level security;

-- Policy: Allow authenticated users (Jessica Agent) to read/write logs
-- (Blocks public/anonymous access)
drop policy if exists "Allow Authenticated Access" on public.learning_logs;
create policy "Allow Authenticated Access" on public.learning_logs
for all
to authenticated
using (true)
with check (true);

-- 2. Add 'created_at' to documents if missing
-- (Safe to run multiple times)
alter table public.documents 
add column if not exists created_at timestamp with time zone default timezone('utc'::text, now());

-- 3. Generic Function: Auto-Update timestamps
create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- 4. Trigger: Auto-Update 'settings' timestamp
drop trigger if exists on_settings_updated on public.settings;
create trigger on_settings_updated
before update on public.settings
for each row execute procedure public.handle_updated_at();

-- 5. specific Function: Log Learning Events
create or replace function public.log_learning_event()
returns trigger
language plpgsql
security definer
as $$
begin
    -- When a new document is inserted, log it to the journal
    insert into public.learning_logs (document_id, activity_type, details)
    values (
        new.id, 
        'memory_encoded', 
        jsonb_build_object('source', new.metadata->>'source', 'topic', new.metadata->>'topic')
    );
    return new;
end;
$$;

-- 6. Trigger: Watch for "Learning" (Inserts on documents)
drop trigger if exists on_memory_added on public.documents;
create trigger on_memory_added
after insert on public.documents
for each row execute procedure public.log_learning_event();

-- 7. (Optional) Trigger for Workflow - Notify backup (if pg_net enabled)
-- This is a placeholder for future cloud workflows.
-- create trigger on_memory_backup ... 

-- Create a specific schema for extensions to keep public clean
create schema if not exists extensions;

-- Enable pgvector in the extensions schema
create extension if not exists vector with schema extensions;

-- [OPTIONAL - Enable if your Supabase Plan supports them]
-- Enable pg_cron (May require Pro plan or specific configuration)
-- create extension if not exists pg_cron with schema extensions;

-- Enable Vault (May not be available on all instances)
-- create extension if not exists vault with schema extensions;

-- Enable pg_net (May not be available/enabled)
-- create extension if not exists pg_net with schema extensions;

-- Create a table to store your documents
create table if not exists public.documents (
  id bigserial primary key,
  content text,
  metadata jsonb,
  embedding extensions.vector(384) -- Reference vector type from extensions schema
);

-- Create a function to search for documents
create or replace function public.match_documents (
  query_embedding extensions.vector(384),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
security definer
set search_path = public, extensions, pg_temp
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from public.documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;

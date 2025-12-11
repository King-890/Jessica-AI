-- Create a specific schema for extensions to keep public clean
create schema if not exists extensions;

-- Enable pgvector in the extensions schema
create extension if not exists vector with schema extensions;

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

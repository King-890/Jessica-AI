-- Fix 1: Secure the 'match_documents' function
-- This prevents malicious code from hijacking the search path during execution.
-- We explicitly set the search_path to 'public' (and 'extensions' if you move vector there).

ALTER FUNCTION match_documents(vector(384), int, jsonb)
SET search_path = public, extensions, temp;

-- Fix 2: Move 'vector' extension to a separate schema (Best Practice)
-- UNCOMMENT the lines below if you want to apply this (Recommended).
-- Be careful: You might need to update your code to reference 'extensions.vector' 
-- if you do this, OR add 'extensions' to your database search_path.

-- create schema if not exists extensions;
-- alter extension vector set schema extensions;
-- grant usage on schema extensions to public;
-- alter database postgres set search_path to public, extensions;

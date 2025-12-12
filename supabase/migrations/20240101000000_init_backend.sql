-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net; -- Required for webhooks if using pg_net

-- 1. MESSAGES TABLE
CREATE TABLE IF NOT EXISTS public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) NOT NULL,
  conversation_id uuid DEFAULT gen_random_uuid(),
  content text NOT NULL,
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  created_at timestamptz DEFAULT now()
);

-- Enable RLS for messages
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can insert their own messages
CREATE POLICY "can_insert_own_message" ON public.messages
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can select their own messages
CREATE POLICY "can_select_own_messages" ON public.messages
FOR SELECT USING (auth.uid() = user_id);


-- 2. EMBEDDINGS TABLE
CREATE TABLE IF NOT EXISTS public.embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid REFERENCES public.messages(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id),
  vector vector(1536), -- Defaulting to 1536 dim (OpenAI/Jina/etc standard), adjust if needed
  model text,
  created_at timestamptz DEFAULT now()
);

-- Index for embeddings
CREATE INDEX IF NOT EXISTS embeddings_vector_idx ON public.embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Enable RLS for embeddings
ALTER TABLE public.embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can select their own embeddings (for search)
CREATE POLICY "can_select_own_embeddings" ON public.embeddings
FOR SELECT USING (auth.uid() = user_id);


-- 3. INFERENCE JOBS TABLE (Queue)
CREATE TABLE IF NOT EXISTS public.inference_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid REFERENCES public.messages(id) ON DELETE CASCADE,
  status text DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
  user_id uuid REFERENCES auth.users(id), -- Optional denormalization for RLS
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable RLS for jobs
ALTER TABLE public.inference_jobs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own jobs
CREATE POLICY "can_view_own_jobs" ON public.inference_jobs
FOR SELECT USING (auth.uid() = user_id);


-- 4. AUTOMATIC EMBEDDING TRIGGER (Stub or Webhook configuration)
-- This function calls the 'embed-generator' Edge Function via pg_net or internal hook
-- For now, we'll create a trigger that effectively notifies the worker or relies on the worker to pick up changes.
-- Alternatively, simpler: The 'enqueue-inference' function can trigger generation.

-- Example Cron Job (if admin enabled):
-- SELECT cron.schedule('process-jobs', '*/1 * * * *', $$
--   -- SQL to invoke function or notify worker
-- $$);

-- 5. ATOMIC JOB CLAIMING FUNCTION
CREATE OR REPLACE FUNCTION public.fn_claim_inference_job()
RETURNS TABLE (
  id uuid,
  message_id uuid,
  status text,
  user_id uuid,
  created_at timestamptz,
  updated_at timestamptz,
  message_content text,
  message_conversation_id uuid,
  message_user_id uuid
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  WITH next_job AS (
    SELECT j.id
    FROM public.inference_jobs j
    WHERE j.status = 'queued'
    ORDER BY j.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  UPDATE public.inference_jobs j
  SET status = 'processing', updated_at = now()
  FROM next_job
  INNER JOIN public.messages m ON next_job.id = j.id AND j.message_id = m.id -- Join logic might need check
  WHERE j.id = next_job.id
  RETURNING j.id, j.message_id, j.status, j.user_id, j.created_at, j.updated_at, 
            (SELECT content FROM messages WHERE id = j.message_id) as message_content,
            (SELECT conversation_id FROM messages WHERE id = j.message_id) as message_conversation_id,
            (SELECT user_id FROM messages WHERE id = j.message_id) as message_user_id;
END;
$$;


-- Fix for atomic job claiming functionality
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
    SELECT j.id, j.message_id -- Select message_id as well
    FROM public.inference_jobs j
    WHERE j.status = 'queued'
    ORDER BY j.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  UPDATE public.inference_jobs j
  SET status = 'processing', updated_at = now()
  FROM next_job
  INNER JOIN public.messages m ON m.id = next_job.message_id -- Join on next_job instead of j
  WHERE j.id = next_job.id
  RETURNING j.id, j.message_id, j.status, j.user_id, j.created_at, j.updated_at, 
            m.content as message_content,
            m.conversation_id as message_conversation_id,
            m.user_id as message_user_id;
END;
$$;

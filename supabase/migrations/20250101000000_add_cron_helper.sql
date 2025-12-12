-- Helper function to schedule the inference worker securely
CREATE OR REPLACE FUNCTION public.install_inference_cron(service_key text, project_url text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Schedule the job (Upsert)
  PERFORM cron.schedule(
    'process-inference-jobs',
    '* * * * *', -- Every minute
    format(
      'SELECT net.http_post(
          url:=''%s/functions/v1/run-inference-worker'',
          headers:=''{"Content-Type": "application/json", "Authorization": "Bearer %s"}''::jsonb,
          body:=''{}''::jsonb
      ) as request_id;',
      project_url,
      service_key
    )
  );
END;
$$;

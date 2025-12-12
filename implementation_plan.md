# Supabase Backend Migration Plan

This plan outlines the migration of the Jessica AI backend to a serverless architecture using Supabase.

## Goal
Move all backend compute, storage, and AI processing to Supabase. The frontend will remain a thin client.

## User Review Required
> [!IMPORTANT]
> This migration requires a Supabase project. You will need to provide `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (and `SUPABASE_ANON_KEY` for the frontend) in your environment variables.

## Proposed Changes

### 1. Database & Schema (SQL Migrations)
#### [NEW] [20240101000000_init_backend.sql](file:///d:/Jessica%20AI/supabase/migrations/20240101000000_init_backend.sql)
- Enable `vector` and `pg_cron` extensions.
- Create `messages` table (with RLS).
- Create `embeddings` table (with vector column and index).
- Create `inference_jobs` table for queuing.
- Configure RLS policies.

### 2. Edge Functions (Serverless Compute)
All functions will be in `supabase/functions/`.

#### [NEW] [embed-generator/index.ts](file:///d:/Jessica%20AI/supabase/functions/embed-generator/index.ts)
- Accepts text, generates embeddings (via external value or placeholder), and updates the database.
- Designed to be called via webhook or trigger.

#### [NEW] [enqueue-inference/index.ts](file:///d:/Jessica%20AI/supabase/functions/enqueue-inference/index.ts)
- API endpoint for frontend to send chat messages.
- Validates Auth.
- Inserts message into DB.
- Queues job in `inference_jobs`.

#### [NEW] [run-inference-worker/index.ts](file:///d:/Jessica%20AI/supabase/functions/run-inference-worker/index.ts)
- Background worker to process `inference_jobs`.
- Calls LLM (local or cloud).
- Updates message with response.

#### [NEW] [auth-proxy/index.ts](file:///d:/Jessica%20AI/supabase/functions/auth-proxy/index.ts)
- Middleware/Proxy for validating user context if needed beyond standard Supabase Auth.

### 3. Frontend Integration
#### [NEW] [src/services/supabase_adapter.js](file:///d:/Jessica%20AI/src/services/supabase_adapter.js)
- methods to `sendMessage` (calls `enqueue-inference`).
- methods to `subscribeToMessages` (Supabase Realtime).

### 4. CI/CD & Deploy
#### [NEW] [deploy_supabase.cmd](file:///d:/Jessica%20AI/deploy_supabase.cmd)
- Helper script for deploying functions and migrations.
#### [NEW] [.github/workflows/supabase-deploy.yml](file:///d:/Jessica%20AI/.github/workflows/supabase-deploy.yml)
- Automated deployment.

## verification Plan

### Automated Tests
- Integration script `test_supabase_flow.sh` (or .js) to:
    1. Sign up/Sign in (get token).
    2. Call `enqueue-inference`.
    3. Verify DB insert.
    4. Verify worker picks it up (mocked if necessary).

### Manual Verification
- User will run the deployment and chat via the frontend.

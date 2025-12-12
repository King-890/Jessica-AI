# Jessica AI - Supabase Backend

This directory contains the configurations and scripts for the backend of Jessica AI, now migrated to Supabase.

## Setup Instructions

### 1. Prerequisites
- **Supabase CLI**: [Install Supabase CLI](https://supabase.com/docs/guides/cli)
- **Docker**: Required for local Supabase development (`supabase start`).
- **Node.js**: For running tests and scripts.

### 2. Environment Variables
Create a `.env` file in the root directory (or use the existing one) with the following keys. 
For local development, these are printed when you run `supabase start`.

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
```

### 3. Running Locally
To start the local Supabase stack (Database, Auth, Edge Functions, Realtime):

```bash
supabase start
```

To run the migrations and seed the database:
(Happens automatically on start if migrations are in `supabase/migrations`)

### 4. Deploying to Cloud
To deploy to your live Supabase project:

1.  Login: `supabase login`
2.  Link Project: `supabase link --project-ref <your-project-ref>`
3.  Deploy:
    ```bash
    ./deploy_supabase.cmd
    ```
    Or manually:
    ```bash
    supabase db push
    supabase functions deploy enqueue-inference
    supabase functions deploy run-inference-worker
    ```

## Architecture

-   **Database**: Postgres with `pgvector` for embeddings.
-   **Auth**: Supabase Auth (JWT).
-   **Compute**: Supabase Edge Functions (Deno).
    -   `enqueue-inference`: Receives chat messages, saves to DB, queues job.
    -   `run-inference-worker`: Processes jobs, calls AI model (mocked or external).
-   **Realtime**: Frontend subscribes to `messages` table changes.

## Testing

Run the integration test script to verify the flow:

```bash
npm install @supabase/supabase-js dotenv
node test_supabase_flow.js
```

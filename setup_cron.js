require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function setupCron() {
    console.log("Setting up Cron Job for run-inference-worker...");

    // Call the RPC defined in the migration
    const { error } = await supabase.rpc('install_inference_cron', {
        service_key: supabaseKey,
        project_url: supabaseUrl
    });

    if (error) {
        console.error("Error setting up cron:", error);
    } else {
        console.log("Cron job 'process-inference-jobs' scheduled successfully (every minute).");
    }
}

setupCron();

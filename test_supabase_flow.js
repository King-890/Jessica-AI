// test_supabase_flow.js
// Usage: node test_supabase_flow.js
// Prerequisite: npm install @supabase/supabase-js dotenv

require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY; // Using service role to bypass auth for test setup if needed, or normal key

if (!supabaseUrl || !supabaseKey) {
    console.error("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function runTest() {
    console.log("Starting Supabase Integration Test...");

    // 1. Simulate User Login (Create a test user or use an existing one)
    // For simplicity, we'll assume a test user exists or just use the service role to act as a user
    // But enqueue-inference requires a real JWT usually.
    // Let's sign up a random test user
    const email = `testuser_${Date.now()}@example.com`;
    const password = 'testpassword123';

    console.log(`Creating test user: ${email}`);
    const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
    });

    if (authError) {
        console.error("Auth Error:", authError);
        return;
    }

    const userId = authData.user?.id;
    const token = authData.session?.access_token;

    if (!token) {
        console.log("No session returned (confirm email might be on). Using Service Role for operations instead of JWT for now if possible, but Edge Function requires JWT.");
        // If email confirmation is on, this fails. 
        // For testing, we might need a user that is already confirmed.
        console.log("Skipping Inference Test if no token available.");
        return;
    }

    console.log("User authenticated.");

    // 2. Call Enqueue-Inference
    console.log("Calling enqueue-inference...");
    const functionUrl = `${supabaseUrl}/functions/v1/enqueue-inference`;
    const response = await fetch(functionUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: "Hello Jessica, can you help me?",
            conversation_id: null
        })
    });

    if (!response.ok) {
        console.error("Enqueue Failed:", await response.text());
        return;
    }

    const result = await response.json();
    console.log("Enqueue Result:", result);

    const jobId = result.job_id;
    const messageId = result.message_id;

    // 3. Poll for Job Completion (Simulating Frontend Polling)
    console.log(`Polling job ${jobId}...`);
    let status = 'queued';
    let attempts = 0;
    while (status !== 'completed' && status !== 'failed' && attempts < 10) {
        await new Promise(r => setTimeout(r, 1000));
        const { data: job } = await supabase.from('inference_jobs').select('status').eq('id', jobId).single();
        status = job.status;
        console.log(`Job Status: ${status}`);
        attempts++;
    }

    // 4. Verify Assistant Response
    console.log("Checking for Assistant Response...");
    const { data: messages } = await supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', result.conversation_id)
        .order('created_at', { ascending: true });

    console.log("Messages in Conversation:");
    messages.forEach(m => console.log(`[${m.role}] ${m.content}`));

    if (messages.find(m => m.role === 'assistant')) {
        console.log("✅ TEST PASSED: Assistant response received.");
    } else {
        console.error("❌ TEST FAILED: No assistant response found.");
    }

    // Cleanup (Optional)
    // await supabase.auth.admin.deleteUser(userId);
}

runTest();

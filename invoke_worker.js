require('dotenv').config();

async function invoke() {
    const url = `${process.env.SUPABASE_URL}/functions/v1/run-inference-worker`;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

    console.log(`Invoking: ${url}`);

    // Use standard fetch
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${key}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    });

    console.log(`Status: ${response.status} ${response.statusText}`);
    const text = await response.text();
    console.log("Body:", text);
}

invoke();

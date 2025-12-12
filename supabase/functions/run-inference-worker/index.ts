import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.21.0";

console.log("Run-Inference-Worker Function Initialized");

serve(async (req: Request) => {
    try {
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        const supabase = createClient(supabaseUrl, supabaseKey);

        // Atomic Job Claiming via Stored Procedure
        const { data: job, error: claimError } = await supabase
            .rpc('fn_claim_inference_job')
            .maybeSingle();

        if (claimError) throw claimError;

        if (!job) {
            return new Response(JSON.stringify({ message: "No jobs to process" }), { status: 200 });
        }

        console.log(`Processing job ${job.id} for message ${job.message_id}`);

        // Perform Inference (Mocking LLM Call)
        // Replace this with actual call to your LLM API
        const mockResponse = `This is a mocked AI response to: "${job.message_content}". I am running on the Edge!`;

        // Simulate delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Store Assistant Response
        const { data: assistantMessage, error: replyError } = await supabase
            .from('messages')
            .insert({
                user_id: job.message_user_id, // Match the user of the conversation
                conversation_id: job.message_conversation_id,
                content: mockResponse,
                role: 'assistant'
            })
            .select()
            .single();

        if (replyError) throw replyError;

        // Update Job Status to Completed
        await supabase.from('inference_jobs').update({ status: 'completed' }).eq('id', job.id);

        // Trigger Embedding for the new Assistant Message
        await fetch(`${supabaseUrl}/functions/v1/embed-generator`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${supabaseKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message_id: assistantMessage.id, user_id: job.message_user_id })
        });

        return new Response(JSON.stringify({ success: true, job_id: job.id, response_id: assistantMessage.id }), {
            headers: { "Content-Type": "application/json" },
            status: 200,
        });

    } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
            headers: { "Content-Type": "application/json" },
            status: 500,
        });
    }
});

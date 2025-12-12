import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.21.0";

console.log("Enqueue-Inference Function Initialized");

serve(async (req: Request) => {
    try {
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        const supabase = createClient(supabaseUrl, supabaseKey);

        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return new Response(JSON.stringify({ error: 'Missing Authorization header' }), { status: 401 });
        }
        const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));

        if (authError || !user) {
            return new Response(JSON.stringify({ error: 'Unauthorized', details: authError }), { status: 401 });
        }

        const { content, conversation_id } = await req.json();

        if (!content) {
            return new Response(JSON.stringify({ error: 'Content is required' }), { status: 400 });
        }

        const { data: messageData, error: messageError } = await supabase
            .from('messages')
            .insert({
                user_id: user.id,
                conversation_id: conversation_id || crypto.randomUUID(),
                content: content,
                role: 'user'
            })
            .select()
            .single();

        if (messageError) throw messageError;

        const { data: jobData, error: jobError } = await supabase
            .from('inference_jobs')
            .insert({
                message_id: messageData.id,
                user_id: user.id,
                status: 'queued'
            })
            .select()
            .single();

        if (jobError) throw jobError;

        return new Response(JSON.stringify({
            success: true,
            message_id: messageData.id,
            job_id: jobData.id,
            conversation_id: messageData.conversation_id
        }), {
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

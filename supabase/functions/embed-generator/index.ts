// @ts-ignore
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.21.0";

console.log("Embed-Generator Function Initialized");

// @ts-ignore
declare const Deno: any;

serve(async (req: Request) => {
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const { message_id, content, user_id } = await req.json();

    if (!content && !message_id) {
      return new Response(JSON.stringify({ error: "Missing content or message_id" }), { status: 400 });
    }

    let textToEmbed = content;

    if (message_id && !content) {
      const { data, error } = await supabase
        .from('messages')
        .select('content, user_id')
        .eq('id', message_id)
        .single();

      if (error || !data) throw new Error("Message not found");
      textToEmbed = data.content;
    }

    console.log(`Generating embedding for: ${textToEmbed.substring(0, 50)}...`);

    // Mock 1536-dim vector for testing
    const mockVector = Array(1536).fill(0).map(() => Math.random());

    const { error: insertError } = await supabase
      .from('embeddings')
      .insert({
        message_id: message_id,
        user_id: user_id,
        vector: mockVector,
        model: 'mock-model-v1'
      });

    if (insertError) throw insertError;

    return new Response(JSON.stringify({ success: true, message: "Embedding generated and stored." }), {
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

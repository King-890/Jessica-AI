import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.21.0";

console.log("Auth-Proxy Function Initialized");

serve(async (req: Request) => {
    try {
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        const supabase = createClient(supabaseUrl, supabaseKey);

        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return new Response(JSON.stringify({ error: 'Missing Authorization header' }), { status: 401 });
        }

        // Validate JWT
        const { data: { user }, error } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));

        if (error || !user) {
            return new Response(JSON.stringify({ valid: false, error: 'Invalid Token' }), { status: 401 });
        }

        return new Response(JSON.stringify({
            valid: true,
            user: {
                id: user.id,
                email: user.email,
                role: user.role
            }
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

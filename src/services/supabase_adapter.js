import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client
// Ensure these environment variables are set in your frontend configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "YOUR_SUPABASE_URL";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "YOUR_SUPABASE_ANON_KEY";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const SupabaseAdapter = {
    /**
     * Sends a message to the inference queue.
     * @param {string} content - The text content of the message.
     * @param {string} [conversationId] - Optional conversation ID.
     * @returns {Promise<object>} - The response data.
     */
    async sendMessage(content, conversationId = null) {
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) throw new Error("User not authenticated");

        const response = await fetch(`${supabaseUrl}/functions/v1/enqueue-inference`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${session.access_token}`,
            },
            body: JSON.stringify({
                content,
                conversation_id: conversationId,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || "Failed to send message");
        }

        return await response.json();
    },

    /**
     * Subscribes to new messages for a specific conversation.
     * @param {string} conversationId - The conversation ID to listen to.
     * @param {function} onMessage - Callback function when a new message is received.
     * @returns {object} - The subscription object.
     */
    subscribeToMessages(conversationId, onMessage) {
        return supabase
            .channel(`chat:${conversationId}`)
            .on(
                'postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'messages',
                    filter: `conversation_id=eq.${conversationId}`
                },
                (payload) => {
                    onMessage(payload.new);
                }
            )
            .subscribe();
    },

    /**
     * Checks the status of a specific job.
     * @param {string} jobId - The ID of the inference job.
     * @returns {Promise<string>} - The status of the job.
     */
    async getJobStatus(jobId) {
        const { data, error } = await supabase
            .from('inference_jobs')
            .select('status')
            .eq('id', jobId)
            .single();

        if (error) throw error;
        return data.status;
    }
};

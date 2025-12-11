import sys
import os
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.backend.cloud.supabase_client import get_client

def view_knowledge():
    """
    Fetch and display the latest knowledge from Supabase 'documents' table.
    """
    print("☁️ Connecting to Supabase Knowledge Base...")
    client = get_client()
    if not client:
        print("❌ Error: Supabase client not available.")
        return

    try:
        # Fetch latest 20 documents
        # Note: 'documents' table might differ in structure based on vector extension usage.
        # We assume 'id', 'content', 'metadata' exist.
        res = client.table("documents").select("id, content, metadata") \
            .order("id", desc=True).limit(20).execute()
        
        data = res.data
        if not data:
            print("📭 Knowledge Base is empty.")
            return

        print(f"\n📚 Latest {len(data)} Learning Entries:\n" + "="*60)
        
        for item in data:
            meta = item.get("metadata", {})
            source = meta.get("source", "Unknown")
            topic = meta.get("topic", "General")
            content_preview = item.get("content", "")[:100].replace("\n", " ")
            
            print(f"ID: {item['id']} | Topic: {topic} | Source: {source}")
            print(f"Content: {content_preview}...")
            print("-" * 60)
            
        print("\n✅ End of Report.")

    except Exception as e:
        print(f"❌ Error fetching knowledge: {e}")

if __name__ == "__main__":
    view_knowledge()

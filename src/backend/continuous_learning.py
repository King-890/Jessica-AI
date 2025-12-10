import time
import random
import os
import json
from datetime import datetime

# Import our existing tools
# Note: We need to make sure we are adding to SUPABASE integration
try:
    from src.rag.vector_store import VectorStore
    from src.backend.ai_core import google_search
    from src.backend.cloud.supabase_client import upload_file, get_client
except ImportError:
    # Fix python path if run as standalone script
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.rag.vector_store import VectorStore
    from src.backend.ai_core import google_search
    from src.backend.cloud.supabase_client import upload_file, get_client

# Topics to learn about
# Prioritized Security & Tech Topics
TOPICS = [
    # Core Tech
    "advanced software architecture patterns",
    "compiler design and optimization",
    "operating system kernel development",
    "distributed systems reliability",

    # Security / Hacking (Defensive Focus)
    "advanced penetration testing techniques",
    "zero-day vulnerability research methodology",
    "reverse engineering malware analysis",
    "secure coding practices for finance",
    "blockchain smart contract auditing",
    "network security protocol analysis",
    "ethical hacking vs blackhat techniques analysis",  # Understanding the threat
    "web application firewall bypass prevention",
    "buffer overflow protection mechanisms"
]


class ContinuousLearner:
    def __init__(self):
        print("Initializing Continuous Learner (Cloud/GitHub Mode)...")
        # Initialize Vector Store (this connects to Supabase via existing logic)
        self.brain = VectorStore()
        self.bucket = "datasets"
        self.cli = get_client()

    def should_run(self) -> bool:
        """Check Supabase settings to see if learning is enabled."""
        if not self.cli:
            return True  # Default to run if no cli (local testing)
        try:
            # We use the 'settings' table we created earlier
            resp = self.cli.table("settings").select("value").eq("key", "learning_enabled").execute()
            if resp.data:
                return bool(resp.data[0].get("value"))

            # If setting doesn't exist, create it as TRUE (default ON)
            self.cli.table("settings").upsert({"key": "learning_enabled", "value": True}).execute()
            return True
        except Exception:
            return True  # Fail open or closed? Let's fail open for "24/7" feel.

    def crawl_url(self, url: str) -> str:
        """Fetch and clean page content. Basic implementation."""
        try:
            import requests
            from bs4 import BeautifulSoup

            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return ""

            soup = BeautifulSoup(resp.text, 'html.parser')
            # Remove scripts and styles
            for s in soup(["script", "style", "nav", "footer"]):
                s.decompose()

            text = soup.get_text()
            # Clean whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:10000]  # Limit size per page
        except Exception:
            return ""

    def learn_step(self, topic: str):
        print(f"\n[Learning] researching: {topic}...")

        # 1. Search (Google/DDG)
        query = f"{topic} detailed guide {datetime.now().year}"
        summary_text = google_search(query)

        if "No results found" in summary_text:
            print(" - No results.")
            return

        # 2. Extract URLs from summary (if markdown links exist) or search again for links
        # simple hack: regex for http links in the summary or just use the summary itself + specific crawl
        # For this 'Advance AI', let's search specifically for links to crawl
        import re
        links = re.findall(r'(https?://[^\s\)]+)', summary_text)

        full_knowledge = f"Summary:\n{summary_text}\n\nDeep Dive:\n"

        # Crawl top 2 links
        for link in links[:2]:
            print(f" - Crawling {link}...")
            page_content = self.crawl_url(link)
            if page_content:
                full_knowledge += f"\n--- Source: {link} ---\n{page_content}\n"

        # 3. Store in Brain (Vector Store)
        from src.rag.document_processor import Document

        # Chunking might be needed if too large, but pgvector handles reasonable sizes.
        # We'll store the summary + crawled content.
        doc = Document(
            content=full_knowledge[:8000],  # safe limit for embedding
            metadata={
                "source": "deep_crawler",
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            }
        )

        try:
            self.brain.add_documents([doc])
            print(" - Memory Updated (Supabase).")
        except Exception as e:
            print(f" - Vector Error: {e}")

        # 4. Archive Raw Data (Zero Footprint)
        filename = f"learned_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{topic[:10].replace(' ', '_')}.json"

        # We upload DIRECTLY from memory if possible, but our upload_file takes a path.
        # So we create a temp file, upload, then IMMEDIATELY delete.
        temp_path = f"temp_{filename}"

        data = {
            "topic": topic,
            "query": query,
            "summary": summary_text,
            "full_content": full_knowledge,
            "timestamp": datetime.now().isoformat()
        }

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            upload_file(self.bucket, f"auto_learning/{filename}", temp_path)
            print(" - Archived to Cloud.")
        except Exception as e:
            print(f" - Archive Error: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(" - Local temp cleaned.")

    def start_loop(self, single_run: bool = False, max_duration: int = 0):
        print(f"Jessica Learner Started. (Single Run: {single_run}, Max Duration: {max_duration}s)")
        start_time = time.time()

        while True:
            # 1. Check Kill Switch
            if not self.should_run():
                print("Learning paused by command (Supabase setting 'learning_enabled'=false). Exiting.")
                break

            # Check duration limit
            if max_duration > 0 and (time.time() - start_time) > max_duration:
                print("Max duration reached. Exiting gracefully.")
                break

            # 2. Pick a random topic (Security prioritized)
            topic = random.choice(TOPICS)
            try:
                self.learn_step(topic)
            except Exception as e:
                print(f"ERROR exploring {topic}: {e}")

            # Logic:
            # If max_duration is SET, we ignore single_run and loop until time is up.
            # If max_duration is 0, we respect single_run.
            if max_duration == 0 and single_run:
                print("Single run completed (GitHub Action mode).")
                break

            # Wait before next topic
            # If running locally 24/7, we wait.
            # If running effectively 24/7 via CI, we might just exit and let CI restart,
            # but 'single_run' handles that.
            sleep_sec = 60 * 5  # Every 5 minutes
            print(f"[Wait] Sleeping for {sleep_sec}s...")
            time.sleep(sleep_sec)


if __name__ == "__main__":
    import argparse

    # Check if running in CI/Cloud environment to decide loop vs single run
    # For GitHub actions, we might want to run for a limit duration or once per schedule trigger
    # Let's run once per trigger to avoid timeouts, but trigger often.
    is_ci = os.getenv("CI") == "true"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Run for N seconds then exit (0 = infinite or single run based on env)"
    )
    args = parser.parse_args()

    learner = ContinuousLearner()
    learner.start_loop(single_run=is_ci, max_duration=args.duration)


import os
import time
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIG ---
CORPUS_FILE = "training_data/corpus.txt"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME = "datasets"

TOPICS = [
    "python programming advanced patterns",
    "rust lang memory safety guide",
    "linux kernel internal documentation",
    "distributed systems design patterns",
    "machine learning transformer architecture explained",
    "cybersecurity penetration testing methodologies",
    "reactjs performance optimization guide",
    "software architecture detailed principles",
    "tcp ip networking protocols deep dive",
    "cryptography algorithms mathematics"
]

class DataMiner:
    def __init__(self):
        self.ensure_dir()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.chars_harvested = 0
        self.last_sync = time.time()

    def ensure_dir(self):
        if not os.path.exists("training_data"):
            os.makedirs("training_data")

    def search_ddg(self, query):
        """Use DuckDuckGo (No API Key required)"""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                urls = [r['href'] for r in results]
                return urls
        except ImportError:
            print("[Error] duckduckgo-search not installed. Run: pip install duckduckgo-search")
            return []
        except Exception as e:
            print(f"[Search Error]: {e}")
            return []

    def crawl(self, url):
        try:
            print(f"   -> Crawling: {url[:60]}...")
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                return ""
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            # Remove junk
            for s in soup(["script", "style", "nav", "footer", "header", "form"]):
                s.decompose()
            
            text = soup.get_text(separator=' ')
            # Clean text
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception as e:
            # print(f"      [Error]: {e}")
            return ""

    def sync_to_cloud(self):
        """Upload current corpus to Supabase"""
        if not (SUPABASE_URL and SUPABASE_KEY):
            print("   [Cloud] Skpping sync (No Supabase Keys in env)")
            return

        print("   ☁️ Syncing corpus to Supabase...")
        try:
            file_path = CORPUS_FILE
            file_name = f"auto_learning/corpus_backup_{int(time.time())}.txt"
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Simple REST Upload
            url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "text/plain"
            }
            # Try to upload
            resp = requests.post(url, headers=headers, data=file_data)
            
            if resp.status_code in [200, 201]:
                print("   ✅ Backup Successful!")
            else:
                print(f"   ⚠️ Backup Failed: {resp.text}")
                
        except Exception as e:
            print(f"   [Sync Error]: {e}")

    def mine(self):
        print(f"🚀 Sovereign Data Miner Started. Target: {CORPUS_FILE}")
        
        while True:
            for topic in TOPICS:
                print(f"\n🔍 Searching Topic: {topic}")
                urls = self.search_ddg(topic)
                
                if not urls:
                    print("   - No results found (Check internet/modules).")
                    time.sleep(2)
                    continue

                for url in urls:
                    content = self.crawl(url)
                    if len(content) > 2000: # High quality filter
                        with open(CORPUS_FILE, "a", encoding="utf-8") as f:
                            f.write(f"\n\n<|endoftext|>\n\n") 
                            f.write(content)
                            f.write(f"\n\n--- Source: {url} ---\n\n")
                        
                        self.chars_harvested += len(content)
                        size_mb = os.path.getsize(CORPUS_FILE) / (1024 * 1024)
                        print(f"      + Added {len(content)} chars. Corpus Size: {size_mb:.2f} MB")
                    
                    time.sleep(1) # Be polite
                
                # Check for sync
                if time.time() - self.last_sync > 300: # Every 5 mins
                    self.sync_to_cloud()
                    self.last_sync = time.time()
                
            print("Cycle check complete. Sleeping 5s...")
            time.sleep(5)

if __name__ == "__main__":
    miner = DataMiner()
    miner.mine()

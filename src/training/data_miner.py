
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

# Fallback Seeds (If Search Fails)
SEEDS = [
    "https://docs.python.org/3/tutorial/index.html",
    "https://doc.rust-lang.org/book/",
    "https://react.dev/learn",
    "https://kubernetes.io/docs/concepts/",
    "https://pytorch.org/tutorials/",
    "https://www.kali.org/docs/",
    "https://arxiv.org/list/cs.AI/recent"
]

TOPICS = [
    "python programming advanced patterns",
    "rust lang memory safety guide",
    "linux kernel internal documentation",
    "distributed systems design patterns",
    "machine learning transformer architecture explained",
    "cybersecurity penetration testing methodologies"
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
        # Pre-seed URLs to ensure we start immediately
        self.url_queue = SEEDS.copy()

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
                print(f"   [Search] Found {len(urls)} URLs.", flush=True)
                return urls
        except Exception as e:
            print(f"   [Search Error]: {e}", flush=True)
            return []

    def crawl(self, url):
        try:
            print(f"   -> Crawling: {url[:60]}...", flush=True)
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"      [Failed] Status: {resp.status_code}", flush=True)
                return ""
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header", "form"]):
                s.decompose()
            
            text = soup.get_text(separator=' ')
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = "\n".join(lines)
            return content
        except Exception as e:
            print(f"      [Crawl Error]: {e}", flush=True)
            return ""

    def sync_to_cloud(self):
        """Upload current corpus to Supabase"""
        if not (SUPABASE_URL and SUPABASE_KEY):
            print("   [Cloud] Skipping sync (No Supabase Keys)", flush=True)
            return

        print("   ☁️ Syncing corpus to Supabase...", flush=True)
        try:
            file_path = CORPUS_FILE
            if not os.path.exists(file_path): return
            
            file_name = f"auto_learning/corpus_backup_{int(time.time())}.txt"
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{file_name}"
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "apikey": SUPABASE_KEY,
                "Content-Type": "text/plain"
            }
            resp = requests.post(url, headers=headers, data=file_data)
            
            if resp.status_code in [200, 201]:
                print("   ✅ Backup Successful!", flush=True)
            else:
                print(f"   ⚠️ Backup Failed: {resp.text}", flush=True)
                
        except Exception as e:
            print(f"   [Sync Error]: {e}", flush=True)

    def mine(self):
        print(f"🚀 Sovereign Data Miner Started. Target: {CORPUS_FILE}", flush=True)
        
        # 1. Process Seeds First
        print("\n--- Processing Seed List ---", flush=True)
        for url in self.url_queue:
            self.process_url(url)

        # 2. Infinite Loop
        while True:
            for topic in TOPICS:
                print(f"\n🔍 Searching Topic: {topic}", flush=True)
                urls = self.search_ddg(topic)
                
                # If Search fails, try a random seed as backup
                if not urls:
                    print("   - Search blocked/empty. Using fallback seed.", flush=True)
                    # Force re-add a seed
                    import random
                    urls = [random.choice(SEEDS)]
                    time.sleep(2)

                for url in urls:
                    self.process_url(url)
                    time.sleep(1) 
                
                # Check for sync
                if time.time() - self.last_sync > 300: # Every 5 mins
                    self.sync_to_cloud()
                    self.last_sync = time.time()
                
            print("Cycle check complete. Sleeping 5s...", flush=True)
            time.sleep(5)

    def process_url(self, url):
        content = self.crawl(url)
        # Lower threshold to 200 chars to catch smaller docs
        if len(content) > 200: 
            with open(CORPUS_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n\n<|endoftext|>\n\n") 
                f.write(content)
                f.write(f"\n\n--- Source: {url} ---\n\n")
            
            self.chars_harvested += len(content)
            size_mb = os.path.getsize(CORPUS_FILE) / (1024 * 1024)
            print(f"      + Added {len(content)} chars. Corpus Size: {size_mb:.2f} MB", flush=True)
        else:
            print(f"      [Skip] Content too short ({len(content)} chars)", flush=True)
            
if __name__ == "__main__":
    miner = DataMiner()
    miner.mine()

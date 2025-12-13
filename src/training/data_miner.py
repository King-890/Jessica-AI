
import os
import time
import requests
import re
from bs4 import BeautifulSoup
import os
import time
import requests
import re
from bs4 import BeautifulSoup
# from src.backend.ai_core import google_search # Remove dependency

# Standalone Google Search simple implementation
def google_search(query):
    try:
        from serpapi import GoogleSearch
        # Note: This requires serpapi pkg or we use the duckduckgo fallback if simple
        # For this Miner, let's use the SerpApi library compatible logic or basic DDG
        pass
    except:
        pass
    # FALLBACK: Use a robust free search or just the SerpAPI standard if installed
    # Since we installed 'google-search-results', we use that.
    try:
        from serpapi import GoogleSearch
        api_key = os.getenv("GOOGLE_CSE_API_KEY") # Reuse Search Key or new one
        # If no key, we might fail. Let's assume user has key or use a public scrape hack.
        # Actually, let's just use the serpapi logic properly.
        # But wait, the user installed 'google-search-results'.
        if not api_key: return "No API Key"
        
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        # Parse organic results
        summary = ""
        if "organic_results" in results:
            for r in results["organic_results"]:
                summary += r.get("link", "") + " "
        return summary
    except Exception as e:
        return str(e)

# Target Corpus Size: 100MB
CORPUS_FILE = "training_data/corpus.txt"
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

    def ensure_dir(self):
        if not os.path.exists("training_data"):
            os.makedirs("training_data")

    def clean_text(self, text):
        # Remove empty lines and excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

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
            return self.clean_text(text)
        except Exception as e:
            print(f"      [Error]: {e}")
            return ""

    def mine(self):
        print(f"🚀 Sovereign Data Miner Started. Target: {CORPUS_FILE}")
        
        while True:
            for topic in TOPICS:
                print(f"\n🔍 Searching Topic: {topic}")
                try:
                    # 1. Get Seeds from Google
                    summary = google_search(f"{topic} documentation tutorial")
                    urls = re.findall(r'(https?://[^\s\)]+)', summary)
                    
                    # 2. Extract unique URLs
                    unique_urls = list(set(urls))[:5] # Take top 5
                    
                    for url in unique_urls:
                        content = self.crawl(url)
                        if len(content) > 1000: # Only keep substantial articles
                            with open(CORPUS_FILE, "a", encoding="utf-8") as f:
                                # Add delimiter for distinct documents
                                f.write(f"\n\n<|endoftext|>\n\n") 
                                f.write(content)
                            
                            size_mb = os.path.getsize(CORPUS_FILE) / (1024 * 1024)
                            print(f"      + Added {len(content)} chars. Corpus Size: {size_mb:.2f} MB")
                        
                        time.sleep(1) # Be polite
                except Exception as e:
                    print(f"Critical Mining Error: {e}")
                
            print("Cycle check complete. Sleeping 10s...")
            time.sleep(10)

if __name__ == "__main__":
    miner = DataMiner()
    miner.mine()

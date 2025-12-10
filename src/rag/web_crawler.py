"""
Web Crawler - Fetches and parses web content for RAG
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from urllib.parse import urlparse


class WebCrawler:
    """Fetches and processes web pages"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'JessicaAI/1.0 (Educational AI Assistant)'
        }

    def fetch_page(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch and parse a web page

        Args:
            url: URL to fetch

        Returns:
            Dict with 'title', 'content', 'url', or None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean text (remove extra whitespace)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)

            title = soup.title.string if soup.title else url

            return {
                'title': title,
                'content': clean_text,
                'url': url,
                'domain': urlparse(url).netloc
            }

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

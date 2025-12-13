import requests
import json
import os

class GeminiClient:
    """
    Lightweight client for Google Gemini API (REST).
    No heavy dependencies.
    """
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
        # Check Env Vars (Prioritize specific Gemini key, fallback to CSE key if shared)
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            # User might be trying to use one key for both Search and AI
            self.api_key = os.getenv("GOOGLE_CSE_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generate text using Gemini Flash 1.5
        """
        if not self.api_key:
            return "Error: Google API Key is missing. Please add GOOGLE_API_KEY to your .env file."

        url = f"{self.BASE_URL}?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Construct Payload
        contents = [{"parts": [{"text": prompt}]}]
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code != 200:
                return f"[Gemini Error {response.status_code}]: {response.text}"
            
            data = response.json()
            # Parse Response
            # Structure: candidates[0].content.parts[0].text
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError):
                return f"[Gemini Parsing Error]: Unexpected JSON structure. {data}"

        except Exception as e:
            return f"[Gemini Connection Error]: {e}"

import threading
import time
import speech_recognition as sr
from typing import Optional, Callable
from .tts import TTS

class VoiceManager:
    """
    Manages Voice Interaction (STT + TTS).
    Uses SpeechRecognition for microphone input and pyttsx3 (via TTS class) for output.
    """
    def __init__(self):
        self.tts = TTS()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.callback: Optional[Callable[[str], None]] = None
        self.thread = None
        
        # Audio tweaks
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000
        
        print("🎤 Voice Manager Initialized.")

    def speak(self, text: str):
        """Speak text using TTS"""
        if self.tts.is_ready():
            print(f"🔊 Speaking: {text}")
            self.tts.speak(text)
        else:
            print(f"[Silent] Speak: {text}")

    def start_listening(self, callback: Callable[[str], None]):
        """Start background listening thread"""
        self.callback = callback
        self.is_listening = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("👂 Started listening for voice commands...")

    def stop_listening(self):
        self.is_listening = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def _listen_loop(self):
        with self.microphone as source:
            print("🎤 Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Ready.")
            
            while self.is_listening:
                try:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    # Transcribe
                    try:
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            print(f"👂 Heard: {text}")
                            if self.callback:
                                self.callback(text)
                    except sr.UnknownValueError:
                        pass # Squelch
                    except sr.RequestError as e:
                        print(f"STT Error: {e}")
                        
                except Exception:
                    # Timeout or other issue, just loop
                    pass

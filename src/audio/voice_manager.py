import threading
import time
from typing import Optional, Callable
from .tts import TTS

# Optional Import for CI
try:
    import speech_recognition as sr
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sr = None
    print("Warning: SpeechRecognition not found. Voice features disabled.")

class VoiceManager:
    """
    Manages Voice Interaction (STT + TTS).
    Uses SpeechRecognition for microphone input and pyttsx3 (via TTS class) for output.
    """
    def __init__(self):
        self.tts = TTS()
        self.callback: Optional[Callable[[str], None]] = None
        self.thread = None
        
        self.recognizer = None
        self.microphone = None
        self.is_listening = False

        if AUDIO_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                # Audio tweaks
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.energy_threshold = 4000
                print("🎤 Voice Manager Initialized.")
            except Exception as e:
                print(f"Warning: Microphone init failed: {e}")
                AUDIO_AVAILABLE = False
        else:
             print("🎤 Voice Manager Disabled (Missing Libs).")

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
        if not AUDIO_AVAILABLE or not self.microphone or not self.recognizer:
            return

        with self.microphone as source:
            print("🎤 Adjusting for ambient noise...")
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except: pass
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

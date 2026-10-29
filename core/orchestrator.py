import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

from core.tools import get_current_time, save_memory, find_object, search_notes, set_reminder, live_internet_search
import datetime

class AIAssistant:
    def __init__(self):
        load_dotenv()
        
        self.api_keys = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3")
        ]
        self.api_keys = [k for k in self.api_keys if k]
        if not self.api_keys:
            print("[WARNING] No GEMINI_API_KEY found in .env!")
            self.api_keys = ["MISSING_KEY"]
            
        self.current_key_index = 0
        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
        
        # --- NEW: Dynamic Model Fetching ---
        self.available_models = self._fetch_fast_models()
        self.current_model_index = 0
        
        self.system_prompt = """You are Jarvis, an autonomous AI agent for the Memorax smart glasses system.
Keep your spoken responses concise, natural, and highly efficient for someone wearing smart glasses.
CRITICAL: For any questions about real-world facts, current events, politicians, or news, you MUST use the Google Search tool to verify the latest live information before answering.
Use the provided tools only when necessary. Never explain your internal reasoning; just provide the final helpful answer directly."""

        self.start_new_chat()

    def _fetch_fast_models(self):
        """Automatically retrieves the latest, fastest working models for the active API key."""
        print("[SYSTEM] Fetching available Gemini models automatically...")
        fast_models = []
        try:
            for m in self.client.models.list():
                # Filter out deprecated (2.5) and unstable preview models
                if "gemini" in m.name and "flash" in m.name and "2.5" not in m.name and "preview" not in m.name:
                    fast_models.append(m.name)
        except Exception as e:
            print(f"[WARNING] Could not fetch models dynamically: {e}")
        
        # Hard-priority fallback as explicitly recommended by Google's error log
        if not fast_models:
            fast_models = ["gemini-3.8-flash", "gemini-3.5-flash"]
        elif "models/gemini-3.8-flash" in fast_models:
            # Move the best model to the absolute front of the line
            fast_models.insert(0, fast_models.pop(fast_models.index("models/gemini-3.8-flash")))
            
        print(f"[SYSTEM] Priority models loaded: {fast_models[:3]}...") # Print just top 3 to keep logs clean
        return fast_models

    def _rotate_credentials(self, error_message=""):
        """Rotates API keys if quota is hit, otherwise tries the next model."""
        error_str = str(error_message)
        
        # If we hit a hard rate limit or quota, we MUST change the API key immediately
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("[FAILOVER] Quota limit hit! Instantly swapping API Key...")
            if len(self.api_keys) > 1:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                print(f"[FAILOVER] Successfully switched to backup API Key #{self.current_key_index + 1}")
                self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
                
                # Re-fetch models for the new key and reset index
                self.available_models = self._fetch_fast_models()
                self.current_model_index = 0
            else:
                print("[FAILOVER WARNING] No backup API keys left! Must wait for quota to reset.")
                
        # If it's just a model deprecation (404) or server hiccup, swap the model instead
        else:
            self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
            
            # If we've run out of models on this key, swap keys anyway
            if self.current_model_index == 0 and len(self.api_keys) > 1:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                print(f"[FAILOVER] Out of models. Switched to backup API Key #{self.current_key_index + 1}")
                self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
                self.available_models = self._fetch_fast_models()
                
            print(f"[FAILOVER] Trying next model: {self.available_models[self.current_model_index]}")
            
        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        model_name = self.available_models[self.current_model_index]
        try:
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    tools=[
                        live_internet_search,  # <-- NEW: Free live internet access!
                        get_current_time, 
                        save_memory, 
                        find_object, 
                        search_notes, 
                        set_reminder
                    ],
                    temperature=0.3
                )
            )
        except Exception as e:
            print(f"[INIT ERROR] Could not start chat with {model_name}: {e}")

    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message to the AI with an automatic multi-step retry loop."""
        
        if not image_path and not audio_path and user_text:
            clean_text = user_text.lower().strip()
            if clean_text in ["what time is it", "what time is it?", "tell me the time", "jarvis what time is it"]:
                now = datetime.datetime.now().strftime("%I:%M %p")
                return f"It is currently {now}."
            elif clean_text in ["hello", "hi", "hey jarvis", "jarvis", "hello jarvis"]:
                return "Hello! Memorax systems are online and ready. How can I help you?"

        def build_payload():
            content = []
            if user_text:
                content.append(user_text)
            
            if image_path:
                try:
                    content.append(Image.open(image_path))
                except Exception as error:
                    print(f"[SYSTEM ERROR] Could not open image: {error}")
                    
            if audio_path:
                try:
                    print(f"[SYSTEM] Uploading audio file to Gemini storage: {audio_path}")
                    audio_file = self.client.files.upload(file=audio_path)
                    content.append(audio_file)
                except Exception as error:
                    print(f"[SYSTEM ERROR] Could not upload audio: {error}")
                    
            return content

        max_retries = 3
        for attempt in range(max_retries):
            message_content = build_payload()
            try:
                response = self.chat.send_message(message_content)
                return response.text.strip()
            except Exception as e:
                print(f"[AI ERROR] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("[SYSTEM] Initiating failover recovery...")
                    # Pass the exact error to the failover system so it knows what to do!
                    self._rotate_credentials(str(e))
                else:
                    print("[AI FATAL ERROR] All failover attempts exhausted.")
                    return "I am having trouble connecting to the network right now. Please try again in a minute."
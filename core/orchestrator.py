import os
import time
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

from core.tools import get_current_time, save_memory, find_object, search_notes, set_reminder, live_internet_search

MAX_TURNS_BEFORE_RESET = 20   # keeps the chat history short so responses stay fast
GEMINI_TIMEOUT_MS = 20000     # 20 seconds; the SDK takes milliseconds


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
        self.client = self._make_client(self.api_keys[self.current_key_index])

        # Override in .env: GEMINI_MODELS=model-a,model-b
        env_models = os.getenv("GEMINI_MODELS")
        self.available_models = (
            [m.strip() for m in env_models.split(",") if m.strip()]
            if env_models else ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        )
        self.current_model_index = 0
        self.turn_count = 0

        self.system_prompt = """You are Jarvis, an autonomous AI agent for the Memorax smart glasses system.
Keep your spoken responses concise (1-3 short sentences), natural, and highly efficient for someone wearing smart glasses.

SEARCH RULES (very important):
- For ANY question about real-world facts that can change (current events, news, politicians and office holders, prices, sports, weather, products, "latest"/"current"/"now"), you MUST call live_internet_search BEFORE answering.
- Every message begins with a [Current date and time: ...] line. It is hidden background context for you only. Treat it as the true date, never assume an earlier year, and never put an old year in a search query. NEVER repeat, quote, or mention that line in your reply unless the user directly asks for the date or time.- ALWAYS search again for a new question, even if a similar question was answered earlier in this conversation. Earlier answers may be outdated.
- When search results conflict, trust the most recent one. Do not use your training knowledge for current facts.
- Use other tools only when necessary. Never explain your internal reasoning; just give the final helpful answer."""

        self.start_new_chat()

    # ------------------------------------------------------------------
    def _make_client(self, api_key):
        """Creates a Gemini client with a request timeout so hung calls fail fast."""
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )

    # ------------------------------------------------------------------
    def _rotate_credentials(self, error_message=""):
        """Rotates API keys if quota is hit, otherwise tries the next model."""
        error_str = str(error_message)

        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("[FAILOVER] Quota limit hit! Instantly swapping API Key...")
            if len(self.api_keys) > 1:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                print(f"[FAILOVER] Successfully switched to backup API Key #{self.current_key_index + 1}")
                self.client = self._make_client(self.api_keys[self.current_key_index])
                self.current_model_index = 0
            else:
                print("[FAILOVER WARNING] No backup API keys left! Must wait for quota to reset.")
        else:
            self.current_model_index = (self.current_model_index + 1) % len(self.available_models)

            if self.current_model_index == 0 and len(self.api_keys) > 1:
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                print(f"[FAILOVER] Out of models. Switched to backup API Key #{self.current_key_index + 1}")
                self.client = self._make_client(self.api_keys[self.current_key_index])

            print(f"[FAILOVER] Trying next model: {self.available_models[self.current_model_index]}")

        self.start_new_chat()

    # ------------------------------------------------------------------
    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        model_name = self.available_models[self.current_model_index]
        self.turn_count = 0
        try:
            config_kwargs = dict(
                system_instruction=self.system_prompt,
                tools=[
                    live_internet_search,
                    get_current_time,
                    save_memory,
                    find_object,
                    search_notes,
                    set_reminder
                ],
                temperature=0.3,
                max_output_tokens=300,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=False,
                    maximum_remote_calls=5
                )
            )

            # Optional: GEMINI_THINKING_BUDGET=0 in .env disables "thinking" (latency saver)
            thinking_budget = os.getenv("GEMINI_THINKING_BUDGET")
            if thinking_budget is not None and thinking_budget != "":
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=int(thinking_budget)
                )

            self.chat = self.client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            print(f"[INIT] ✅ Chat ready with model: {model_name}")
        except Exception as e:
            print(f"[INIT ERROR] Could not start chat with {model_name}: {e}")

    # ------------------------------------------------------------------
    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message to the AI. SDK automatically handles all tool calls."""

        now = datetime.datetime.now()

        # Fast local shortcuts (no API call at all)
        if not image_path and not audio_path and user_text:
            clean_text = user_text.lower().strip()
            if clean_text in ["what time is it", "what time is it?", "tell me the time", "jarvis what time is it"]:
                return f"It is currently {now.strftime('%I:%M %p')}."
            elif clean_text in ["hello", "hi", "hey jarvis", "jarvis", "hello jarvis"]:
                return "Hello! Memorax systems are online and ready. How can I help you?"

        # Keep the history short so each request stays fast
        if self.turn_count >= MAX_TURNS_BEFORE_RESET:
            print("[SYSTEM] Resetting chat history to keep responses fast.")
            self.start_new_chat()

        date_line = f"[Current date and time: {now.strftime('%A, %d %B %Y, %I:%M %p')}]"

        def build_payload():
            content = []
            if user_text:
                content.append(f"{date_line}\n{user_text}")
            else:
                content.append(date_line)
            if image_path:
                try:
                    content.append(Image.open(image_path))
                except Exception as error:
                    print(f"[SYSTEM ERROR] Could not open image: {error}")
            if audio_path:
                try:
                    print(f"[SYSTEM] Uploading audio file to Gemini storage: {audio_path}")
                    t0 = time.time()
                    audio_file = self.client.files.upload(file=audio_path)
                    print(f"[SYSTEM] ⏱ Audio upload took {time.time() - t0:.1f}s")
                    content.append(audio_file)
                except Exception as error:
                    print(f"[SYSTEM ERROR] Could not upload audio: {error}")
            return content

        max_retries = 3
        for attempt in range(max_retries):
            # Rebuilt each attempt because uploaded files belong to a specific API key
            message_content = build_payload()
            try:
                print(f"[AI] ⏱ Sending to Gemini ({self.available_models[self.current_model_index]})...")
                t0 = time.time()
                response = self.chat.send_message(message_content)
                print(f"[AI] ⏱ Gemini responded in {time.time() - t0:.1f}s")

                answer = response.text.strip() if response.text else ""
                if answer:
                    self.turn_count += 1
                    return answer
                else:
                    print(f"[AI WARNING] Empty response on attempt {attempt + 1}, retrying...")
                    continue
            except Exception as e:
                print(f"[AI ERROR] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("[SYSTEM] Initiating failover recovery...")
                    self._rotate_credentials(str(e))
                else:
                    print("[AI FATAL ERROR] All failover attempts exhausted.")
                    return "I am having trouble connecting to the network right now. Please try again in a minute."

        return "I processed your request but could not generate a response. Please try again."
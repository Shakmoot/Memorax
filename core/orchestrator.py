import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

from core.tools import get_current_time, save_memory, find_object, search_notes, set_reminder
import datetime

class AIAssistant:
    def __init__(self):
        load_dotenv()
        
        # Load multiple API keys for hackathon failover protection
        self.api_keys = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3")
        ]
        # Filter out empty/None keys
        self.api_keys = [k for k in self.api_keys if k]
        if not self.api_keys:
            print("[WARNING] No GEMINI_API_KEY found in .env!")
            self.api_keys = ["MISSING_KEY"]
            
        self.current_key_index = 0
        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
        
        # Valid, fast production models with automatic fallback
        self.available_models = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
        self.current_model_index = 0
        
        # NEW: The ReAct System Instruction
        self.react_prompt = """You are Jarvis, an autonomous AI agent for the Memorax smart glasses system. 
To answer a query, you MUST use the following ReAct format:

Thought: Explain your reasoning and what you need to do next based on the user's request.
Action: Call a tool if needed. 
Observation: (The system will automatically execute the tool and provide the result).

You must continue generating Thoughts and Actions until you have completely satisfied the user's request. 
Keep your spoken responses concise, natural, and helpful for someone wearing smart glasses.
Once you are ready to speak to the user, you MUST start your final response with exactly:
Final Answer: [The exact words you want the Text-to-Speech engine to say]"""

        self.start_new_chat()

    def _rotate_credentials(self):
        """Rotates API keys and models if a rate limit or error occurs during the live demo."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            print(f"[FAILOVER] Switched to backup API Key #{self.current_key_index + 1}")
            self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
            
        self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
        print(f"[FAILOVER] Switched to model: {self.available_models[self.current_model_index]}")
        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        model_name = self.available_models[self.current_model_index]
        try:
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    system_instruction=self.react_prompt,
                    tools=[get_current_time, save_memory, find_object, search_notes, set_reminder],
                    temperature=0.3
                )
            )
        except Exception as e:
            print(f"[INIT ERROR] Could not start chat with {model_name}: {e}")

    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message, processes the ReAct loop, and returns only the final answer."""
        
        # STAGE 1: Zero-Latency Local Intent Router (Only when no image/audio is attached)
        if not image_path and not audio_path and user_text:
            clean_text = user_text.lower().strip()
            if clean_text in ["what time is it", "what time is it?", "tell me the time", "jarvis what time is it"]:
                now = datetime.datetime.now().strftime("%I:%M %p")
                return f"It is currently {now}."
            elif clean_text in ["hello", "hi", "hey jarvis", "jarvis", "hello jarvis"]:
                return "Hello! Memorax systems are online and ready. How can I help you?"

        message_content = [user_text]
        
        if image_path:
            try:
                img = Image.open(image_path)
                message_content.append(img)
            except Exception as error:
                return f"System Error: Could not open the image. {error}"
                
        if audio_path:
            try:
                print(f"[SYSTEM] Uploading audio file to Gemini: {audio_path}")
                audio_file = self.client.files.upload(file=audio_path)
                message_content.append(audio_file)
            except Exception as error:
                return f"System Error: Could not upload the audio. {error}"

        # Start the ReAct Parsing Loop
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            try:
                response = self.chat.send_message(message_content)
                
                print(f"\n[AI INTERNAL THOUGHT]\n{response.text}\n")
                
                if response.text and "Final Answer:" in response.text:
                    final_text = response.text.split("Final Answer:")[-1].strip()
                    return final_text
                elif response.text:
                    # Even if the model forgot the exact "Final Answer:" prefix, return clean text rather than failing
                    cleaned = response.text.replace("Thought:", "").strip()
                    if len(cleaned) > 0 and iteration >= 1:
                        return cleaned
                    message_content = ["Please provide the final spoken response now starting with 'Final Answer:'."]
                    iteration += 1
                else:
                    iteration += 1
                    
            except Exception as e:
                print(f"[AI ERROR] {e}. Rotating model/key...")
                self._rotate_credentials()
                iteration += 1
                    
        return "I processed that request, please check the console log for details."
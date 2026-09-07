import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

# NEW: Import the set_reminder tool
from core.tools import get_current_time, save_memory, find_object, search_notes, set_reminder

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Lock in the correct 3.6 model to avoid 404 errors
        self.available_models = [
            "gemini-3.6-flash"
        ]
            
        self.current_model_index = 0
        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        if self.current_model_index < len(self.available_models):
            model_name = self.available_models[self.current_model_index]
            
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    # Add set_reminder to the AI's toolbelt!
                    tools=[get_current_time, save_memory, find_object, search_notes, set_reminder] 
                )
            )

    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message (and optionally an image or audio)."""
        
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

        while self.current_model_index < len(self.available_models):
            try:
                response = self.chat.send_message(message_content)
                return response.text
                
            except Exception as e:
                print(f"[AI ERROR] {e}. Trying next model...")
                self.current_model_index += 1
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                
        self.current_model_index = 0
        self.start_new_chat()
        
        return "Servers are a little busy, please wait."
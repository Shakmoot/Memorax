import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

from core.tools import get_current_time, save_memory, find_object

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # FIX: We bypass dynamic fetching to avoid deprecated models.
        # Hardcoding the explicitly supported 3.6 models prevents the 404 errors.
        self.available_models = [
            "gemini-3.6-flash",
            "gemini-3.6-pro"
        ]
            
        self.current_model_index = 0
        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model and tools."""
        if self.current_model_index < len(self.available_models):
            model_name = self.available_models[self.current_model_index]
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    # Includes all tools: time, saving memories, and finding objects
                    tools=[get_current_time, save_memory, find_object] 
                )
            )

    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message (and optionally an image or audio), with silent fallback."""
        
        # Bundle text, image, and audio together if provided
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
                # Send the message (which might now include media!)
                response = self.chat.send_message(message_content)
                return response.text
                
            except Exception as e:
                print(f"[AI ERROR] {e}. Trying next model...")
                # Fallback to the next model if it fails
                self.current_model_index += 1
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                
        # If all models fail, reset back to the primary model for the next attempt
        self.current_model_index = 0
        self.start_new_chat()
        
        return "Servers are a little busy, please wait."

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting AI Assistant...\n")
    assistant = AIAssistant()
    
    print("User: Can you tell me exactly what time it is right now?")
    reply1 = assistant.ask_question("Can you tell me exactly what time it is right now?")
    print("AI:", reply1, "\n")
    
    # NEW TEST: Vision!
    # Because you are running the terminal from the main folder, the path is core/test_image.jpg
    print("User: [Sends image] What is in this image?")
    reply2 = assistant.ask_question("What is in this image? Describe it briefly.", image_path="core/test_image.jpg")
    print("AI:", reply2, "\n")
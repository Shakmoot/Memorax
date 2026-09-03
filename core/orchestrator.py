import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image  # NEW: Import the Pillow library to read images

from tools import get_current_time

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Fetch ALL available models dynamically
        self.available_models = []
        for model in self.client.models.list():
            if 'gemini' in model.name:
                self.available_models.append(model.name)
                
        if not self.available_models:
            self.available_models = ['gemini-3.6-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
            
        self.current_model_index = 0
        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        if self.current_model_index < len(self.available_models):
            model_name = self.available_models[self.current_model_index]
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    tools=[get_current_time] 
                )
            )

    def ask_question(self, user_text, image_path=None):
        """Sends a message (and optionally an image), with silent fallback."""
        
        # NEW: Bundle text and image together if an image is provided
        message_content = user_text
        if image_path:
            try:
                # Open the image file from your computer
                img = Image.open(image_path)
                # Google's library accepts a list of [Text, Image]
                message_content = [user_text, img]
            except Exception as error:
                return f"System Error: Could not open the image. {error}"

        while self.current_model_index < len(self.available_models):
            try:
                # Send the message (which might now include an image!)
                response = self.chat.send_message(message_content)
                return response.text
                
            except Exception:
                # Fallback to the next model if it fails
                self.current_model_index += 1
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                
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
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import both of our tools
from core.tools import get_current_time, get_weather

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Fetch ALL available models dynamically directly from Google
        self.available_models = []
        for model in self.client.models.list():
            if 'gemini' in model.name:
                self.available_models.append(model.name)
                
        # Fallback just in case the API fails to list models
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
                    # Register BOTH tools here!
                    tools=[get_current_time, get_weather] 
                )
            )

    def ask_question(self, user_text, media_path=None):
        """Sends a message, optionally attaching an image or audio file, with silent fallback."""
        
        message_content = user_text
        
        # If the user passed a file (Image or Audio)
        if media_path:
            try:
                # Upload the media file directly to Google's servers
                media_file = self.client.files.upload(file=media_path)
                # Bundle the text and the uploaded media together
                message_content = [user_text, media_file]
            except Exception as error:
                return f"System Error: Could not process the media file. {error}"

        while self.current_model_index < len(self.available_models):
            try:
                # TRY to send the message to the current model
                response = self.chat.send_message(message_content)
                return response.text
                
            except Exception:
                # EXCEPT: Move to the next model silently if it fails
                self.current_model_index += 1
                
                # Start a new chat with the new model
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                
        # If all models fail, reset back to the first model for the next question
        self.current_model_index = 0
        self.start_new_chat()
        
        return "Servers are a little busy, please wait."

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting AI Assistant...\n")
    assistant = AIAssistant()
    
    # Let's test the AI's ability to use its new tool!
    print("User: Should I wear a jacket in Kochi, Kerala right now?")
    reply = assistant.ask_question("Should I wear a jacket in Kochi, Kerala right now?")
    print("AI:", reply, "\n")
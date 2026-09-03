import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from tools import get_current_time

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # 1. Fetch ALL available models dynamically directly from Google
        self.available_models = []
        for model in self.client.models.list():
            # We only want 'gemini' text/chat models (ignore search/embedding models)
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
                    tools=[get_current_time] 
                )
            )

    def ask_question(self, user_text):
        """Sends a message, automatically trying ALL backup models silently if needed."""
        
        while self.current_model_index < len(self.available_models):
            try:
                # TRY to send the message to the current model
                response = self.chat.send_message(user_text)
                return response.text
                
            except Exception:
                # EXCEPT: The server rejected us (or the specific model doesn't support tools)
                # The print statement has been removed. It will now fail silently.
                
                # Move to the next model in our massive list
                self.current_model_index += 1
                
                # Start a new chat with the new model
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                
        # If the loop finishes and EVERY SINGLE model failed:
        # Reset back to the first model for the next question
        self.current_model_index = 0
        self.start_new_chat()
        
        return "Servers are a little busy, please wait."

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting AI Assistant...\n")
    assistant = AIAssistant()
    
    print("User: Hello, who are you?")
    reply1 = assistant.ask_question("Hello, who are you?")
    print("AI:", reply1, "\n")
    
    print("User: Can you tell me exactly what time it is right now?")
    reply2 = assistant.ask_question("Can you tell me exactly what time it is right now?")
    print("AI:", reply2, "\n")
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from PIL import Image

from core.tools import get_current_time, save_memory, find_object, search_notes, set_reminder

class AIAssistant:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.available_models = ["gemini-3.6-flash"]
        self.current_model_index = 0
        
        # NEW: The ReAct System Instruction
        self.react_prompt = """You are an autonomous AI agent for a smart glasses system. 
To answer a query, you MUST use the following ReAct format:

Thought: Explain your reasoning and what you need to do next based on the user's request.
Action: Call a tool if needed. 
Observation: (The system will automatically execute the tool and provide the result).

You must continue generating Thoughts and Actions until you have completely satisfied the user's request. 
Once you are ready to speak to the user, you MUST start your final response with exactly:
Final Answer: [The exact words you want the Text-to-Speech engine to say]"""

        self.start_new_chat()

    def start_new_chat(self):
        """Creates a new chat session using the currently selected model."""
        if self.current_model_index < len(self.available_models):
            model_name = self.available_models[self.current_model_index]
            
            self.chat = self.client.chats.create(
                model=model_name, 
                config=types.GenerateContentConfig(
                    system_instruction=self.react_prompt,
                    # We pass the tools directly; the SDK handles the execution loop automatically!
                    tools=[get_current_time, save_memory, find_object, search_notes, set_reminder],
                    temperature=0.3 # Lower temperature keeps the reasoning logical and structured
                )
            )

    def ask_question(self, user_text, image_path=None, audio_path=None):
        """Sends a message, processes the ReAct loop, and returns only the final answer."""
        
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
                # Send the message. If the AI calls a tool, the SDK handles the observation cycle.
                response = self.chat.send_message(message_content)
                
                # Print the AI's internal monologue to the console for debugging
                print(f"\n[AI INTERNAL THOUGHT]\n{response.text}\n")
                
                # Check if the AI has reached a conclusion
                if "Final Answer:" in response.text:
                    # Extract only the final words for the TTS engine
                    final_text = response.text.split("Final Answer:")[-1].strip()
                    return final_text
                else:
                    # If the AI forgot to use the Final Answer tag, gently push it to conclude
                    message_content = ["You have not provided a final answer. Please conclude with 'Final Answer: [your response]'."]
                    iteration += 1
                    
            except Exception as e:
                print(f"[AI ERROR] {e}. Trying next model...")
                self.current_model_index += 1
                if self.current_model_index < len(self.available_models):
                    self.start_new_chat()
                else:
                    self.current_model_index = 0
                    self.start_new_chat()
                    return "Servers are a little busy, please wait."
                    
        return "I'm sorry, I got stuck thinking and couldn't formulate a final answer."
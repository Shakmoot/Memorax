import os
from core.orchestrator import AIAssistant

class VisionService:
    def __init__(self, ai_assistant):
        # We pass the main AI Assistant into this service so it can use the AI's brain
        self.assistant = ai_assistant

    def describe_scene(self, image_path):
        """Asks the AI to describe what it sees generally."""
        prompt = "Describe what you see in this image in one brief sentence."
        return self.assistant.ask_question(prompt, image_path)

    def extract_text(self, image_path):
        """OCR: Extracts exact text from an image without commentary."""
        prompt = "Extract all the text from this image exactly as written. Do not add any extra commentary."
        return self.assistant.ask_question(prompt, image_path)

    def translate_image_text(self, image_path, target_language="English"):
        """Extracts text and translates it to the target language."""
        prompt = f"Please read the text in this image and translate it into {target_language}. Return only the translation."
        return self.assistant.ask_question(prompt, image_path)

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Starting Vision Service...\n")
    
    # 1. Boot up our main AI brain
    brain = AIAssistant()
    
    # 2. Hand the brain to our new Vision Service
    vision = VisionService(brain)
    
    # 3. Test OCR and Translation!
    image_file = "core/foreign_sign.jpg"
    
    if os.path.exists(image_file):
        print("--- EXTRACTING TEXT (OCR) ---")
        extracted = vision.extract_text(image_file)
        print(extracted, "\n")
        
        print("--- TRANSLATING TO ENGLISH ---")
        translation = vision.translate_image_text(image_file, target_language="English")
        print(translation, "\n")
    else:
        print(f"Error: Could not find {image_file}. Did you download it and put it in the core folder?")
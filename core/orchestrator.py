class AIAssistant:
    def __init__(self):
        print("[MOCK AI] Initialized successfully.")

    def get_response(self, user_text: str) -> str:
        if "time" in user_text.lower():
            return "[MOCK AI] You asked for the time. I am triggering a tool."
        return f"[MOCK AI] I received your text message: '{user_text}'"

    def process_image(self, image_path: str) -> str:
        """Simulates analyzing an image using computer vision."""
        import os
        if os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            # In the real app, we would send this file to Gemini Vision here
            return f"[MOCK AI] I successfully analyzed the image! (Size: {file_size} bytes). I see a coffee cup."
        else:
            return "[MOCK AI] Error: The image file was not found."
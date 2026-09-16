import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

class VisionService:
    def __init__(self, ai_assistant=None):
        # 1. Keep the Gemini Brain
        self.assistant = ai_assistant
        
        # 2. Initialize the NVIDIA Brain
        load_dotenv()
        self.nvidia_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )
        
        # 3. State Tracker: Who is our primary provider right now?
        self.current_provider = "gemini"

    def _encode_image(self, image_path):
        """Helper to convert images to Base64 for NVIDIA's API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _ask_gemini(self, prompt, image_path):
        """Attempts to use Gemini."""
        if not self.assistant:
            raise Exception("Gemini Assistant not connected.")
            
        result = self.assistant.ask_question(prompt, media_path=image_path)
        
        # If your Orchestrator hits a rate limit, it returns this string.
        # We catch it and throw an error so the failover system triggers.
        if "Servers are a little busy" in result or "System Error" in result:
            raise Exception("Gemini quota or server limit reached.")
            
        return result

    def _ask_nvidia(self, prompt, image_path):
        """Attempts to use NVIDIA PaliGemma."""
        base64_image = self._encode_image(image_path)
        response = self.nvidia_client.chat.completions.create(
            model="google/paligemma",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}],
            max_tokens=256,
            temperature=0.2
        )
        return response.choices[0].message.content

    def _execute_with_failover(self, prompt, image_path):
        """
        The Dual-Engine Router:
        Tries the current provider. If it fails, flips the switch to the 
        backup provider and immediately tries again silently.
        """
        if self.current_provider == "gemini":
            try:
                return self._ask_gemini(prompt, image_path)
            except Exception as e:
                print(f"[VisionService] Gemini failed: {e} \n-> Switching to NVIDIA PaliGemma.")
                self.current_provider = "nvidia"  # Flip the switch!
                return self._ask_nvidia(prompt, image_path)
                
        elif self.current_provider == "nvidia":
            try:
                return self._ask_nvidia(prompt, image_path)
            except Exception as e:
                print(f"[VisionService] NVIDIA failed: {e} \n-> Switching back to Gemini.")
                self.current_provider = "gemini"  # Flip the switch back!
                return self._ask_gemini(prompt, image_path)

    # --- PUBLIC API TASKS ---

    def describe_scene(self, image_path):
        prompt = "Describe what you see in this image in one brief sentence."
        return self._execute_with_failover(prompt, image_path)

    def extract_text(self, image_path):
        prompt = "Extract all the text from this image exactly as written. Do not add any extra commentary."
        return self._execute_with_failover(prompt, image_path)

    def translate_image_text(self, image_path, target_language="English"):
        prompt = f"Please read the text in this image and translate it into {target_language}. Return only the translation."
        return self._execute_with_failover(prompt, image_path)
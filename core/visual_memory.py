import json
import os
from core.orchestrator import AIAssistant
from core.tools import save_memory


import base64
from openai import OpenAI
from dotenv import load_dotenv

class VisualMemoryService:
    def __init__(self, ai_assistant: AIAssistant):
        self.assistant = ai_assistant

    def _encode_image(self, image_path):
        """Helper to convert images to Base64 for NVIDIA's API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_visual_entities(self, image_path):
        import requests 
        import os
        from dotenv import load_dotenv
        
        prompt = "List the main objects you see in this image and their exact locations. Format as: 'object name -> location description'"
        
        # 1. Try Gemini First
        raw_response = self.assistant.ask_question(prompt, image_path=image_path)
        
        # 2. The Tripwire: If Gemini is rate-limited, switch to NVIDIA NIM
        if "Servers are a little busy" in raw_response or "System Error" in raw_response:
            print("[Visual Memory] Gemini API limit reached! Rerouting to NVIDIA NIM...")
            
            load_dotenv()
            api_key = os.getenv("NVIDIA_API_KEY")
            base64_image = self._encode_image(image_path)
            
            try:
                # Direct REST call
                url = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "google/paligemma", # Update this if the NVIDIA API Reference tab showed a different string
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    "max_tokens": 256,
                    "temperature": 0.2
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    raw_response = response.json()["choices"][0]["message"]["content"]
                else:
                    print(f"[Visual Memory] NVIDIA failed with status {response.status_code}: {response.text}")
                    raw_response = ""
                    
            except Exception as e:
                print(f"[Visual Memory] NVIDIA request failed: {e}")
                raw_response = ""

        # --- THE FIX: Parse the raw string into a list of dictionaries ---
        parsed_items = []
        if raw_response:
            for line in raw_response.split('\n'):
                if '->' in line:
                    parts = line.split('->')
                    obj_name = parts[0].strip()
                    loc_desc = parts[1].strip()
                    parsed_items.append({"object": obj_name, "location": loc_desc})
                    
        return parsed_items

    def process_camera_snapshot(self, image_path: str, memory_callback=None):
        """
        Processes a snapshot from the 'img' command and logs discovered items.
        If a memory_callback function is provided (e.g. your Team Lead's save_memory),
        it calls it automatically for each detected item.
        """
        print(f"[VisualMemory] Analyzing scene snapshot: {image_path}...")
        detected_items = self.extract_visual_entities(image_path)

        if not detected_items:
            print("[VisualMemory] No notable objects detected.")
            return []

        print(f"[VisualMemory] Detected {len(detected_items)} objects:")
        for item in detected_items:
            obj = item.get("object")
            loc = item.get("location")
            print(f"  • {obj} -> {loc}")

            # If the team's SQLite save function is passed in, call it directly:
            if memory_callback and callable(memory_callback):
                # Pass a descriptive string to satisfy the tool's requirements!
                memory_callback(object_name=obj, location=loc, description=f"Automatically spotted {obj} at {loc}")

        return detected_items

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("Initializing Visual Memory Service...\n")
    brain = AIAssistant()
    service = VisualMemoryService(brain)

    # Use any test photo with objects on a desk or table
    # You can reuse the foreign_sign.jpg or drop a quick desk photo named 'desk_test.jpg'
    test_image = "core/desk_test.jpg"

    if os.path.exists(test_image):
        # Mock memory callback to demonstrate how it feeds the Team Lead's database
        def mock_save_memory(object_name, location):
            print(f"  [Mock DB] Saved to SQLite: '{object_name}' at '{location}'")

        service.process_camera_snapshot(test_image, memory_callback=save_memory)
    else:
        print(f"To test: Place a photo with a few objects (phone, keys, cup) at '{test_image}' and re-run.")
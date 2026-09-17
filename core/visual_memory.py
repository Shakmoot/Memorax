import json
import os
from core.orchestrator import AIAssistant
from core.tools import save_memory

class VisualMemoryService:
    def __init__(self, ai_assistant: AIAssistant):
        self.assistant = ai_assistant

    def extract_visual_entities(self, image_path: str):
        """
        Analyzes a photo and extracts key everyday objects and their spatial context.
        Returns a list of dicts: [{'object': 'keys', 'location': 'wooden desk next to laptop'}]
        """
        if not os.path.exists(image_path):
            return {"error": f"Image file not found at {image_path}"}

        prompt = """
        Analyze this image taken from smart glasses. 
        Identify any distinct everyday items (e.g., keys, wallet, phone, notebook, water bottle, glasses, backpack, chargers).
        For each item, describe its precise location relative to nearby furniture or landmarks.

        Return STRICT raw JSON (no markdown formatting, no backticks, no extra text) as a list of objects:
        [
          {
            "object": "name of object",
            "location": "concise description of where it is resting or located"
          }
        ]
        If no distinct portable items are clearly visible, return an empty list: []
        """

        raw_response = self.assistant.ask_question(prompt, image_path=image_path)
        
        # Clean up potential markdown formatting if the model adds ```json ... ```
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("\n", 1)[0]
        cleaned = cleaned.strip()

        try:
            items = json.loads(cleaned)
            return items if isinstance(items, list) else []
        except json.JSONDecodeError:
            print(f"[Warning] Failed to parse JSON from visual response: {raw_response}")
            return []

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
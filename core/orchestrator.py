class AIAssistant:
    def __init__(self):
        print("[MOCK AI] Initialized successfully.")

    def get_response(self, user_text: str) -> str:
        # Simulate processing time or basic tool logic
        if "time" in user_text.lower():
            return "[MOCK AI] You asked for the time. I am triggering a tool."
        
        return f"[MOCK AI] I received your message: '{user_text}'"
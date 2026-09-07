import threading
import time

class ReminderService:
    def __init__(self):
        self.reminders = []
        self.callback = None
        self.running = False

    def set_callback(self, callback):
        """Attaches a function to run when a reminder triggers."""
        self.callback = callback

    def add_reminder(self, delay_seconds: float, message: str):
        """Calculates the exact future time to trigger the reminder."""
        trigger_time = time.time() + delay_seconds
        self.reminders.append((trigger_time, message))
        print(f"[SYSTEM] Background task scheduled to trigger in {delay_seconds} seconds.")

    def start(self):
        """Starts the infinite background loop in a separate thread."""
        if not self.running:
            self.running = True
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        """Continuously checks if any reminder's time has arrived."""
        while self.running:
            current_time = time.time()
            
            # Iterate over a copy of the list to safely remove items while looping
            for reminder in self.reminders[:]:
                trigger_time, message = reminder
                
                if current_time >= trigger_time:
                    self.reminders.remove(reminder)
                    if self.callback:
                        self.callback(message)
                        
            # Sleep for 1 second to prevent the loop from maxing out the CPU
            time.sleep(1)
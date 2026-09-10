import customtkinter as ctk

# Set the overall appearance to dark mode, which fits our AI glasses theme.
ctk.set_appearance_mode("dark")
# Set the default color for our interactive elements (buttons, sliders) to blue.
ctk.set_default_color_theme("blue")

# This creates the actual window that will pop up on your screen.
app = ctk.CTk()
app.geometry("400x300") # Sets the width and height of the window
app.title("Smart Glasses - Control Panel") # The title at the top of the window

def wake_ai_clicked():
    # This is a "dummy" function. For now, it just prints a message to your terminal.
    # Later, we will connect this to the actual AI backend!
    print("Wake Assistant button was clicked! The AI is now listening...")

# NEW: Function to handle the Meeting Mode toggle
def meeting_mode_toggled():
    if meeting_switch.get() == 1:
        print("Meeting Mode ON: Recording and transcribing...")
    else:
        print("Meeting Mode OFF.")

# NEW: Status Label (Goal 3) using a red circle emoji for "Disconnected"
status_label = ctk.CTkLabel(
    master=app,
    text="Status: 🔴 Disconnected",
    font=("Roboto", 18)
)
status_label.pack(pady=(20, 10)) # Adds spacing above and below

# We create a button, attach it to our 'app' window, give it text, and tell it what function to run.
wake_button = ctk.CTkButton(
    master=app, 
    text="Wake Assistant", 
    command=wake_ai_clicked,
    font=("Roboto", 20, "bold"), # Make the font large and bold
    width=200,                   # Make the button wide
    height=60,                   # Make the button tall
    corner_radius=30             # Give it nice, smooth, rounded edges
)
wake_button.pack(pady=20) # Changed from expand=True so we can stack multiple items

# NEW: Meeting Mode Toggle Switch (Goal 2)
meeting_switch = ctk.CTkSwitch(
    master=app,
    text="Meeting Mode",
    command=meeting_mode_toggled,
    font=("Roboto", 16)
)
meeting_switch.pack(pady=20)

# This keeps the window open on your screen until you close it.
if __name__ == "__main__":
    app.mainloop()
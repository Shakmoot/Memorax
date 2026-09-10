import customtkinter as ctk

# Set the theme to dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Create the main window
app = ctk.CTk()
app.title("AI Smart Glasses - Companion App")
app.geometry("600x700") # Made the window slightly bigger for our tabs

# --- HARDWARE STATUS BAR (Always visible at the top) ---
status_frame = ctk.CTkFrame(master=app, fg_color="transparent")
status_frame.pack(pady=(15, 5), fill="x", padx=25)

status_label = ctk.CTkLabel(master=status_frame, text="🔴 Glasses Disconnected", text_color="red", font=("Arial", 14, "bold"))
status_label.pack(side="left")

is_connected = False

def toggle_connection():
    global is_connected 
    is_connected = not is_connected 
    
    chat_history.configure(state="normal")
    
    if is_connected:
        status_label.configure(text="🟢 Glasses Connected", text_color="#2ecc71")
        connect_button.configure(text="Disconnect")
        chat_history.insert("end", "System: Glasses connected successfully via TCP.\n\n")
    else:
        status_label.configure(text="🔴 Glasses Disconnected", text_color="red")
        connect_button.configure(text="Connect")
        chat_history.insert("end", "System: Glasses disconnected.\n\n")
        
    chat_history.configure(state="disabled")
    chat_history.see("end")

connect_button = ctk.CTkButton(master=status_frame, text="Connect", width=80, command=toggle_connection)
connect_button.pack(side="right")

# --- NEW: TABVIEW (The main container for our different screens) ---
# Create the tab container and put it in the main app
tabview = ctk.CTkTabview(master=app, width=550, height=550)
tabview.pack(pady=10, padx=20)

# Add our three tabs
tabview.add("Live Chat")
tabview.add("Memory Inspector")
tabview.add("Document Manager")

# --- TAB 1: LIVE CHAT ---
# Notice how the 'master' for these chat items is now the "Live Chat" tab!

chat_history = ctk.CTkTextbox(master=tabview.tab("Live Chat"), width=500, height=400)
chat_history.pack(pady=10) 

def send_message():
    user_text = input_box.get()
    if user_text.strip() == "":
        return 
        
    chat_history.configure(state="normal")
    chat_history.insert("end", f"You: {user_text}\n\n")
    chat_history.insert("end", f"AI: I heard you say '{user_text}'.\n\n")
    chat_history.configure(state="disabled")
    chat_history.see("end")
    input_box.delete(0, "end")

input_frame = ctk.CTkFrame(master=tabview.tab("Live Chat"), fg_color="transparent")
input_frame.pack(pady=10)

input_box = ctk.CTkEntry(master=input_frame, width=400, placeholder_text="Type your message...")
input_box.pack(side="left", padx=10)

send_button = ctk.CTkButton(master=input_frame, text="Send", width=80, command=send_message)
send_button.pack(side="left")

chat_history.insert("0.0", "System: AI Glasses Chat Interface Initialized...\n\n")
chat_history.configure(state="disabled")

# --- TAB 2: MEMORY INSPECTOR (Placeholder for now) ---
memory_label = ctk.CTkLabel(master=tabview.tab("Memory Inspector"), text="Database Memory will go here!", font=("Arial", 18))
memory_label.pack(pady=50)

# --- TAB 3: DOCUMENT MANAGER (Placeholder for now) ---
doc_label = ctk.CTkLabel(master=tabview.tab("Document Manager"), text="Drag & Drop PDFs here later!", font=("Arial", 18))
doc_label.pack(pady=50)

# Start the application loop
app.mainloop()
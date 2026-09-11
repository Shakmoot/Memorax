import customtkinter as ctk
import os # We import this to help us easily read file names

# Set the theme to dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Create the main window
app = ctk.CTk()
app.title("AI Smart Glasses - Companion App")
app.geometry("600x700")

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

# --- TABVIEW (The main container for our different screens) ---
tabview = ctk.CTkTabview(master=app, width=550, height=550)
tabview.pack(pady=10, padx=20)

tabview.add("Live Chat")
tabview.add("Memory Inspector")
tabview.add("Document Manager")

# --- TAB 1: LIVE CHAT ---
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

# --- TAB 2: MEMORY INSPECTOR ---
memory_scroll_frame = ctk.CTkScrollableFrame(master=tabview.tab("Memory Inspector"), width=500, height=450)
memory_scroll_frame.pack(pady=10)

dummy_memories = [
    {"time": "09:15 AM", "text": "Keys left on the kitchen counter."},
    {"time": "10:30 AM", "text": "Meeting with Sarah scheduled for Thursday at 2 PM."},
    {"time": "01:45 PM", "text": "Spotted a rare bird outside the window."},
    {"time": "04:20 PM", "text": "Remember to buy milk on the way home."}
]

for memory in dummy_memories:
    memory_card = ctk.CTkFrame(master=memory_scroll_frame, fg_color="#2b2b2b", corner_radius=10)
    memory_card.pack(pady=5, fill="x", padx=10)
    
    time_label = ctk.CTkLabel(master=memory_card, text=memory["time"], text_color="gray", font=("Arial", 12))
    time_label.pack(side="left", padx=10, pady=10)
    
    text_label = ctk.CTkLabel(master=memory_card, text=memory["text"], font=("Arial", 14), wraplength=350, justify="left")
    text_label.pack(side="left", padx=10, pady=10)

# --- TAB 3: DOCUMENT MANAGER ---
doc_frame = ctk.CTkFrame(master=tabview.tab("Document Manager"), fg_color="transparent")
doc_frame.pack(pady=20, fill="both", expand=True)

# A visual list to hold our uploaded documents
doc_list_frame = ctk.CTkScrollableFrame(master=doc_frame, width=450, height=300, label_text="Uploaded Study Materials")
doc_list_frame.pack(pady=10)

def upload_document():
    # This opens your computer's file explorer!
    filepath = ctk.filedialog.askopenfilename(
        title="Select a PDF",
        filetypes=[("PDF files", "*.pdf")]
    )
    
    # If the user actually selected a file (and didn't hit cancel)
    if filepath:
        # Get just the name of the file (e.g., "homework.pdf")
        filename = os.path.basename(filepath)
        
        # Add a new label to our document list
        new_doc = ctk.CTkLabel(master=doc_list_frame, text=f"📄 {filename}", font=("Arial", 14))
        new_doc.pack(anchor="w", pady=5, padx=10)
        
        # Add a helpful message to the Live Chat!
        chat_history.configure(state="normal")
        chat_history.insert("end", f"System: Document '{filename}' queued for AI Study Mode.\n\n")
        chat_history.configure(state="disabled")
        chat_history.see("end")

# The button that triggers the upload function
upload_button = ctk.CTkButton(master=doc_frame, text="Browse for PDF", command=upload_document, font=("Arial", 14, "bold"))
upload_button.pack(pady=20)

# Start the application loop
app.mainloop()
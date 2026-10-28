import os
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CompanionApp(ctk.CTk):
    def __init__(self, on_message, on_wake, on_meeting, on_upload, on_test_vision=None, on_ocr_clipboard=None):
        super().__init__()
        
        # Attach the callback functions passed from main.py
        self.on_message = on_message
        self.on_wake = on_wake
        self.on_meeting = on_meeting
        self.on_upload = on_upload
        self.on_test_vision = on_test_vision
        self.on_ocr_clipboard = on_ocr_clipboard
        
        self.title("Memorax Smart Glasses - Live Demo Command Center")
        self.geometry("780x820")
        
        self._build_header()
        self._build_demo_bar()
        self._build_tabs()
        
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(15, 5), fill="x", padx=25)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            self.header_frame, 
            text="🟢 System Ready (Standby)", 
            text_color="#2ecc71", 
            font=("Roboto", 16, "bold")
        )
        self.status_label.pack(side="left")
        
        # Meeting Mode Toggle
        self.meeting_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Meeting Recording Mode",
            command=self._meeting_toggled,
            font=("Roboto", 14, "bold")
        )
        self.meeting_switch.pack(side="right", padx=10)
        
        # Wake Button
        self.wake_button = ctk.CTkButton(
            self, 
            text="🎙️ Wake Jarvis (Listen)", 
            command=self.on_wake,
            font=("Roboto", 18, "bold"),
            width=240, height=48, corner_radius=24,
            fg_color="#0284c7", hover_color="#0369a1"
        )
        self.wake_button.pack(pady=8)

    def _build_demo_bar(self):
        """1-Click Demo Deck so judges or presenters can trigger features reliably."""
        demo_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        demo_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(
            demo_frame, 
            text="⚡ Judge Demo Quick-Triggers:", 
            font=("Roboto", 13, "bold"),
            text_color="#38bdf8"
        ).pack(side="left", padx=12, pady=8)
        
        ctk.CTkButton(
            demo_frame, text="🌐 Translate / Vision", width=130, height=32,
            fg_color="#0f766e", hover_color="#115e59",
            command=self._trigger_vision_demo
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkButton(
            demo_frame, text="📋 OCR to Clipboard", width=130, height=32,
            fg_color="#4f46e5", hover_color="#4338ca",
            command=self._trigger_ocr_demo
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkButton(
            demo_frame, text="🔑 Find My Keys", width=110, height=32,
            fg_color="#b45309", hover_color="#92400e",
            command=lambda: self._quick_query("Where did I leave my keys?")
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkButton(
            demo_frame, text="📚 Summarize Notes", width=130, height=32,
            fg_color="#6d28d9", hover_color="#5b21b6",
            command=lambda: self._quick_query("Search my study notes and give me the key takeaways.")
        ).pack(side="left", padx=5, pady=8)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, width=720, height=580)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.tabview.add("Live Chat & Vision")
        self.tabview.add("Memory Inspector")
        self.tabview.add("Document Manager (RAG)")
        
        self._build_chat_tab()
        self._build_memory_tab()
        self._build_doc_tab()

    def _build_chat_tab(self):
        tab = self.tabview.tab("Live Chat & Vision")
        
        # Top split: Chat on left, Vision Preview on right
        content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        content_frame.pack(pady=5, fill="both", expand=True)
        
        self.chat_history = ctk.CTkTextbox(content_frame, wrap="word", font=("Roboto", 14))
        self.chat_history.pack(side="left", padx=(0, 10), fill="both", expand=True)
        self.chat_history.insert("0.0", "System: Memorax AI Glasses Initialized. Ready for voice, vision, or text queries...\n\n")
        self.chat_history.configure(state="disabled")
        
        # Image Preview Card
        self.vision_frame = ctk.CTkFrame(content_frame, width=220, fg_color="#1e293b", corner_radius=10)
        self.vision_frame.pack(side="right", fill="y")
        self.vision_frame.pack_propagate(False)
        
        ctk.CTkLabel(self.vision_frame, text="📷 Latest Camera Feed", font=("Roboto", 13, "bold"), text_color="#38bdf8").pack(pady=(10, 5))
        
        self.image_label = ctk.CTkLabel(self.vision_frame, text="No image captured yet.\n\nTap glasses button or\nclick 'Translate / Vision'", text_color="gray", font=("Roboto", 12))
        self.image_label.pack(pady=20, padx=10, fill="both", expand=True)
        
        # Bottom Input Box
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.pack(pady=8, fill="x")
        
        self.input_box = ctk.CTkEntry(input_frame, placeholder_text="Ask Jarvis anything (or press Enter)...", height=38, font=("Roboto", 14))
        self.input_box.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.input_box.bind("<Return>", lambda event: self._send_message())
        
        send_button = ctk.CTkButton(input_frame, text="Send", width=90, height=38, font=("Roboto", 14, "bold"), command=self._send_message)
        send_button.pack(side="right")

    def _build_memory_tab(self):
        tab = self.tabview.tab("Memory Inspector")
        self.memory_scroll = ctk.CTkScrollableFrame(tab, label_text="SQLite Long-Term Object & Event Memories")
        self.memory_scroll.pack(pady=10, fill="both", expand=True)
        
        self.add_memory_card("09:15 AM", "Keys left on the kitchen counter.")

    def _build_doc_tab(self):
        tab = self.tabview.tab("Document Manager (RAG)")
        self.doc_list = ctk.CTkScrollableFrame(tab, label_text="Uploaded ChromaDB Study Materials")
        self.doc_list.pack(pady=10, fill="both", expand=True)
        
        upload_btn = ctk.CTkButton(tab, text="📄 Browse & Ingest PDF for RAG", command=self._upload_doc, font=("Roboto", 15, "bold"), height=42)
        upload_btn.pack(pady=10)

    def _quick_query(self, query_text):
        self.append_chat("You (Demo Trigger)", query_text)
        if self.on_message:
            self.on_message(query_text)

    def _trigger_vision_demo(self):
        filepath = ctk.filedialog.askopenfilename(
            title="Select Image to Translate or Analyze",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if filepath and self.on_test_vision:
            self.show_image_preview(filepath)
            self.on_test_vision(filepath)

    def _trigger_ocr_demo(self):
        filepath = ctk.filedialog.askopenfilename(
            title="Select Image to Extract Text to Clipboard",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")]
        )
        if filepath and self.on_ocr_clipboard:
            self.show_image_preview(filepath)
            self.on_ocr_clipboard(filepath)

    def show_image_preview(self, image_path):
        """Displays the captured or selected photo inside the UI right panel."""
        def update():
            if os.path.exists(image_path):
                try:
                    pil_img = Image.open(image_path)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(195, 195))
                    self.image_label.configure(image=ctk_img, text="")
                    self.image_label.image = ctk_img
                except Exception as e:
                    print(f"[UI] Could not preview image: {e}")
        self.after(0, update)

    def _send_message(self):
        text = self.input_box.get()
        if text.strip():
            self.append_chat("You", text)
            self.input_box.delete(0, "end")
            if self.on_message:
                self.on_message(text)

    def _meeting_toggled(self):
        is_on = self.meeting_switch.get() == 1
        if self.on_meeting:
            self.on_meeting(is_on)

    def _upload_doc(self):
        filepath = ctk.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filepath:
            filename = os.path.basename(filepath)
            ctk.CTkLabel(self.doc_list, text=f"✅ {filename} (Indexed in ChromaDB)", font=("Roboto", 14)).pack(anchor="w", pady=5, padx=10)
            self.append_chat("System", f"Uploading and indexing '{filename}' into ChromaDB...")
            if self.on_upload:
                self.on_upload(filepath)

    def append_chat(self, sender, message):
        """Thread-safe way to add text to the chat box."""
        def update():
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"{sender}: {message}\n\n")
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")
        self.after(0, update)

    def set_connection_status(self, is_connected):
        """Updates the hardware status indicator."""
        def update():
            if is_connected:
                self.status_label.configure(text="🟢 Glasses Connected (Active Stream)", text_color="#2ecc71")
            else:
                self.status_label.configure(text="🔴 Glasses Disconnected", text_color="red")
        self.after(0, update)

    def add_memory_card(self, time_str, text):
        """Adds a visual memory card to the inspector."""
        def update():
            card = ctk.CTkFrame(self.memory_scroll, fg_color="#2b2b2b", corner_radius=10)
            card.pack(pady=5, fill="x", padx=10)
            ctk.CTkLabel(card, text=time_str, text_color="#38bdf8", font=("Roboto", 12, "bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(card, text=text, font=("Roboto", 14), wraplength=480, justify="left").pack(side="left", padx=10, pady=10)
        self.after(0, update)
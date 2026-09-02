import socket
import threading

class GlassesServer:
    def __init__(self, host='0.0.0.0', port=65432, on_command_callback=None):
        self.host = host
        self.port = port
        self.on_command_callback = on_command_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False

    def start(self):
        """Starts the server in a background thread so it doesn't block the UI."""
        self.is_running = True
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[NETWORK] Glasses Server listening on {self.host}:{self.port}")
        
        # Create and start the background thread
        server_thread = threading.Thread(target=self._listen_loop, daemon=True)
        server_thread.start()

    def _listen_loop(self):
        """The infinite loop that waits for the ESP32 to connect."""
        while self.is_running:
            try:
                # This line blocks ONLY this background thread, not the main app
                client_socket, address = self.server_socket.accept()
                print(f"[NETWORK] Connection received from {address}")
                
                # Handle the client data
                self._handle_client(client_socket)
            except Exception as e:
                if self.is_running:
                    print(f"[NETWORK ERROR] {e}")

    def _handle_client(self, client_socket):
        """Reads the data sent by the ESP32."""
        with client_socket:
            # Receive up to 1024 bytes (fine for text commands, we'll need more for images later)
            data = client_socket.recv(1024)
            if data:
                command = data.decode('utf-8').strip()
                print(f"[NETWORK] Received command: {command}")
                
                # Pass the command to main.py to handle
                if self.on_command_callback:
                    self.on_command_callback(command)
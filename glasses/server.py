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
        """Reads the data sent by the ESP32 using a Header/Payload protocol."""
        with client_socket:
            try:
                # 1. Read the header one byte at a time until the newline
                header = b""
                while True:
                    char = client_socket.recv(1)
                    if not char or char == b'\n':
                        break
                    header += char
                
                if not header:
                    return

                header_text = header.decode('utf-8').strip()
                print(f"[NETWORK] Received header: {header_text}")
                
                # 2. Parse the command and the size of the payload
                if ":" in header_text:
                    command, size_str = header_text.split(":", 1)
                    payload_size = int(size_str)
                else:
                    command = header_text
                    payload_size = 0

                # 3. Read the exact number of bytes specified in the payload size
                payload = b""
                bytes_received = 0
                while bytes_received < payload_size:
                    # Read in chunks, but don't read more than what's left
                    chunk = client_socket.recv(min(4096, payload_size - bytes_received))
                    if not chunk:
                        raise ConnectionError("Socket closed before full payload was received.")
                    payload += chunk
                    bytes_received += len(chunk)

                # 4. Handle the specific command
                if command == "BUTTON_PRESS":
                    if self.on_command_callback:
                        self.on_command_callback("BUTTON_PRESS")
                        
                elif command == "IMAGE":
                    print(f"[NETWORK] Received complete image! Size: {len(payload)} bytes")
                    # Save the image payload to disk so the AI module can use it later
                    with open("latest_capture.jpg", "wb") as f:
                        f.write(payload)
                    print("[NETWORK] Image saved as 'latest_capture.jpg'")
                    if self.on_command_callback:
                        self.on_command_callback("IMAGE_RECEIVED")

            except Exception as e:
                print(f"[NETWORK ERROR] Failed to handle client data: {e}")
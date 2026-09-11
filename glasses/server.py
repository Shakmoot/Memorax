import socket
import threading

class GlassesServer:
    def __init__(self, port, on_command_callback):
        self.port = port
        self.on_command_callback = on_command_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow address reuse to prevent "Address already in use" errors if you restart quickly
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            client, addr = self.server_socket.accept()
            threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()

    def _handle_client(self, client_socket, addr):
        print(f"[NETWORK] Connection received from {addr}")
        try:
            # 1. Read the header character by character until newline
            header_data = b""
            while b"\n" not in header_data:
                chunk = client_socket.recv(1)
                if not chunk:
                    break
                header_data += chunk
            
            header_str = header_data.decode('utf-8').strip()
            print(f"[NETWORK] Received header: {header_str}")
            
            # 2. Parse the command and payload length
            if ":" in header_str:
                command, length_str = header_str.split(':', 1)
                payload_length = int(length_str)
            else:
                command = header_str
                payload_length = 0

            # 3. Route the commands
            if command == "IMAGE":
                # Read the binary image payload
                payload = b""
                while len(payload) < payload_length:
                    chunk = client_socket.recv(min(4096, payload_length - len(payload)))
                    if not chunk:
                        break
                    payload += chunk
                    
                # Save the image
                with open("latest_capture.jpg", "wb") as f:
                    f.write(payload)
                    
                # Trigger the callback in main.py
                self.on_command_callback("IMAGE_RECEIVED")
                
            else:
                # NEW FIX: Forward all other commands (BUTTON_PRESS, START_MEETING, STOP_MEETING) 
                # directly to the main.py callback instead of throwing them away!
                self.on_command_callback(command)

        except Exception as e:
            print(f"[NETWORK ERROR] {e}")
        finally:
            client_socket.close()
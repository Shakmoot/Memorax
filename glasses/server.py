import socket
import threading
import wave

class GlassesServer:
    def __init__(self, port, on_command_callback):
        self.port = port
        self.on_command_callback = on_command_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                payload = bytearray()
                bytes_received = 0
                
                print(f"[NETWORK] Incoming Image: Expecting {payload_length} bytes...")
                
                while bytes_received < payload_length:
                    # Request chunks
                    chunk = client_socket.recv(min(4096, payload_length - bytes_received))
                    if not chunk:
                        print(f"[NETWORK] Warning: Connection closed early. Got {bytes_received}/{payload_length} bytes.")
                        break # Break out, but KEEP the payload we have!
                        
                    payload.extend(chunk)
                    bytes_received += len(chunk)
                
                print(f"[NETWORK] Image download complete: {bytes_received} bytes received.")
                    
                # Save the image (Even if it's slightly truncated, it often still opens!)
                if bytes_received > 0:
                    with open("latest_capture.jpg", "wb") as f:
                        f.write(payload)
                    print("[NETWORK] Image saved to disk.")
                    # Trigger the callback in main.py
                    self.on_command_callback("IMAGE_RECEIVED")
                else:
                    print("[NETWORK] Error: Received 0 bytes for image.")

            elif command == "AUDIO_STREAM":
                # Read the incoming audio bytes until the glasses close the connection
                payload = bytearray()
                print("[NETWORK] Incoming Audio Stream...")
                
                try:
                    while True:
                        chunk = client_socket.recv(4096)
                        if not chunk:
                            break
                        payload += chunk
                except Exception as stream_err:
                     print(f"[NETWORK] Warning: Audio stream interrupted: {stream_err}")
                    
                print(f"[NETWORK] Audio stream ended. Received {len(payload)} bytes.")
                
                # Only process if we actually received a decent amount of audio data
                # 16kHz, 16-bit mono = 32,000 bytes per second.
                # Let's require at least 0.5 seconds of audio (16,000 bytes) to process.
                if len(payload) > 16000:
                    # Convert the raw 16-bit, 16kHz, Mono PCM bytes into a standard WAV file
                    wav_filename = "glasses_voice_query.wav"
                    try:
                        with wave.open(wav_filename, 'wb') as wf:
                            wf.setnchannels(1)          # Mono
                            wf.setsampwidth(2)          # 16-bit (2 bytes per sample)
                            wf.setframerate(16000)      # 16 kHz
                            wf.writeframes(payload)
                        print(f"[NETWORK] Saved {wav_filename} successfully.")
                        # Trigger the callback in main.py to process the voice
                        self.on_command_callback("VOICE_AUDIO_RECEIVED")
                    except Exception as wave_err:
                        print(f"[NETWORK] Failed to save WAV file: {wave_err}")
                else:
                    print(f"[NETWORK] Ignored short/blank audio clip ({len(payload)} bytes). Please hold the button longer.")

            else:
                # Forward all other commands (BUTTON_PRESS, START_MEETING, STOP_MEETING)
                self.on_command_callback(command)
                
        except Exception as e:
            print(f"[NETWORK] Error handling client {addr}: {e}")
        finally:
            client_socket.close()
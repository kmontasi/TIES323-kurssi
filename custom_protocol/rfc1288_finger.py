import socket
import threading
import sys

class FingerServer:
    def __init__(self, host="127.0.0.1", port=8079):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.users = {
            "": "Login       Name               Office\r\narjuvi      Ari Viinikainen    Agora\r\nstudent     Opiskelija         Agora\r\n",
            "arjuvi": "Login: arjuvi\tName: Ari Viinikainen\r\nToimisto: Agora\r\n",
            "student": "Login: student\tName: Opiskelija\r\nToimisto: Agora\r\n"
        }

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        print(f"Finger palvelin kuuntelee: {self.host}:{self.port}")

        while self.running:
            try:
                conn, _ = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        with conn:
            req = conn.recv(1024).decode("utf-8", errors="ignore").strip()
            reply = self.users.get(req, f"Kayttajaa '{req}' ei loydy.\r\n")
            conn.sendall(reply.encode("utf-8"))

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

class FingerClient:
    def __init__(self, host="127.0.0.1", port=8079):
        self.host = host
        self.port = port

    def query(self, username=""):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((self.host, self.port))
            s.sendall(f"{username}\r\n".encode("utf-8"))
            data = b""
            while chunk := s.recv(4096):
                data += chunk
            return data.decode("utf-8", errors="replace")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        FingerServer().start()
    else:
        user = sys.argv[1] if len(sys.argv) > 1 else ""
        cli = FingerClient()
        print(cli.query(user))

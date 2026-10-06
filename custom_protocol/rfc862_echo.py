import socket
import threading
import sys

class EchoServer:
    def __init__(self, host="127.0.0.1", port=8007):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        print(f"Echo palvelin kuuntelee: {self.host}:{self.port}")

        while self.running:
            try:
                conn, _ = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                conn.sendall(data)

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

class EchoClient:
    def __init__(self, host="127.0.0.1", port=8007):
        self.host = host
        self.port = port

    def echo(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((self.host, self.port))
            s.sendall(message.encode("utf-8"))
            return s.recv(4096).decode("utf-8")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        EchoServer().start()
    else:
        cli = EchoClient()
        msg = sys.argv[1] if len(sys.argv) > 1 else "Hei Echo"
        print("Vastaus:", cli.echo(msg))

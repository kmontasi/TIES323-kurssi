import socket
import threading
import sys
import datetime

class DaytimeServer:
    def __init__(self, host="127.0.0.1", port=8013):
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
        print(f"Daytime palvelin kuuntelee: {self.host}:{self.port}")

        while self.running:
            try:
                conn, _ = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        with conn:
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %H:%M:%S %Y UTC\r\n")
            conn.sendall(now_str.encode("ascii"))

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

class DaytimeClient:
    def __init__(self, host="127.0.0.1", port=8013):
        self.host = host
        self.port = port

    def get_time(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((self.host, self.port))
            return s.recv(1024).decode("ascii").strip()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        DaytimeServer().start()
    else:
        cli = DaytimeClient()
        print("Palvelimen aika:", cli.get_time())

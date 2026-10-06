import socket
import threading
import sys
import enum

class ServerState(enum.Enum):
    LISTEN = "LISTEN"
    WAIT_HELLO = "WAIT_HELLO"
    AUTHENTICATED = "AUTHENTICATED"
    PROCESSING = "PROCESSING"
    DISCONNECTING = "DISCONNECTING"
    CLOSED = "CLOSED"

class ClientState(enum.Enum):
    INIT = "INIT"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    HANDSHAKING = "HANDSHAKING"
    READY = "READY"
    AWAITING_REPLY = "AWAITING_REPLY"
    TERMINATING = "TERMINATING"
    CLOSED = "CLOSED"

class KVSPServer:
    def __init__(self, host="127.0.0.1", port=9099):
        self.host = host
        self.port = port
        self.running = False
        self.sock = None
        self.storage = {}
        self.lock = threading.Lock()

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        print(f"KVSP palvelin kuuntelee: {self.host}:{self.port}")

        while self.running:
            try:
                conn, addr = self.sock.accept()
                threading.Thread(target=self._session, args=(conn, addr), daemon=True).start()
            except Exception:
                break

    def _session(self, conn, addr):
        state = ServerState.WAIT_HELLO
        conn.sendall(b"200 KVSP/1.0 READY\r\n")
        buffer = ""

        with conn:
            while state != ServerState.CLOSED:
                try:
                    data = conn.recv(1024).decode("utf-8", errors="replace")
                    if not data:
                        state = ServerState.CLOSED
                        break
                    buffer += data
                except Exception:
                    state = ServerState.CLOSED
                    break

                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(" ", 2)
                    cmd = parts[0].upper()

                    if state == ServerState.WAIT_HELLO:
                        if cmd == "HELLO":
                            client_id = parts[1] if len(parts) > 1 else "tuntematon"
                            state = ServerState.AUTHENTICATED
                            conn.sendall(f"200 HELLO_OK welcome {client_id}\r\n".encode("utf-8"))
                        elif cmd == "BYE":
                            state = ServerState.CLOSED
                            conn.sendall(b"200 GOODBYE\r\n")
                            break
                        else:
                            conn.sendall(b"400 EXPECTED_HELLO\r\n")

                    elif state == ServerState.AUTHENTICATED:
                        state = ServerState.PROCESSING

                        if cmd == "SET":
                            if len(parts) >= 3:
                                k, v = parts[1], parts[2]
                                with self.lock:
                                    self.storage[k] = v
                                conn.sendall(f"201 STORED {k}\r\n".encode("utf-8"))
                            else:
                                conn.sendall(b"400 INVALID_SYNTAX\r\n")
                        elif cmd == "GET":
                            if len(parts) >= 2:
                                k = parts[1]
                                with self.lock:
                                    v = self.storage.get(k)
                                if v is not None:
                                    conn.sendall(f"200 VALUE {k} {v}\r\n".encode("utf-8"))
                                else:
                                    conn.sendall(f"404 NOT_FOUND {k}\r\n".encode("utf-8"))
                            else:
                                conn.sendall(b"400 INVALID_SYNTAX\r\n")
                        elif cmd == "DEL":
                            if len(parts) >= 2:
                                k = parts[1]
                                with self.lock:
                                    existed = self.storage.pop(k, None) is not None
                                if existed:
                                    conn.sendall(f"200 DELETED {k}\r\n".encode("utf-8"))
                                else:
                                    conn.sendall(f"404 NOT_FOUND {k}\r\n".encode("utf-8"))
                        elif cmd == "COUNT":
                            with self.lock:
                                c = len(self.storage)
                            conn.sendall(f"200 COUNT {c}\r\n".encode("utf-8"))
                        elif cmd == "BYE":
                            state = ServerState.DISCONNECTING
                            conn.sendall(b"200 GOODBYE\r\n")
                            state = ServerState.CLOSED
                            break
                        else:
                            conn.sendall(b"405 UNKNOWN_COMMAND\r\n")

                        if state == ServerState.PROCESSING:
                            state = ServerState.AUTHENTICATED

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()


class KVSPClient:
    def __init__(self, host="127.0.0.1", port=9099):
        self.host = host
        self.port = port
        self.state = ClientState.INIT
        self.sock = None

    def connect(self, client_id="test_kayttaja"):
        self.state = ClientState.CONNECTING
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.host, self.port))
        self.state = ClientState.CONNECTED

        ready_line = self._recv_line()
        if not ready_line.startswith("200"):
            self.close()
            raise RuntimeError(f"Palvelin ei valmis: {ready_line}")

        self.state = ClientState.HANDSHAKING
        self._send_line(f"HELLO {client_id}")
        resp = self._recv_line()
        if not resp.startswith("200"):
            self.close()
            raise RuntimeError("Kattely epaonnistui")

        self.state = ClientState.READY
        return resp

    def _send_line(self, text):
        self.sock.sendall((text + "\r\n").encode("utf-8"))

    def _recv_line(self):
        buf = ""
        while True:
            ch = self.sock.recv(1).decode("utf-8", errors="replace")
            if not ch:
                break
            buf += ch
            if buf.endswith("\r\n"):
                break
        return buf.strip()

    def set(self, key, value):
        self.state = ClientState.AWAITING_REPLY
        self._send_line(f"SET {key} {value}")
        resp = self._recv_line()
        self.state = ClientState.READY
        return resp

    def get(self, key):
        self.state = ClientState.AWAITING_REPLY
        self._send_line(f"GET {key}")
        resp = self._recv_line()
        self.state = ClientState.READY
        if resp.startswith("200 VALUE"):
            parts = resp.split(" ", 3)
            return parts[3] if len(parts) > 3 else ""
        return None

    def delete(self, key):
        self.state = ClientState.AWAITING_REPLY
        self._send_line(f"DEL {key}")
        resp = self._recv_line()
        self.state = ClientState.READY
        return resp.startswith("200")

    def count(self):
        self.state = ClientState.AWAITING_REPLY
        self._send_line("COUNT")
        resp = self._recv_line()
        self.state = ClientState.READY
        parts = resp.split()
        return int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    def close(self):
        if self.state in (ClientState.READY, ClientState.CONNECTED, ClientState.HANDSHAKING):
            try:
                self.state = ClientState.TERMINATING
                self._send_line("BYE")
                self._recv_line()
            except Exception:
                pass
        self.state = ClientState.CLOSED
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        KVSPServer().start()
    else:
        cli = KVSPClient()
        cli.connect("testi")
        print("SET status active ->", cli.set("status", "active"))
        print("GET status ->", cli.get("status"))
        print("COUNT ->", cli.count())
        cli.close()

import socket
import threading

class Pop3Server:
    def __init__(self, inbox, host="127.0.0.1", port=1110):
        self.inbox = inbox
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)
        print(f"POP3 server kuuntelee osoitteessa {self.host}:{self.port}")

        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        conn.sendall(b"+OK POP3 server ready\r\n")
        deleted = set()
        buffer = ""

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
            except Exception:
                break

            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip("\r").strip()
                if not line:
                    continue

                parts = line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "USER":
                    conn.sendall(b"+OK User accepted\r\n")
                elif cmd == "PASS":
                    conn.sendall(b"+OK Pass accepted\r\n")
                elif cmd == "STAT":
                    count = self.inbox.count() - len(deleted)
                    conn.sendall(f"+OK {count} 0\r\n".encode())
                elif cmd == "LIST":
                    count = self.inbox.count()
                    lines = [f"+OK {count} messages\r\n"]
                    for i in range(count):
                        if i not in deleted:
                            m = self.inbox.get(i)
                            size = len(m["body"]) if m else 0
                            lines.append(f"{i + 1} {size}\r\n")
                    lines.append(".\r\n")
                    conn.sendall("".join(lines).encode())
                elif cmd == "RETR":
                    try:
                        idx = int(arg) - 1
                        msg = self.inbox.get(idx)
                        if msg and idx not in deleted:
                            body = msg["body"]
                            conn.sendall(f"+OK {len(body)} octets\r\n{body}\r\n.\r\n".encode())
                        else:
                            conn.sendall(b"-ERR No such message\r\n")
                    except:
                        conn.sendall(b"-ERR Invalid argument\r\n")
                elif cmd == "DELE":
                    try:
                        idx = int(arg) - 1
                        deleted.add(idx)
                        conn.sendall(b"+OK Message deleted\r\n")
                    except:
                        conn.sendall(b"-ERR Invalid argument\r\n")
                elif cmd == "RSET":
                    deleted.clear()
                    conn.sendall(b"+OK Reset done\r\n")
                elif cmd == "NOOP":
                    conn.sendall(b"+OK\r\n")
                elif cmd == "QUIT":
                    for idx in sorted(deleted, reverse=True):
                        self.inbox.delete(idx)
                    conn.sendall(b"+OK Bye\r\n")
                    conn.close()
                    return
                else:
                    conn.sendall(b"-ERR Unknown command\r\n")
        conn.close()

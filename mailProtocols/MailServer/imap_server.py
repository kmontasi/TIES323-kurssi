import socket
import threading

class ImapServer:
    def __init__(self, inbox, host="127.0.0.1", port=1143):
        self.inbox = inbox
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)
        print(f"IMAP server kuuntelee osoitteessa {self.host}:{self.port}")

        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        conn.sendall(b"* OK IMAP4rev1 Server Ready\r\n")
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

                parts = line.split(" ", 2)
                if len(parts) < 2:
                    continue
                tag = parts[0]
                cmd = parts[1].upper()
                arg = parts[2] if len(parts) > 2 else ""

                if cmd == "CAPABILITY":
                    conn.sendall(f"* CAPABILITY IMAP4rev1\r\n{tag} OK CAPABILITY completed\r\n".encode())
                elif cmd == "LOGIN":
                    conn.sendall(f"{tag} OK LOGIN completed\r\n".encode())
                elif cmd == "SELECT":
                    c = self.inbox.count()
                    conn.sendall(f"* {c} EXISTS\r\n* 0 RECENT\r\n{tag} OK [READ-WRITE] SELECT completed\r\n".encode())
                elif cmd == "LIST":
                    conn.sendall(f'* LIST () "/" "INBOX"\r\n{tag} OK LIST completed\r\n'.encode())
                elif cmd == "FETCH":
                    try:
                        num = int(arg.split()[0]) - 1
                        msg = self.inbox.get(num)
                        if msg:
                            body = msg["body"]
                            res = f"* {num + 1} FETCH (RFC822 {{{len(body)}}}\r\n{body}\r\n)\r\n{tag} OK FETCH completed\r\n"
                            conn.sendall(res.encode())
                        else:
                            conn.sendall(f"{tag} NO No such message\r\n".encode())
                    except:
                        conn.sendall(f"{tag} BAD Invalid arguments\r\n".encode())
                elif cmd == "NOOP":
                    conn.sendall(f"{tag} OK NOOP completed\r\n".encode())
                elif cmd == "LOGOUT":
                    conn.sendall(f"* BYE Server logging out\r\n{tag} OK LOGOUT completed\r\n".encode())
                    conn.close()
                    return
                else:
                    conn.sendall(f"{tag} BAD Command unrecognized\r\n".encode())
        conn.close()

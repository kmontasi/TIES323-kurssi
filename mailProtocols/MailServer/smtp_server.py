import socket
import threading

class SmtpServer:
    def __init__(self, inbox, host="127.0.0.1", port=2525):
        self.inbox = inbox
        self.host = host
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)
        print(f"SMTP server kuuntelee osoitteessa {self.host}:{self.port}")

        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def handle_client(self, conn):
        conn.sendall(b"220 localhost SMTP ready\r\n")
        sender = ""
        recipients = []
        in_data = False
        body_lines = []

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
            except Exception:
                break

            text = data.decode("utf-8", errors="ignore")

            if in_data:
                body_lines.append(text)
                full = "".join(body_lines)
                if "\r\n.\r\n" in full or "\n.\n" in full:
                    clean_body = full.replace("\r\n.\r\n", "").replace("\n.\n", "")
                    self.inbox.add(sender, recipients, clean_body)
                    conn.sendall(b"250 OK: viesti tallennettu\r\n")
                    in_data = False
                    body_lines = []
                continue

            for line in text.split("\r\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(" ", 1)
                cmd = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ("HELO", "EHLO"):
                    conn.sendall(b"250 Hello\r\n")
                elif cmd == "MAIL":
                    if arg.upper().startswith("FROM:"):
                        sender = arg[5:].strip("<> ")
                        recipients = []
                        conn.sendall(b"250 OK\r\n")
                    else:
                        conn.sendall(b"501 Syntax error\r\n")
                elif cmd == "RCPT":
                    if arg.upper().startswith("TO:"):
                        recipients.append(arg[3:].strip("<> "))
                        conn.sendall(b"250 OK\r\n")
                    else:
                        conn.sendall(b"501 Syntax error\r\n")
                elif cmd == "DATA":
                    conn.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                    in_data = True
                    body_lines = []
                elif cmd == "RSET":
                    sender = ""
                    recipients = []
                    conn.sendall(b"250 OK\r\n")
                elif cmd == "NOOP":
                    conn.sendall(b"250 OK\r\n")
                elif cmd == "QUIT":
                    conn.sendall(b"221 Bye\r\n")
                    conn.close()
                    return
                else:
                    conn.sendall(b"500 Command unrecognized\r\n")
        conn.close()

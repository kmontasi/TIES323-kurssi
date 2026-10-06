import socket
import sys

def send_mail(sender, recipient, subject, body, host="127.0.0.1", port=2525):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(s.recv(1024).decode().strip())

    def send_cmd(cmd):
        print(">", cmd)
        s.sendall((cmd + "\r\n").encode())
        res = s.recv(1024).decode().strip()
        print("<", res)
        return res

    send_cmd("HELO localhost")
    send_cmd(f"MAIL FROM:<{sender}>")
    send_cmd(f"RCPT TO:<{recipient}>")
    send_cmd("DATA")

    full_data = f"From: <{sender}>\r\nTo: <{recipient}>\r\nSubject: {subject}\r\n\r\n{body}\r\n.\r\n"
    s.sendall(full_data.encode())
    print("<", s.recv(1024).decode().strip())

    send_cmd("QUIT")
    s.close()
    print("Viesti lahetetty.")

if __name__ == "__main__":
    sender = sys.argv[1] if len(sys.argv) > 1 else "student@ties323.local"
    rcpt = sys.argv[2] if len(sys.argv) > 2 else "teacher@ties323.local"
    subj = sys.argv[3] if len(sys.argv) > 3 else "TIES323 Testi"
    body = sys.argv[4] if len(sys.argv) > 4 else "Tama on testiviesti SMTP asiakkaalta."
    send_mail(sender, rcpt, subj, body)

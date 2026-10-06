import socket

def read_line(s):
    buf = ""
    while not buf.endswith("\r\n"):
        c = s.recv(1).decode(errors="ignore")
        if not c:
            break
        buf += c
    return buf.strip()

def run_imap(host="127.0.0.1", port=1143, user="guest", password="password"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(read_line(s))

    tag = 1
    def send_cmd(cmd):
        nonlocal tag
        t = f"a{tag:03d}"
        tag += 1
        print(">", f"{t} {cmd}")
        s.sendall(f"{t} {cmd}\r\n".encode())
        while True:
            line = read_line(s)
            print("<", line)
            if line.startswith(f"{t} OK") or line.startswith(f"{t} NO") or line.startswith(f"{t} BAD"):
                return line

    send_cmd(f'LOGIN "{user}" "{password}"')
    send_cmd('SELECT "INBOX"')
    send_cmd('FETCH 1 (RFC822)')
    send_cmd('LOGOUT')
    s.close()

if __name__ == "__main__":
    run_imap()

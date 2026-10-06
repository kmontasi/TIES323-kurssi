import socket

def read_line(s):
    buf = ""
    while not buf.endswith("\r\n"):
        c = s.recv(1).decode(errors="ignore")
        if not c:
            break
        buf += c
    return buf.strip()

def run_pop3(host="127.0.0.1", port=1110, user="guest", password="password"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(read_line(s))

    def send_cmd(cmd):
        print(">", cmd)
        s.sendall((cmd + "\r\n").encode())
        res = read_line(s)
        print("<", res)
        return res

    send_cmd(f"USER {user}")
    send_cmd(f"PASS {password}")
    send_cmd("STAT")

    send_cmd("LIST")
    msg_ids = []
    while True:
        line = read_line(s)
        if line == ".":
            break
        parts = line.split()
        if parts:
            msg_ids.append(parts[0])

    for mid in msg_ids:
        print(f"\n--- Viesti #{mid} ---")
        send_cmd(f"RETR {mid}")
        while True:
            line = read_line(s)
            if line == ".":
                break
            print(line)

    send_cmd("QUIT")
    s.close()

if __name__ == "__main__":
    run_pop3()

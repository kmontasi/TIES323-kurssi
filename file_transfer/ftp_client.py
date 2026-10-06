import socket
import sys
import re
import os

class FTPClient:
    def __init__(self, host="127.0.0.1", port=2121):
        self.host = host
        self.port = port
        self.ctrl_sock = None

    def connect(self):
        self.ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ctrl_sock.settimeout(10.0)
        self.ctrl_sock.connect((self.host, self.port))
        resp = self.recv_ctrl()
        print("<", resp.strip())
        return resp

    def send_ctrl(self, cmd):
        print(">", cmd)
        self.ctrl_sock.sendall((cmd + "\r\n").encode("utf-8"))
        resp = self.recv_ctrl()
        print("<", resp.strip())
        return resp

    def recv_ctrl(self):
        resp = ""
        while True:
            chunk = self.ctrl_sock.recv(4096).decode("utf-8", errors="replace")
            if not chunk:
                break
            resp += chunk
            lines = resp.strip().split("\n")
            last = lines[-1].strip()
            if len(last) >= 4 and last[:3].isdigit() and last[3] == " ":
                break
            elif len(last) == 3 and last.isdigit():
                break
        return resp

    def login(self, username="anonymous", password="guest@ties323.local"):
        self.send_ctrl(f"USER {username}")
        resp = self.send_ctrl(f"PASS {password}")
        return resp.startswith("230")

    def pasv(self):
        # Haetaan passiivitilan portti vastauskoodista
        resp = self.send_ctrl("PASV")
        m = re.search(r'\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)', resp)
        if not m:
            raise RuntimeError("PASV jasennys epaonnistui")
        nums = [int(x) for x in m.groups()]
        ip = f"{nums[0]}.{nums[1]}.{nums[2]}.{nums[3]}"
        port = (nums[4] << 8) + nums[5]
        return ip, port

    def epsv(self):
        resp = self.send_ctrl("EPSV")
        m = re.search(r'\(\|\|\|(\d+)\|\)', resp)
        if not m:
            raise RuntimeError("EPSV jasennys epaonnistui")
        return self.host, int(m.group(1))

    def open_data_connection(self, use_epsv=False):
        ip, port = self.epsv() if use_epsv else self.pasv()
        dsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dsock.settimeout(10.0)
        dsock.connect((ip, port))
        return dsock

    def list(self, use_epsv=False):
        dsock = self.open_data_connection(use_epsv)
        self.send_ctrl("LIST")
        listing = b""
        while True:
            chunk = dsock.recv(4096)
            if not chunk:
                break
            listing += chunk
        dsock.close()
        self.recv_ctrl()
        return listing.decode("utf-8", errors="replace")

    def retr(self, remote_file, local_path=None, use_epsv=False):
        if local_path is None:
            local_path = remote_file
        dsock = self.open_data_connection(use_epsv)
        resp = self.send_ctrl(f"RETR {remote_file}")
        if not resp.startswith("150"):
            dsock.close()
            raise RuntimeError(f"RETR epaonnistui: {resp}")

        with open(local_path, "wb") as f:
            while True:
                chunk = dsock.recv(4096)
                if not chunk:
                    break
                f.write(chunk)
        dsock.close()
        self.recv_ctrl()
        print(f"Ladattu: {remote_file} -> {local_path}")

    def quit(self):
        resp = self.send_ctrl("QUIT")
        try:
            self.ctrl_sock.close()
        except:
            pass
        return resp

def run_test_server(host="127.0.0.1", port=2121):
    import threading
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    print(f"Testi-FTP kuuntelee: {host}:{port}")

    files = {"welcome.txt": b"Tervetuloa FTP-palvelimelle!\nTama tiedosto vahvistaa RETR-toiminnon."}

    def client_thread(conn):
        conn.sendall(b"220 FTP valmiina\r\n")
        pasv_s = None
        pasv_port = None

        while True:
            try:
                line = conn.recv(1024).decode("utf-8", errors="ignore")
                if not line:
                    break
            except:
                break

            parts = line.strip().split(" ", 1)
            cmd = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "USER":
                conn.sendall(b"331 Anna salasana\r\n")
            elif cmd == "PASS":
                conn.sendall(b"230 Kirjauduttu sisaan\r\n")
            elif cmd in ("PASV", "EPSV"):
                if pasv_s:
                    pasv_s.close()
                pasv_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                pasv_s.bind((host, 0))
                pasv_s.listen(1)
                pasv_port = pasv_s.getsockname()[1]

                if cmd == "PASV":
                    p1 = pasv_port >> 8
                    p2 = pasv_port & 0xFF
                    conn.sendall(f"227 Entering Passive Mode (127,0,0,1,{p1},{p2})\r\n".encode())
                else:
                    conn.sendall(f"229 Entering Extended Passive Mode (|||{pasv_port}|)\r\n".encode())
            elif cmd == "LIST":
                conn.sendall(b"150 Hakemistolistaus tulossa\r\n")
                if pasv_s:
                    dconn, _ = pasv_s.accept()
                    listing = ""
                    for name, content in files.items():
                        listing += f"-rw-r--r-- 1 student staff {len(content)} Oct 06 12:00 {name}\r\n"
                    dconn.sendall(listing.encode())
                    dconn.close()
                    pasv_s.close()
                    pasv_s = None
                conn.sendall(b"226 Valmis\r\n")
            elif cmd == "RETR":
                if arg in files:
                    conn.sendall(b"150 Avataan datayhteys\r\n")
                    if pasv_s:
                        dconn, _ = pasv_s.accept()
                        dconn.sendall(files[arg])
                        dconn.close()
                        pasv_s.close()
                        pasv_s = None
                    conn.sendall(b"226 Siirto valmis\r\n")
                else:
                    conn.sendall(b"550 Tiedostoa ei loydy\r\n")
            elif cmd == "QUIT":
                conn.sendall(b"221 Nakemiin\r\n")
                break
        conn.close()

    while True:
        try:
            conn, _ = s.accept()
            threading.Thread(target=client_thread, args=(conn,), daemon=True).start()
        except:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        run_test_server()
    else:
        cli = FTPClient()
        cli.connect()
        cli.login()
        print("Tiedostot:")
        print(cli.list())
        cli.retr("welcome.txt", "ladattu_welcome.txt")
        cli.quit()

import socket
import struct
import threading
import sys
import os

OP_RRQ   = 1
OP_WRQ   = 2
OP_DATA  = 3
OP_ACK   = 4
OP_ERROR = 5

BLOCK_SIZE = 512
DEFAULT_TIMEOUT = 2.0
MAX_RETRIES = 5

class TFTPServer:
    def __init__(self, host="127.0.0.1", port=6969, storage_dir=None):
        self.host = host
        self.port = port
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tftp_storage")
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = False

    def start(self):
        self.running = True
        print(f"TFTP palvelin kuuntelee: {self.host}:{self.port}")

        while self.running:
            try:
                data, client_addr = self.sock.recvfrom(2048)
                if len(data) < 4:
                    continue
                opcode = struct.unpack("!H", data[:2])[0]
                if opcode in (OP_RRQ, OP_WRQ):
                    threading.Thread(
                        target=self.handle_request,
                        args=(data, client_addr, opcode),
                        daemon=True
                    ).start()
            except Exception:
                break

    def stop(self):
        self.running = False
        self.sock.close()

    def handle_request(self, req_data, client_addr, opcode):
        parts = req_data[2:].split(b"\x00")
        filename = parts[0].decode("utf-8", errors="replace")
        filepath = os.path.join(self.storage_dir, os.path.basename(filename))

        worker_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        worker_sock.bind((self.host, 0))
        worker_sock.settimeout(DEFAULT_TIMEOUT)

        if opcode == OP_RRQ:
            self.handle_rrq(worker_sock, client_addr, filepath)
        elif opcode == OP_WRQ:
            self.handle_wrq(worker_sock, client_addr, filepath)
        worker_sock.close()

    def handle_rrq(self, sock, client_addr, filepath):
        if not os.path.exists(filepath):
            sock.sendto(struct.pack("!HH", OP_ERROR, 1) + b"Tiedostoa ei loydy\x00", client_addr)
            return

        with open(filepath, "rb") as f:
            block_num = 1
            while True:
                chunk = f.read(BLOCK_SIZE)
                data_pkt = struct.pack("!HH", OP_DATA, block_num) + chunk
                retries = 0
                ack_ok = False

                while retries < MAX_RETRIES:
                    sock.sendto(data_pkt, client_addr)
                    try:
                        resp, _ = sock.recvfrom(2048)
                        if len(resp) >= 4:
                            op, blk = struct.unpack("!HH", resp[:4])
                            if op == OP_ACK and blk == block_num:
                                ack_ok = True
                                break
                    except socket.timeout:
                        retries += 1
                        print(f"Aikakatkaisu lohkon {block_num} kuittaukselle, lahetetaan uudelleen")

                if not ack_ok:
                    print(f"Lataus keskeytyi lohkon {block_num} kohdalla")
                    return

                if len(chunk) < BLOCK_SIZE:
                    print(f"Tiedosto {filepath} lahetetty onnistuneesti")
                    break
                block_num = (block_num + 1) & 0xFFFF

    def handle_wrq(self, sock, client_addr, filepath):
        last_ack = 0
        sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)

        expected_block = 1
        with open(filepath, "wb") as f:
            while True:
                retries = 0
                saved = False

                while retries < MAX_RETRIES:
                    try:
                        pkt, _ = sock.recvfrom(2048)
                        if len(pkt) < 4:
                            continue
                        op, blk = struct.unpack("!HH", pkt[:4])

                        if op != OP_DATA:
                            sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)
                            retries += 1
                            continue

                        if blk == expected_block:
                            payload = pkt[4:]
                            f.write(payload)
                            last_ack = expected_block
                            sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)
                            saved = True

                            if len(payload) < BLOCK_SIZE:
                                print(f"Vastaanotettu tiedosto {filepath}")
                                return
                            expected_block = (expected_block + 1) & 0xFFFF
                            break
                        elif blk < expected_block or blk == last_ack:
                            # Duplikaattilohko
                            sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)
                        else:
                            sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)
                    except socket.timeout:
                        retries += 1
                        sock.sendto(struct.pack("!HH", OP_ACK, last_ack), client_addr)

                if not saved:
                    return

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 6969
    srv = TFTPServer(port=port)
    try:
        srv.start()
    except KeyboardInterrupt:
        srv.stop()

import socket
import struct
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

class TFTPClient:
    def __init__(self, host="127.0.0.1", port=6969, timeout=DEFAULT_TIMEOUT):
        self.server_host = host
        self.server_port = port
        self.timeout = timeout
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)

    def download_file(self, remote_filename, local_filename=None):
        if local_filename is None:
            local_filename = remote_filename

        rrq_pkt = struct.pack("!H", OP_RRQ) + remote_filename.encode("utf-8") + b"\x00octet\x00"
        server_tid = None
        expected_block = 1
        last_ack_block = 0

        print(f"Lahetetaan RRQ tiedostolle '{remote_filename}'")
        self.sock.sendto(rrq_pkt, (self.server_host, self.server_port))

        with open(local_filename, "wb") as f:
            while True:
                retries = 0
                block_received = False

                while retries < MAX_RETRIES:
                    try:
                        pkt, addr = self.sock.recvfrom(2048)
                        if server_tid is None:
                            server_tid = addr
                        elif addr != server_tid:
                            continue

                        if len(pkt) < 4:
                            continue

                        op, blk = struct.unpack("!HH", pkt[:4])
                        if op == OP_ERROR:
                            err_msg = pkt[4:].decode("utf-8", errors="replace")
                            raise RuntimeError(f"TFTP virhe: {err_msg}")

                        if op != OP_DATA:
                            self.sock.sendto(struct.pack("!HH", OP_ACK, last_ack_block), server_tid)
                            retries += 1
                            continue

                        if blk == expected_block:
                            payload = pkt[4:]
                            f.write(payload)
                            last_ack_block = expected_block
                            self.sock.sendto(struct.pack("!HH", OP_ACK, last_ack_block), server_tid)
                            block_received = True

                            if len(payload) < BLOCK_SIZE:
                                print(f"Lataus valmis: {remote_filename}")
                                return
                            expected_block = (expected_block + 1) & 0xFFFF
                            break
                        elif blk < expected_block or blk == last_ack_block:
                            # Duplikaattipaketti, lahetetaan edellinen kuittaus uudelleen
                            self.sock.sendto(struct.pack("!HH", OP_ACK, last_ack_block), server_tid)
                        else:
                            self.sock.sendto(struct.pack("!HH", OP_ACK, last_ack_block), server_tid)

                    except socket.timeout:
                        retries += 1
                        print(f"Aikakatkaisu lohkolle {expected_block}, yritetaan uudelleen ({retries}/{MAX_RETRIES})")
                        target = server_tid if server_tid else (self.server_host, self.server_port)
                        if last_ack_block == 0:
                            self.sock.sendto(rrq_pkt, target)
                        else:
                            self.sock.sendto(struct.pack("!HH", OP_ACK, last_ack_block), target)

                if not block_received:
                    raise TimeoutError(f"Lohkon {expected_block} vastaanotto epaonnistui")

    def upload_file(self, local_filename, remote_filename=None):
        if remote_filename is None:
            remote_filename = os.path.basename(local_filename)

        if not os.path.exists(local_filename):
            raise FileNotFoundError(f"Tiedostoa ei loydy: {local_filename}")

        wrq_pkt = struct.pack("!H", OP_WRQ) + remote_filename.encode("utf-8") + b"\x00octet\x00"
        server_tid = None

        print(f"Lahetetaan WRQ tiedostolle '{remote_filename}'")
        retries = 0
        ack_0_received = False

        while retries < MAX_RETRIES:
            self.sock.sendto(wrq_pkt, (self.server_host, self.server_port))
            try:
                pkt, addr = self.sock.recvfrom(2048)
                if len(pkt) >= 4:
                    op, blk = struct.unpack("!HH", pkt[:4])
                    if op == OP_ACK and blk == 0:
                        server_tid = addr
                        ack_0_received = True
                        break
                    elif op == OP_ERROR:
                        raise RuntimeError("TFTP virhe palvelimelta")
            except socket.timeout:
                retries += 1
                print(f"Aikakatkaisu WRQ kuittaukselle ({retries}/{MAX_RETRIES})")

        if not ack_0_received:
            raise TimeoutError("Palvelin ei kuitannut WRQ-pyyntoa")

        with open(local_filename, "rb") as f:
            block_num = 1
            while True:
                chunk = f.read(BLOCK_SIZE)
                data_pkt = struct.pack("!HH", OP_DATA, block_num) + chunk
                retries = 0
                ack_received = False

                while retries < MAX_RETRIES:
                    self.sock.sendto(data_pkt, server_tid)
                    try:
                        resp, raddr = self.sock.recvfrom(2048)
                        if raddr != server_tid:
                            continue
                        if len(resp) >= 4:
                            op, blk = struct.unpack("!HH", resp[:4])
                            if op == OP_ACK:
                                if blk == block_num:
                                    ack_received = True
                                    break
                    except socket.timeout:
                        retries += 1
                        print(f"Aikakatkaisu kuittaukselle lohkolle {block_num} ({retries}/{MAX_RETRIES})")

                if not ack_received:
                    raise TimeoutError(f"Ei kuittausta lohkolle {block_num}")

                if len(chunk) < BLOCK_SIZE:
                    print(f"Lahetys valmis: {local_filename}")
                    break
                block_num = (block_num + 1) & 0xFFFF

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Kaytto: python3 tftp_client.py [get|put] tiedostonimi")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    fname = sys.argv[2]
    cli = TFTPClient()

    if cmd == "get":
        cli.download_file(fname)
    elif cmd == "put":
        cli.upload_file(fname)

import socket
import struct
import time
import random
import os
import sys

def create_pcap_global_header():
    return struct.pack("!IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)

def build_pcap_packet(data, src_ip="127.0.0.1", dst_ip="127.0.0.1", src_port=12345, dst_port=6969):
    ts = time.time()
    ts_sec = int(ts)
    ts_usec = int((ts - ts_sec) * 1_000_000)

    eth = b"\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x01\x08\x00"

    def ip2int(ip):
        return bytes([int(x) for x in ip.split(".")])

    src_bytes = ip2int(src_ip)
    dst_bytes = ip2int(dst_ip)
    udp_len = 8 + len(data)
    ip_total_len = 20 + udp_len

    ip_hdr = struct.pack("!BBHHHBBH4s4s",
                         0x45, 0, ip_total_len, random.randint(1, 65535), 0x4000, 64, 17, 0,
                         src_bytes, dst_bytes)

    udp_hdr = struct.pack("!HHHH", src_port, dst_port, udp_len, 0)
    raw_frame = eth + ip_hdr + udp_hdr + data
    frame_len = len(raw_frame)
    pcap_rec_hdr = struct.pack("!IIII", ts_sec, ts_usec, frame_len, frame_len)
    return pcap_rec_hdr + raw_frame

class ImpairmentProxy:
    def __init__(self, listen_port=6970, target_port=6969, drop_rate=0.25, pcap_out="tftp_recovery.pcap"):
        self.listen_port = listen_port
        self.target_port = target_port
        self.drop_rate = drop_rate
        self.pcap_out = pcap_out
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.listen_port))
        self.pcap_file = open(self.pcap_out, "wb")
        self.pcap_file.write(create_pcap_global_header())
        self.pcap_file.flush()
        self.client_addr = None
        self.server_worker_addr = None
        self.pkt_counter = 0
        self.running = True

    def stop(self):
        self.running = False

    def run(self, max_duration=60):
        print(f"Proxy valitetty 127.0.0.1:{self.listen_port} <-> 127.0.0.1:{self.target_port}")
        self.sock.settimeout(0.5)
        start_time = time.time()

        while self.running and (time.time() - start_time < max_duration):
            try:
                data, addr = self.sock.recvfrom(2048)
                self.pkt_counter += 1

                if self.client_addr is None or addr == self.client_addr:
                    self.client_addr = addr
                    dest = self.server_worker_addr if self.server_worker_addr else ("127.0.0.1", self.target_port)
                    rec = build_pcap_packet(data, src_port=addr[1], dst_port=dest[1])
                    self.pcap_file.write(rec)
                    self.pcap_file.flush()

                    if random.random() < self.drop_rate and len(data) >= 4 and struct.unpack("!H", data[:2])[0] in (3, 4):
                        print(f"Pudotettu asiakkaan paketti #{self.pkt_counter}")
                        continue

                    self.sock.sendto(data, dest)
                else:
                    self.server_worker_addr = addr
                    dest = self.client_addr
                    rec = build_pcap_packet(data, src_port=addr[1], dst_port=dest[1])
                    self.pcap_file.write(rec)
                    self.pcap_file.flush()

                    if random.random() < self.drop_rate and len(data) >= 4 and struct.unpack("!H", data[:2])[0] in (3, 4):
                        print(f"Pudotettu palvelimen paketti #{self.pkt_counter}")
                        continue

                    self.sock.sendto(data, dest)
            except socket.timeout:
                continue
            except Exception:
                break

        self.pcap_file.close()
        self.sock.close()

if __name__ == "__main__":
    out_pcap = sys.argv[1] if len(sys.argv) > 1 else "tftp_recovery.pcap"
    proxy = ImpairmentProxy(pcap_out=out_pcap)
    proxy.run()

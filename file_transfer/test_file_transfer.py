import subprocess
import time
import os
import sys
import hashlib
import threading
from network_impairment_proxy import ImpairmentProxy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FTP_CLIENT_PY = os.path.join(BASE_DIR, "ftp_client.py")
TFTP_SERVER_PY = os.path.join(BASE_DIR, "tftp_server.py")
TFTP_CLIENT_PY = os.path.join(BASE_DIR, "tftp_client.py")
CAPTURES_DIR = os.path.join(BASE_DIR, "captures")
PCAP_FILE = os.path.join(CAPTURES_DIR, "tftp_packet_loss_recovery.pcap")

def sha256(fname):
    h = hashlib.sha256()
    with open(fname, "rb") as f:
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()

def test_ftp():
    print("\n--- Testataan FTP ---")
    server_proc = subprocess.Popen([sys.executable, FTP_CLIENT_PY, "--server"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.0)
    try:
        res = subprocess.run([sys.executable, FTP_CLIENT_PY],
                             capture_output=True, text=True)
        print(res.stdout)
        assert res.returncode == 0
        assert os.path.exists("ladattu_welcome.txt")
        print("FTP-testi OK")
    finally:
        server_proc.terminate()
        server_proc.wait()
        if os.path.exists("ladattu_welcome.txt"):
            os.remove("ladattu_welcome.txt")

def test_tftp_normal():
    print("\n--- Testataan normaali TFTP ---")
    srv_dir = os.path.join(BASE_DIR, "tftp_storage")
    os.makedirs(srv_dir, exist_ok=True)
    server_proc = subprocess.Popen([sys.executable, TFTP_SERVER_PY, "6969"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.0)

    try:
        test_file = os.path.join(BASE_DIR, "sample_data.txt")
        with open(test_file, "w") as f:
            for i in range(100):
                f.write(f"Rivi {i}: TFTP testidataa siirtoa varten.\n")
        original_hash = sha256(test_file)

        # Lahetys (WRQ)
        res = subprocess.run([sys.executable, TFTP_CLIENT_PY, "put", test_file],
                             capture_output=True, text=True)
        print(res.stdout)
        assert res.returncode == 0

        # Lataus (RRQ)
        dl_file = os.path.join(BASE_DIR, "downloaded_sample.txt")
        if os.path.exists(dl_file):
            os.remove(dl_file)
        res = subprocess.run([sys.executable, TFTP_CLIENT_PY, "get", "sample_data.txt"],
                             capture_output=True, text=True)
        print(res.stdout)
        assert res.returncode == 0
        assert original_hash == sha256("sample_data.txt")
        print("TFTP normaali siirto OK")

    finally:
        server_proc.terminate()
        server_proc.wait()
        if os.path.exists("sample_data.txt"):
            os.remove("sample_data.txt")
        if os.path.exists("downloaded_sample.txt"):
            os.remove("downloaded_sample.txt")

def test_tftp_with_packet_loss():
    print("\n--- Testataan TFTP pakettihavio ja toipuminen ---")
    srv_dir = os.path.join(BASE_DIR, "tftp_storage")
    os.makedirs(srv_dir, exist_ok=True)
    # Luodaan tiedosto palvelimelle
    with open(os.path.join(srv_dir, "loss_test.txt"), "w") as f:
        for i in range(100):
            f.write(f"Rivi {i}: Dataa haviotestia varten.\n")
    orig_hash = sha256(os.path.join(srv_dir, "loss_test.txt"))

    server_proc = subprocess.Popen([sys.executable, TFTP_SERVER_PY, "6969"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.0)

    proxy = ImpairmentProxy(listen_port=6970, target_port=6969, drop_rate=0.25, pcap_out=PCAP_FILE)
    proxy_thread = threading.Thread(target=proxy.run, kwargs={"max_duration": 15}, daemon=True)
    proxy_thread.start()
    time.sleep(0.5)

    try:
        if os.path.exists("loss_test.txt"):
            os.remove("loss_test.txt")

        # Noudetaan proxyn kautta portista 6970
        client = subprocess.run([sys.executable, "-c", "from tftp_client import TFTPClient; cli = TFTPClient(port=6970); cli.download_file('loss_test.txt')"],
                                capture_output=True, text=True, cwd=BASE_DIR)
        print(client.stdout)
        if client.returncode != 0:
            print("Client virhe:", client.stderr)
        assert client.returncode == 0
        assert orig_hash == sha256(os.path.join(BASE_DIR, "loss_test.txt"))
        print(f"TFTP toipuminen OK, pcap tallennettu: {PCAP_FILE}")
    finally:
        proxy.stop()
        server_proc.terminate()
        server_proc.wait()
        if os.path.exists("loss_test.txt"):
            os.remove("loss_test.txt")

if __name__ == "__main__":
    test_ftp()
    test_tftp_normal()
    test_tftp_with_packet_loss()
    print("\nKaikki tiedonsiirtotestit suoritettu onnistuneesti.")

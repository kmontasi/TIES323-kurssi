import socket
import ssl

def test_tls():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("[*] Testataan suojatun TLS-yhteyden muodostamista pop.gmail.com porttiin 995...")
    try:
        raw = socket.create_connection(("pop.gmail.com", 995), timeout=5)
        with ctx.wrap_socket(raw, server_hostname="pop.gmail.com") as s:
            banner = s.recv(1024).decode()
            print("Vastaus palvelimelta:", banner.strip())
            s.sendall(b"QUIT\r\n")
            print("TLS-yhteys onnistui!")
    except Exception as e:
        print("TLS yhteysvirhe:", e)

if __name__ == "__main__":
    test_tls()

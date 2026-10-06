import time
import threading
from rfc862_echo import EchoServer, EchoClient
from rfc867_daytime import DaytimeServer, DaytimeClient
from rfc1288_finger import FingerServer, FingerClient
from kvsp_protocol import KVSPServer, KVSPClient, ClientState

def test():
    print("--- Testataan Echo ---")
    echo_s = EchoServer(port=8107)
    threading.Thread(target=echo_s.start, daemon=True).start()
    time.sleep(0.3)
    echo_c = EchoClient(port=8107)
    assert echo_c.echo("Testiviesti") == "Testiviesti"
    echo_s.stop()
    print("Echo OK")

    print("\n--- Testataan Daytime ---")
    day_s = DaytimeServer(port=8113)
    threading.Thread(target=day_s.start, daemon=True).start()
    time.sleep(0.3)
    day_c = DaytimeClient(port=8113)
    t = day_c.get_time()
    assert "UTC" in t
    day_s.stop()
    print("Daytime OK")

    print("\n--- Testataan Finger ---")
    fin_s = FingerServer(port=8179)
    threading.Thread(target=fin_s.start, daemon=True).start()
    time.sleep(0.3)
    fin_c = FingerClient(port=8179)
    assert "arjuvi" in fin_c.query()
    fin_s.stop()
    print("Finger OK")

    print("\n--- Testataan KVSP tilakone ---")
    kv_s = KVSPServer(port=9199)
    threading.Thread(target=kv_s.start, daemon=True).start()
    time.sleep(0.3)
    kv_c = KVSPClient(port=9199)
    kv_c.connect("kayttaja")
    assert kv_c.state == ClientState.READY
    kv_c.set("kurssi", "TIES323")
    assert kv_c.get("kurssi") == "TIES323"
    assert kv_c.count() == 1
    kv_c.delete("kurssi")
    assert kv_c.count() == 0
    kv_c.close()
    assert kv_c.state == ClientState.CLOSED
    kv_s.stop()
    print("KVSP OK")

    print("\nKaikki protokollatestit OK.")

if __name__ == "__main__":
    test()

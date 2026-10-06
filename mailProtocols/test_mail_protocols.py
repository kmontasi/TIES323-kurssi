import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "MailServer"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "SMTPclient"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "POP3client"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "IMAPclient"))

from inbox import Inbox
from smtp_server import SmtpServer
from pop3_server import Pop3Server
from imap_server import ImapServer
from smtp_client import send_mail
from pop3_client import run_pop3
from imap_client import run_imap

def test_all():
    inbox = Inbox()
    smtp = SmtpServer(inbox, port=2525)
    pop3 = Pop3Server(inbox, port=1110)
    imap = ImapServer(inbox, port=1143)

    t1 = threading.Thread(target=smtp.start, daemon=True)
    t2 = threading.Thread(target=pop3.start, daemon=True)
    t3 = threading.Thread(target=imap.start, daemon=True)

    t1.start()
    t2.start()
    t3.start()
    time.sleep(0.5)

    print("\n--- 1. Testataan SMTP-lahetys ---")
    send_mail("opiskelija@ties323.local", "opettaja@ties323.local", "Testi 1", "Tervehdys palvelimelle.")

    assert inbox.count() == 1
    msg = inbox.get(0)
    assert msg is not None
    assert "Tervehdys palvelimelle." in msg["body"]
    print("SMTP tallennus postilaatikkoon OK.")

    print("\n--- 2. Testataan POP3-nouto ---")
    run_pop3(port=1110)
    print("POP3 OK.")

    print("\n--- 3. Testataan IMAP-nouto ---")
    run_imap(port=1143)
    print("IMAP OK.")

    print("\nKaikki sahkopostiprotokollat toimivat virheettomasti!")

if __name__ == "__main__":
    test_all()

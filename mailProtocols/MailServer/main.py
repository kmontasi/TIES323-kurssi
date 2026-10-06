import threading
import time
from inbox import Inbox
from smtp_server import SmtpServer
from pop3_server import Pop3Server
from imap_server import ImapServer

def main():
    inbox = Inbox()

    smtp = SmtpServer(inbox, port=2525)
    pop3 = Pop3Server(inbox, port=1110)
    imap = ImapServer(inbox, port=1143)

    t_smtp = threading.Thread(target=smtp.start, daemon=True)
    t_pop3 = threading.Thread(target=pop3.start, daemon=True)
    t_imap = threading.Thread(target=imap.start, daemon=True)

    t_smtp.start()
    t_pop3.start()
    t_imap.start()

    print("[*] MailServerit kaynnistetty. Paina Ctrl+C sammuttaaksesi.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSammutetaan...")

if __name__ == "__main__":
    main()

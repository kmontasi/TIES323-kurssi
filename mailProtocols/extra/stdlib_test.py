import smtplib
import poplib
import imaplib

def test():
    print("[1] Testataan smtplib...")
    try:
        s = smtplib.SMTP("127.0.0.1", 2525)
        s.helo()
        s.sendmail("testi@ties323.fi", ["vastaanottaja@ties323.fi"], "Subject: Testi\r\n\r\nHello stdlib")
        s.quit()
        print("smtplib OK")
    except Exception as e:
        print("smtplib virhe:", e)

    print("\n[2] Testataan poplib...")
    try:
        p = poplib.POP3("127.0.0.1", 1110)
        p.user("guest")
        p.pass_("pass")
        print("POP3 tila:", p.stat())
        p.quit()
        print("poplib OK")
    except Exception as e:
        print("poplib virhe:", e)

    print("\n[3] Testataan imaplib...")
    try:
        m = imaplib.IMAP4("127.0.0.1", 1143)
        m.login("guest", "pass")
        m.select("INBOX")
        m.logout()
        print("imaplib OK")
    except Exception as e:
        print("imaplib virhe:", e)

if __name__ == "__main__":
    test()

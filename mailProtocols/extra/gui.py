import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket

class MailGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sähköpostiohjelma - TIES323")
        self.geometry("600x450")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Lahetys
        self.tab_send = ttk.Frame(self.nb)
        self.nb.add(self.tab_send, text="Lähetä (SMTP)")

        ttk.Label(self.tab_send, text="Vastaanottaja:").pack(anchor=tk.W, padx=5, pady=2)
        self.to_entry = ttk.Entry(self.tab_send, width=40)
        self.to_entry.insert(0, "vastaanottaja@ties323.local")
        self.to_entry.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.tab_send, text="Aihe:").pack(anchor=tk.W, padx=5, pady=2)
        self.subj_entry = ttk.Entry(self.tab_send, width=40)
        self.subj_entry.insert(0, "Testi")
        self.subj_entry.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.tab_send, text="Viesti:").pack(anchor=tk.W, padx=5, pady=2)
        self.body_txt = scrolledtext.ScrolledText(self.tab_send, height=10)
        self.body_txt.insert(tk.END, "Tervehdys graafisesta ohjelmasta!")
        self.body_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(self.tab_send, text="Lähetä sähköposti", command=self.send_smtp).pack(pady=5)

        # Nouto
        self.tab_recv = ttk.Frame(self.nb)
        self.nb.add(self.tab_recv, text="Saapuneet (POP3)")

        btn_box = ttk.Frame(self.tab_recv)
        btn_box.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_box, text="Päivitä saapuneet", command=self.fetch_pop3).pack(side=tk.LEFT)

        self.inbox_txt = scrolledtext.ScrolledText(self.tab_recv, height=15)
        self.inbox_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def send_smtp(self):
        to_addr = self.to_entry.get().strip()
        subj = self.subj_entry.get().strip()
        body = self.body_txt.get("1.0", tk.END).strip()

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 2525))
            s.recv(1024)
            s.sendall(b"HELO localhost\r\n")
            s.recv(1024)
            s.sendall(b"MAIL FROM:<kayttaja@ties323.local>\r\n")
            s.recv(1024)
            s.sendall(f"RCPT TO:<{to_addr}>\r\n".encode())
            s.recv(1024)
            s.sendall(b"DATA\r\n")
            s.recv(1024)
            msg = f"Subject: {subj}\r\nTo: {to_addr}\r\n\r\n{body}\r\n.\r\n"
            s.sendall(msg.encode())
            s.recv(1024)
            s.sendall(b"QUIT\r\n")
            s.recv(1024)
            s.close()
            messagebox.showinfo("OK", "Viesti lähetetty onnistuneesti!")
        except Exception as e:
            messagebox.showerror("Virhe", str(e))

    def fetch_pop3(self):
        self.inbox_txt.delete("1.0", tk.END)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 1110))
            s.recv(1024)
            s.sendall(b"USER guest\r\n")
            s.recv(1024)
            s.sendall(b"PASS pass\r\n")
            s.recv(1024)
            s.sendall(b"LIST\r\n")
            data = s.recv(1024).decode()

            s.sendall(b"RETR 1\r\n")
            msg_data = s.recv(4096).decode()
            self.inbox_txt.insert(tk.END, msg_data)

            s.sendall(b"QUIT\r\n")
            s.close()
        except Exception as e:
            messagebox.showerror("Virhe", str(e))

if __name__ == "__main__":
    app = MailGUI()
    app.mainloop()

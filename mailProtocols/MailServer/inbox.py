import threading

class Inbox:
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = []

    def add(self, sender, recipient, content):
        with self.lock:
            self.messages.append({
                "from": sender,
                "to": recipient,
                "body": content
            })

    def count(self):
        with self.lock:
            return len(self.messages)

    def get(self, index):
        with self.lock:
            if 0 <= index < len(self.messages):
                return self.messages[index]
            return None

    def delete(self, index):
        with self.lock:
            if 0 <= index < len(self.messages):
                del self.messages[index]
                return True
            return False

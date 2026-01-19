import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

class ConsoleManager:
    def __init__(self, widget, theme):
        self.widget = widget
        self.theme = theme
        self.configure_tags()
    
    def configure_tags(self):
        self.widget.tag_config("error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.widget.tag_config("warning", foreground="#e67e22", font=('Consolas', 9, 'bold'))
        self.widget.tag_config("success", foreground="#27ae60", font=('Consolas', 9, 'bold'))
        self.widget.tag_config("info", foreground="#3498db")
    
    def log(self, message, tag="info"):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.widget.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.widget.see(tk.END)
        except:
            print(message)
    
    def clear(self):
        self.widget.delete('1.0', tk.END)


class AIConsoleManager(ConsoleManager):
    def configure_tags(self):
        self.widget.tag_config("ai_request", foreground="#9b59b6", font=('Consolas', 9, 'bold'))
        self.widget.tag_config("ai_response", foreground="#27ae60")
        self.widget.tag_config("ai_error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.widget.tag_config("ai_info", foreground="#3498db")
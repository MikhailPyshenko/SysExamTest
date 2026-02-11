import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable

class BaseWindow:
    """Базовое окно приложения"""

    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self._center_window()

    def _center_window(self, width: int = 800, height: int = 600):
        """Центрирование окна"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def run(self):
        """Запуск основного цикла"""
        self.root.mainloop()

    def destroy(self):
        """Закрытие окна"""
        if self.root:
            self.root.destroy()
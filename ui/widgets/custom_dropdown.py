from typing import Callable, List, Optional

import customtkinter as ctk


class CustomDropdown(ctk.CTkFrame):
    """Стабильный кастомный выпадающий список с поддержкой длинных значений."""

    def __init__(
        self,
        master,
        options: List[str],
        command: Optional[Callable[[str], None]] = None,
        width: int = 300,
        height: int = 42,
        font=None,
        placeholder: str = "Выберите...",
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.options = options
        self.command = command
        self.placeholder = placeholder
        self.selected_value = ""
        self.dropdown_open = False

        self.font = font or ctk.CTkFont(size=14)

        self.button = ctk.CTkButton(
            self,
            text=self.placeholder,
            width=width,
            height=height,
            font=self.font,
            command=self.toggle_dropdown,
            anchor="w",
            corner_radius=8,
        )
        self.button.pack(fill="both", expand=True)

        self.dropdown_window: Optional[ctk.CTkToplevel] = None

    def toggle_dropdown(self):
        if self.dropdown_open:
            self.close_dropdown()
        else:
            self.open_dropdown()

    def _calculate_geometry(self, width: int, height: int):
        self.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height() + 2

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # если вниз не помещается — открываем вверх
        if y + height > sh - 8:
            y = max(8, self.button.winfo_rooty() - height - 2)

        # clamp по горизонтали
        if x + width > sw - 8:
            x = max(8, sw - width - 8)

        return x, y

    def open_dropdown(self):
        if self.dropdown_open or not self.options:
            return

        self.dropdown_open = True
        self.update_idletasks()

        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.attributes("-topmost", True)

        width = max(self.button.winfo_width(), 360)
        max_height = min(360, max(140, len(self.options) * 56 + 12))
        x, y = self._calculate_geometry(width, max_height)
        self.dropdown_window.geometry(f"{width}x{max_height}+{x}+{y}")

        container = ctk.CTkFrame(self.dropdown_window, corner_radius=10)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        scrollable = ctk.CTkScrollableFrame(container, corner_radius=8)
        scrollable.pack(fill="both", expand=True, padx=6, pady=6)

        for option in self.options:
            selected = option == self.selected_value
            row = ctk.CTkFrame(
                scrollable,
                corner_radius=8,
                fg_color=("#dcdcdc", "#3a3a3a") if selected else "transparent",
            )
            row.pack(fill="x", padx=2, pady=2)

            label = ctk.CTkLabel(
                row,
                text=option,
                justify="left",
                anchor="w",
                wraplength=width - 44,
                font=self.font,
                padx=8,
                pady=8,
            )
            label.pack(fill="x")

            row.bind("<Button-1>", lambda _e, opt=option: self.select_option(opt))
            label.bind("<Button-1>", lambda _e, opt=option: self.select_option(opt))

        self.dropdown_window.bind("<Escape>", lambda _e: self.close_dropdown())
        # закрываем только при клике вне (оставляем FocusOut как fallback)
        self.dropdown_window.bind("<FocusOut>", lambda _e: self.close_dropdown())
        self.dropdown_window.focus_force()

    def close_dropdown(self):
        if self.dropdown_window and self.dropdown_open:
            try:
                self.dropdown_window.destroy()
            except Exception:
                pass
        self.dropdown_window = None
        self.dropdown_open = False

    def select_option(self, option: str):
        self.selected_value = option
        self.button.configure(text=option)
        if self.command:
            self.command(option)
        self.close_dropdown()

    def get(self) -> str:
        return self.selected_value

    def set(self, value: str):
        if value in self.options:
            self.selected_value = value
            self.button.configure(text=value)

    def clear(self):
        self.selected_value = ""
        self.button.configure(text=self.placeholder)

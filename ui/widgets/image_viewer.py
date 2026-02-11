import customtkinter as ctk
from PIL import Image, ImageTk
import os
from typing import Optional, Tuple

class ImageViewer(ctk.CTkFrame):
    """Виджет для отображения изображений"""

    def __init__(self,
                 master,
                 image_path: str,
                 description: str = "",
                 max_width: int = 200,
                 max_height: int = 150,
                 **kwargs):
        super().__init__(master, **kwargs)

        self.image_path = image_path
        self.description = description
        self.max_width = max_width
        self.max_height = max_height
        self.thumbnail = None
        self.full_image = None

        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса"""
        self.configure(corner_radius=8, border_width=1, border_color="#ccc")

        # Загрузка и обработка изображения
        try:
            image = Image.open(self.image_path)
            self.full_image = image

            # Создание миниатюры
            image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
            self.thumbnail = ImageTk.PhotoImage(image)

            # Отображение миниатюры
            self.image_label = ctk.CTkLabel(
                self,
                image=self.thumbnail,
                text=""
            )
            self.image_label.pack(pady=5, padx=5)

        except Exception as e:
            # Если изображение не загрузилось
            self.image_label = ctk.CTkLabel(
                self,
                text=f"Изображение\nне загружено",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            self.image_label.pack(pady=5, padx=5)

        # Описание
        if self.description:
            self.desc_label = ctk.CTkLabel(
                self,
                text=self.description,
                font=ctk.CTkFont(size=11),
                wraplength=self.max_width - 10
            )
            self.desc_label.pack(pady=(0, 5))

        # Привязка событий для увеличения
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        if hasattr(self, 'image_label'):
            self.image_label.bind("<Enter>", self._on_enter)
            self.image_label.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """При наведении курсора"""
        self.configure(cursor="hand2")

    def _on_leave(self, event):
        """При уходе курсора"""
        self.configure(cursor="")

    def show_full_size(self):
        """Показать изображение в полном размере"""
        if self.full_image:
            # Создаем окно для просмотра
            viewer = ImageViewerWindow(self.full_image, self.description)
            viewer.show()

class ImageViewerWindow:
    def __init__(self, image: Image.Image, title: str = ""):
        self.image = image
        self.title = title

        self.window = ctk.CTkToplevel()
        self.window.title(title or "Просмотр изображения")

        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса окна просмотра"""
        self.window.geometry(f"{self.image.width}x{self.image.height}")

        # Конвертируем изображение для tkinter
        tk_image = ImageTk.PhotoImage(self.image)

        # Отображаем изображение
        label = ctk.CTkLabel(self.window, image=tk_image, text="")
        label.image = tk_image  # Сохраняем ссылку
        label.pack(fill="both", expand=True)

        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            self.window,
            text="Закрыть",
            command=self.window.destroy,
            width=100,
            height=30
        )
        close_btn.pack(pady=10)

        # Привязка клавиши Escape
        self.window.bind("<Escape>", lambda e: self.window.destroy())

    def show(self):
        """Показать окно"""
        self.window.mainloop()
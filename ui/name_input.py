import customtkinter as ctk
from tkinter import messagebox
from typing import List, Callable, Optional

from core.file_manager import FileManager
from core.settings import AppSettings
from ui.ui_config import apply_adaptive_scaling, center_window_adaptive

class NameInputWindow:
    """Окно ввода имени пользователя"""

    def __init__(self, on_name_entered: Callable[[str, List], None], settings: Optional[AppSettings] = None):
        self.on_name_entered = on_name_entered
        self.questions = []
        self.settings = settings or AppSettings()

        self.root = ctk.CTk()
        apply_adaptive_scaling(self.root)
        self._setup_ui()
        self._center_window(500, 350)

        # Защита от двойного закрытия
        self._is_closing = False

    def _setup_ui(self):
        self.root.title("Ввод данных")

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._safe_destroy)

        # Основной фрейм
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Введите ваше имя",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(18, 10))

        hint_label = ctk.CTkLabel(
            main_frame,
            text="Имена можно вводить вручную — они сохраняются для следующих запусков.",
            font=ctk.CTkFont(size=12),
            text_color=("#5f5f5f", "#b5b5b5"),
            wraplength=420,
            justify="center"
        )
        hint_label.pack(pady=(0, 16))

        # Загрузка существующих имен
        file_manager = FileManager()
        base_names, user_names = file_manager.load_names()
        all_names = base_names if self.settings.NAME_RESTRICT_TO_LIST else user_names

        # Поле ввода
        if all_names:
            # Используем combobox если есть имена в базе
            self.name_var = ctk.StringVar()

            name_label = ctk.CTkLabel(
                main_frame,
                text="Выберите или введите имя:",
                font=ctk.CTkFont(size=14)
            )
            name_label.pack(pady=(0, 5))

            combo_state = "readonly" if self.settings.NAME_RESTRICT_TO_LIST else "normal"
            self.name_combo = ctk.CTkComboBox(
                main_frame,
                values=all_names,
                variable=self.name_var,
                width=300,
                height=40,
                font=ctk.CTkFont(size=14),
                state=combo_state
            )
            self.name_combo.pack(pady=10)
            self.name_combo.set("")
            self.name_combo.bind("<Return>", lambda e: self._submit())
            self.name_combo.focus()

        else:
            # Используем поле ввода если нет имен
            name_label = ctk.CTkLabel(
                main_frame,
                text="Введите ваше имя:",
                font=ctk.CTkFont(size=14)
            )
            name_label.pack(pady=(0, 5))

            self.name_entry = ctk.CTkEntry(
                main_frame,
                width=300,
                height=40,
                font=ctk.CTkFont(size=14),
                placeholder_text="Введите имя..."
            )
            self.name_entry.pack(pady=10)
            self.name_entry.bind("<Return>", lambda e: self._submit())
            self.name_entry.focus()


        if self.settings.NAME_RESTRICT_TO_LIST and not all_names:
            warning = ctk.CTkLabel(
                main_frame,
                text="⚠ Список имен пуст. Добавьте имена в names_base.txt",
                text_color="#FF9800",
                font=ctk.CTkFont(size=12)
            )
            warning.pack(pady=(4, 8))

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=30)

        self.submit_btn = ctk.CTkButton(
            button_frame,
            text="Продолжить",
            command=self._submit,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50"
        )
        self.submit_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self._cancel,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#F44336"
        )
        cancel_btn.pack(side="right", padx=10)

    def _center_window(self, width: int, height: int):
        """Центрирование окна"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        center_window_adaptive(self.root, width, height)

    def _submit(self):
        """Обработка введенного имени"""
        if self._is_closing:
            return

        # Получаем имя в зависимости от типа поля
        if hasattr(self, 'name_combo'):
            name = self.name_combo.get().strip()
        elif hasattr(self, 'name_entry'):
            name = self.name_entry.get().strip()
        else:
            name = ""

        if not name:
            messagebox.showwarning("Внимание", "Пожалуйста, введите ваше имя!")
            return

        if self.settings.NAME_RESTRICT_TO_LIST:
            file_manager = FileManager()
            base_names, _ = file_manager.load_names()
            if name not in base_names:
                messagebox.showwarning("Внимание", "Можно выбрать только имя из names_base.txt")
                return

        # Сохраняем имя
        file_manager = FileManager()
        file_manager.save_name(name)

        # Мягко скрываем окно, затем запускаем следующий шаг.
        # Это снижает вероятность ошибок click_animation/update в CTk after-скриптах.
        self._is_closing = True
        try:
            self.root.withdraw()
        except Exception:
            pass

        try:
            self.on_name_entered(name, self.questions)
        except Exception as e:
            print(f"Ошибка при обработке имени: {e}")
            try:
                self.root.deiconify()
            except Exception:
                pass
            self._is_closing = False
            return

        try:
            self.root.after(180, self._safe_destroy)
        except Exception:
            self._safe_destroy()

    def _safe_destroy(self):
        """Безопасное закрытие окна"""
        self._is_closing = True
        try:
            self.root.destroy()
        except Exception:
            pass

    def _cancel(self):
        """Отмена и возврат"""
        self._safe_destroy()
        # Импортируем здесь, чтобы избежать циклических импортов
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import PyQuizApp
        app = PyQuizApp()
        app.run()

    def show(self):
        """Показать окно"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Ошибка в окне ввода имени: {e}")
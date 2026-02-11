import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from typing import List, Callable

from core.models import Quiz
from core.parser import QuizParser
from core.file_manager import FileManager
from core.settings import SettingsManager
from ui.test_selection_window import TestSelectionWindow
from ui.settings_window import SettingsWindow
from ui.ui_config import apply_adaptive_scaling, center_window_adaptive


class MainWindow:
    """Главное окно выбора тестов"""

    def __init__(self, on_test_selected: Callable[[List[Quiz]], None]):
        self.root = ctk.CTk()
        self.on_test_selected = on_test_selected
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()

        apply_adaptive_scaling(self.root)
        self._setup_ui()
        self._center_window(780, 560)

    def _setup_ui(self):
        self.root.title("СЭТ")

        ctk.CTkLabel(
            self.root,
            text="СЭТ - Система Экзаменационного Тестирования",
            font=ctk.CTkFont(size=24, weight="bold"),
            wraplength=740,
            justify="center",
        ).pack(pady=(26, 18))

        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=16, padx=48, fill="both", expand=True)

        button_style = {"height": 54, "font": ctk.CTkFont(size=16), "corner_radius": 10}

        ctk.CTkButton(button_frame, text="📁 Выбрать тест из готовых", command=self._select_from_existing, **button_style).pack(pady=8, fill="x")
        ctk.CTkButton(button_frame, text="🚀 Запустить все тесты", command=self._run_all_tests, **button_style).pack(pady=8, fill="x")
        ctk.CTkButton(button_frame, text="📤 Загрузить свой файл теста", command=self._load_custom_file, **button_style).pack(pady=8, fill="x")
        ctk.CTkButton(button_frame, text="⚙ Настройки", command=self._open_settings, **button_style).pack(pady=8, fill="x")
        ctk.CTkButton(button_frame, text="ℹ О программе", command=self._show_about, **button_style).pack(pady=8, fill="x")
        ctk.CTkButton(button_frame, text="🚪 Закрыть программу", command=self._exit_app, fg_color="#F44336", **button_style).pack(pady=8, fill="x")

        ctk.CTkLabel(
            self.root,
            text="© СЭТ - 2.2 | 2026 год | Михаил Пышенко | @sir_rumata",
            font=ctk.CTkFont(size=12)
        ).pack(pady=10)

    def _show_about(self):
        about = ctk.CTkToplevel(self.root)
        about.title("О программе")
        center_window_adaptive(about, 900, 720)
        about.transient(self.root)
        about.grab_set()

        frame = ctk.CTkScrollableFrame(about)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        text = (
            "СЭТ - Система Экзаменационного Тестирования\n\n"
            "Основные функции:\n"
            "• запуск одиночных и пакетных тестов\n"
            "• таймер и автоподбор времени\n"
            "• вопросы: один/несколько ответов, сопоставление, свободный ввод\n"
            "• пропуск вопросов с возвратом (карусель)\n"
            "• сохранение результатов и просмотр ошибок\n"
            "• отправка результатов в Telegram (опционально)\n"
            "• управление пользовательскими именами и тестами\n\n"
            "Синтаксис файлов тестов (.txt):\n"
            "1) Первая строка — название теста\n"
            "2) Вопрос: `1. Текст вопроса`\n"
            "3) Варианты: `A) ...`, `B) ...` ...\n"
            "4) Ответы:\n"
            "   • один: `B`\n"
            "   • несколько: `A, C, D`\n"
            "   • сопоставление: `A-K, B-K, ...`\n"
            "   • свободный ввод: строка(и) с корректным ответом\n"
            "5) Картинки в вопросе: `!(Подпись)[image.png]`\n\n"
            "Где хранятся данные:\n"
            "• настройки: ~/.local/share/pyquiz/settings.json (Linux)\n"
            "• пользовательские имена: .../pyquiz/names_user.txt\n"
            "• загруженные тесты: .../pyquiz/tests\n"
            "• результаты: .../pyquiz/results\n"
        )

        ctk.CTkLabel(frame, text=text, justify="left", anchor="w", wraplength=820, font=ctk.CTkFont(size=14)).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(frame, text="Закрыть", command=about.destroy, width=140).pack(pady=(4, 14))

        self.root.wait_window(about)

    def _center_window(self, width: int, height: int):
        center_window_adaptive(self.root, width, height)

    def _select_from_existing(self):
        self.settings = self.settings_manager.load()
        file_manager = FileManager()
        tests_tree = file_manager.find_question_files_recursive(include_base=not self.settings.HIDE_BUILTIN_TESTS)

        if not tests_tree:
            messagebox.showinfo("Информация", "Тесты не найдены!")
            return

        selection_window = TestSelectionWindow(self.root, tests_tree, self._on_tests_selected)
        selection_window.show()

    def _on_tests_selected(self, selected_files: List[str]):
        quizzes = []
        for filepath in selected_files:
            try:
                quizzes.append(QuizParser.parse_question_file(filepath))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка загрузки {filepath}:\n{e}")

        if quizzes:
            self.root.destroy()
            self.on_test_selected(quizzes)

    def _run_all_tests(self):
        self.settings = self.settings_manager.load()
        file_manager = FileManager()
        all_files = file_manager.get_all_test_files(include_base=not self.settings.HIDE_BUILTIN_TESTS)

        if not all_files:
            messagebox.showinfo("Информация", "Тесты не найдены!")
            return

        self._on_tests_selected(all_files)

    def _load_custom_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл с вопросами",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filepath:
            return

        try:
            file_manager = FileManager()
            new_path = file_manager.copy_to_user_tests(filepath)
            quiz = QuizParser.parse_question_file(new_path)
            self.root.destroy()
            self.on_test_selected([quiz])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла:\n{e}")

    def _open_settings(self):
        settings_window = SettingsWindow(self.root)
        settings_window.show()


    def _exit_app(self):
        """Полный выход из приложения без фоновых процессов."""
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        # Принудительное завершение защищает от подвисших after-скриптов CTk
        os._exit(0)

    def show(self):
        self.root.protocol("WM_DELETE_WINDOW", self._exit_app)
        self.root.mainloop()

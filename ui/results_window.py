import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
from datetime import datetime
from typing import Dict, Callable, Optional

from core.models import TestResult
from core.file_manager import FileManager
from services.telegram_service import TelegramService
from core.settings import AppSettings
from ui.ui_config import apply_adaptive_scaling, center_window_adaptive

class ResultsWindow:
    """Окно отображения результатов теста"""

    def __init__(self, result: TestResult, on_restart: Callable, settings: Optional[AppSettings] = None):
        self.result = result
        self.on_restart = on_restart
        self.settings = settings or AppSettings()

        self.root = ctk.CTk()
        apply_adaptive_scaling(self.root)
        self._setup_ui()
        self._center_window(700, 600)

    def _setup_ui(self):
        self.root.title("Результаты теста")
        self.root.protocol("WM_DELETE_WINDOW", self._new_test)

        # Основной контейнер с прокруткой
        main_frame = ctk.CTkScrollableFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Результаты тестирования",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # Карточка с основными результатами
        result_card = ctk.CTkFrame(main_frame, corner_radius=15)
        result_card.pack(fill="x", padx=20, pady=10)

        # Иконка результата
        result_icon = "✅" if self.result.passed else "❌"
        result_text = "СДАЛ" if self.result.passed else "НЕ СДАЛ"

        result_header = ctk.CTkLabel(
            result_card,
            text=f"{result_icon} {result_text}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#4CAF50" if self.result.passed else "#F44336"
        )
        result_header.pack(pady=15)

        # Детальная информация
        info_lines = [
            f"👤 Студент: {self.result.student_name}",
            f"📅 Дата и время: {self.result.timestamp}",
            f"📊 Всего вопросов: {self.result.total_questions}",
            f"✅ Правильных ответов: {self.result.correct_answers}",
            f"❌ Ошибок: {self.result.total_questions - self.result.correct_answers}",
        ]

        mode = self.settings.GRADE_MODE
        if mode == "all":
            info_lines.extend([
                f"📈 Процент выполнения: {self.result.percentage:.1f}%",
                f"🎯 Оценка (12-балльная): {self.result.grade_12}",
                f"🎯 Оценка (5-балльная): {self.result.grade_5}",
            ])
        elif isinstance(mode, str):
            if mode == "%":
                info_lines.append(f"📈 Процент выполнения: {self.result.percentage:.1f}%")
            elif mode == "12":
                info_lines.append(f"🎯 Оценка (12-балльная): {self.result.grade_12}")
            elif mode == "5":
                info_lines.append(f"🎯 Оценка (5-балльная): {self.result.grade_5}")
        else:
            if "%" in mode:
                info_lines.append(f"📈 Процент выполнения: {self.result.percentage:.1f}%")
            if "12" in mode:
                info_lines.append(f"🎯 Оценка (12-балльная): {self.result.grade_12}")
            if "5" in mode:
                info_lines.append(f"🎯 Оценка (5-балльная): {self.result.grade_5}")

        info_text = "\n".join(info_lines)

        if self.result.time_left:
            mins, secs = self.result.time_left
            info_text += f"\n⏱️ Осталось времени: {mins:02d}:{secs:02d}"

        if self.result.timeout:
            info_text += "\n⏰ Тест завершен по таймауту!"

        info_label = ctk.CTkLabel(
            result_card,
            text=info_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        info_label.pack(pady=15, padx=20)

        # Прогресс-бар
        progress_frame = ctk.CTkFrame(result_card)
        progress_frame.pack(fill="x", padx=20, pady=10)

        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Процент выполнения:",
            font=ctk.CTkFont(size=12)
        )
        progress_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=400
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(self.result.percentage / 100)

        # Цвет прогресс-бара
        if self.result.percentage >= 65:
            self.progress_bar.configure(progress_color="#4CAF50")
        elif self.result.percentage >= 50:
            self.progress_bar.configure(progress_color="#FF9800")
        else:
            self.progress_bar.configure(progress_color="#F44336")

        # Кнопки управления
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=30, padx=20, fill="x")

        # Кнопка сохранения
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Сохранить результат",
            command=self._save_result,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#2196F3"
        )
        save_btn.pack(pady=5)

        # Кнопка просмотра ошибок
        if self.settings.SHOW_STATS_BUTTON and self.result.correct_answers < self.result.total_questions:
            errors_btn = ctk.CTkButton(
                button_frame,
                text="📊 Показать ошибки",
                command=self._show_errors,
                width=180,
                height=40,
                font=ctk.CTkFont(size=14),
                fg_color="#FF9800"
            )
            errors_btn.pack(pady=5)

        # Кнопка нового теста
        new_test_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Новый тест",
            command=self._new_test,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#4CAF50"
        )
        new_test_btn.pack(pady=5)

        # Кнопка выхода
        exit_btn = ctk.CTkButton(
            button_frame,
            text="🚪 Выйти",
            command=self._exit_app,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#9E9E9E"
        )
        exit_btn.pack(pady=5)

        if self.settings.TELEGRAM_SEND_ON_RESULT:
            self._send_to_telegram()

    def _center_window(self, width: int, height: int):
        """Центрирование окна"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        center_window_adaptive(self.root, width, height)

    def _save_result(self):
        """Сохранение результата в файл"""
        file_manager = FileManager()

        # Подготовка данных для сохранения
        result_data = {
            'student_name': self.result.student_name,
            'timestamp': self.result.timestamp,
            'total_questions': self.result.total_questions,
            'correct_answers': self.result.correct_answers,
            'percentage': self.result.percentage,
            'grade_12': self.result.grade_12,
            'grade_5': self.result.grade_5,
            'passed': self.result.passed,
            'timeout': self.result.timeout,
            'detailed_results': self.result.detailed_results
        }

        if self.result.time_left:
            result_data['time_left_minutes'] = self.result.time_left[0]
            result_data['time_left_seconds'] = self.result.time_left[1]

        # Запрос места сохранения
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_filename = f"{self.result.student_name}_{timestamp}.json"

        filepath = None
        if self.settings.DEFAULT_SAVE_DIR == "auto":
            filepath = os.path.join(file_manager.get_user_results_dir(), default_filename)
        elif isinstance(self.settings.DEFAULT_SAVE_DIR, str) and self.settings.DEFAULT_SAVE_DIR:
            os.makedirs(self.settings.DEFAULT_SAVE_DIR, exist_ok=True)
            filepath = os.path.join(self.settings.DEFAULT_SAVE_DIR, default_filename)
        else:
            filepath = filedialog.asksaveasfilename(
                title="Сохранить результат",
                initialfile=default_filename,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
            )

            if not filepath:
                return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("Успех", f"Результат сохранён в файл:\n{filepath}")

            # Также сохраняем в пользовательскую директорию
            file_manager.save_result(result_data)

            if self.settings.TELEGRAM_SEND_ON_SAVE:
                self._send_to_telegram()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def _show_errors(self):
        """Отображение ошибок"""
        errors = [r for r in self.result.detailed_results if not r['is_correct']]

        if not errors:
            messagebox.showinfo("Информация", "У вас нет ошибок!")
            return

        # Создаем окно с ошибками
        errors_window = ctk.CTkToplevel(self.root)
        errors_window.title("Ошибки в тесте")
        errors_window.geometry("800x600")

        # Контейнер с прокруткой
        scroll_frame = ctk.CTkScrollableFrame(errors_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, error in enumerate(errors, 1):
            error_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
            error_frame.pack(fill="x", pady=5, padx=5)

            # Заголовок ошибки
            error_title = ctk.CTkLabel(
                error_frame,
                text=f"Ошибка {i}:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F44336"
            )
            error_title.pack(anchor="w", padx=10, pady=(10, 5))

            # Вопрос
            question_label = ctk.CTkLabel(
                error_frame,
                text=error['question'],
                font=ctk.CTkFont(size=12),
                wraplength=700,
                justify="left"
            )
            question_label.pack(anchor="w", padx=10, pady=5)

            # Ваш ответ
            user_answer = self._format_answer_for_display(
                error['question_type'],
                error['user_answer']
            )

            user_label = ctk.CTkLabel(
                error_frame,
                text=f"Ваш ответ: {user_answer}",
                font=ctk.CTkFont(size=11),
                text_color="#F44336"
            )
            user_label.pack(anchor="w", padx=10, pady=2)

            # Правильный ответ
            correct_answer = self._format_answer_for_display(
                error['question_type'],
                error['correct_answer']
            )

            correct_label = ctk.CTkLabel(
                error_frame,
                text=f"Правильный ответ: {correct_answer}",
                font=ctk.CTkFont(size=11),
                text_color="#4CAF50"
            )
            correct_label.pack(anchor="w", padx=10, pady=(2, 10))

        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            scroll_frame,
            text="Закрыть",
            command=errors_window.destroy,
            width=100
        )
        close_btn.pack(pady=20)

    def _format_answer_for_display(self, qtype: str, answer) -> str:
        """Форматирование ответа для отображения"""
        if qtype == "single":
            return str(answer)
        elif qtype == "multiple":
            return ", ".join(sorted(answer))
        elif qtype == "matching":
            return "; ".join([f"{a}–{b}" for a, b in sorted(answer)])
        elif qtype == "freeform":
            if isinstance(answer, list):
                return ", ".join(answer)
            return str(answer)
        return str(answer)

    def _send_to_telegram(self):
        """Отправка результата в Telegram"""
        try:
            telegram_service = TelegramService()
            if telegram_service.is_configured():
                telegram_service.send_result(self.result)
        except Exception:
            pass  # Игнорируем ошибки Telegram

    def _safe_destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def _new_test(self):
        """Запуск нового теста"""
        try:
            self.root.withdraw()
        except Exception:
            pass

        def _restart():
            self._safe_destroy()
            self.on_restart()

        try:
            self.root.after(80, _restart)
        except Exception:
            _restart()

    def _exit_app(self):
        """Выход из приложения"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти?"):
            try:
                self.root.quit()
            except Exception:
                pass
            self._safe_destroy()
            # Гарантированно завершаем процесс, чтобы не оставлять фоновые CTk after-сценарии
            os._exit(0)

    def show(self):
        """Показать окно"""
        self.root.mainloop()
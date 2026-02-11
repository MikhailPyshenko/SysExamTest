import customtkinter as ctk
from typing import List, Callable, Optional

from core.settings import AppSettings, resolve_time_limit_seconds
from ui.ui_config import apply_adaptive_scaling, center_window_adaptive


class PreparationWindow:
    """Окно подготовки к тесту"""

    def __init__(self, student_name: str, questions: List, on_start: Callable, settings: Optional[AppSettings] = None):
        self.student_name = student_name
        self.questions = questions
        self.on_start = on_start
        self.settings = settings or AppSettings()

        self.root = ctk.CTk()
        apply_adaptive_scaling(self.root)
        self._setup_ui()
        self._center_window(760, 520)

    def _format_estimated_time(self) -> str:
        secs = resolve_time_limit_seconds(self.settings.TIMER, len(self.questions))
        if secs <= 0:
            return "⏳ Время: без ограничения"
        mins, sec = divmod(secs, 60)
        if mins >= 60:
            h, m = divmod(mins, 60)
            return f"⏳ Расчётное время: {h} ч {m:02d} мин"
        return f"⏳ Расчётное время: {mins:02d}:{sec:02d}"

    def _setup_ui(self):
        self.root.title("Подготовка к тесту")

        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=26, pady=26)

        ctk.CTkLabel(
            main_frame,
            text="Готовы к экзаменационному тестированию?",
            font=ctk.CTkFont(size=30, weight="bold"),
            justify="center",
        ).pack(pady=(14, 24))

        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=20, pady=12)

        details = (
            f"👤 Участник: {self.student_name}\n"
            f"📚 Количество вопросов: {len(self.questions)}\n"
            f"{self._format_estimated_time()}\n\n"
            "✨ Рекомендации перед стартом:\n"
            "• Убедитесь, что вас ничего не отвлекает\n"
            "• Читайте формулировки внимательно\n"
            "• Сложные вопросы можно пропустить и вернуться позже"
        )

        ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=16),
            justify="left",
            wraplength=700,
        ).pack(pady=18, padx=20)

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=22)

        ctk.CTkButton(
            button_frame,
            text="🚀 Начать тест",
            command=self._start_test,
            width=230,
            height=56,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
        ).pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Отмена",
            command=self._cancel,
            width=180,
            height=44,
            font=ctk.CTkFont(size=15),
            fg_color="#9E9E9E",
        ).pack(pady=8)

    def _center_window(self, width: int, height: int):
        center_window_adaptive(self.root, width, height)

    def _safe_destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def _start_test(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

        try:
            self.on_start(self.student_name, self.questions)
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass
            raise

        try:
            self.root.after(180, self._safe_destroy)
        except Exception:
            self._safe_destroy()

    def _cancel(self):
        self._safe_destroy()
        from main import PyQuizApp
        app = PyQuizApp()
        app.run()

    def show(self):
        self.root.mainloop()

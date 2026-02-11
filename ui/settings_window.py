import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.file_manager import FileManager
from core.settings import AppSettings, SettingsManager
from ui.ui_config import apply_global_appearance, center_window_adaptive


class SettingsWindow:
    def __init__(self, parent, on_saved=None):
        self.parent = parent
        self.on_saved = on_saved
        self.settings_manager = SettingsManager()
        self.file_manager = FileManager()
        self.settings = self.settings_manager.load()

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Настройки")
        center_window_adaptive(self.window, 980, 860)
        self.window.transient(parent)
        self.window.grab_set()

        self._setup_ui()

    def _setup_ui(self):
        frame = ctk.CTkScrollableFrame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Настройки PyQuiz", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        self.timer_var = ctk.StringVar(value=str(self.settings.TIMER))
        self._entry_row(frame, "⏱ Время теста", "0 = без лимита, A = 1 мин/вопрос, A(1.1) = 1.1 мин/вопрос", self.timer_var)

        self.show_timer_var = ctk.BooleanVar(value=self.settings.SHOW_TIMER)
        self._switch_row(frame, "Показывать таймер", self.show_timer_var)

        self.max_questions_var = ctk.StringVar(value=str(self.settings.MAX_QUESTIONS))
        self._entry_row(frame, "Лимит вопросов", "0 = все вопросы, N = случайные N из банка", self.max_questions_var)

        self.show_stats_var = ctk.BooleanVar(value=self.settings.SHOW_STATS_BUTTON)
        self._switch_row(frame, "Показывать кнопку 'Ошибки' в результате", self.show_stats_var)

        self.disable_focus_var = ctk.BooleanVar(value=self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS)
        self._switch_row(frame, "Запретить сворачивание во время теста", self.disable_focus_var)

        self.hide_builtin_tests_var = ctk.BooleanVar(value=self.settings.HIDE_BUILTIN_TESTS)
        self._switch_row(frame, "Скрыть стандартные тесты", self.hide_builtin_tests_var)

        self.name_restrict_var = ctk.BooleanVar(value=self.settings.NAME_RESTRICT_TO_LIST)
        self._switch_row(frame, "Имя только из names_base.txt", self.name_restrict_var)

        grade_mode_initial = self.settings.GRADE_MODE if isinstance(self.settings.GRADE_MODE, str) else ",".join(self.settings.GRADE_MODE)
        self.grade_mode_var = ctk.StringVar(value=grade_mode_initial)
        self._entry_row(frame, "Формат оценок", "all | % | 12 | 5 | либо список: 12,%", self.grade_mode_var)

        self.pass_threshold_var = ctk.StringVar(value=str(self.settings.PASS_THRESHOLD))
        self._entry_row(frame, "Порог сдачи (%)", "Можно дробное число", self.pass_threshold_var)

        self.auto_next_var = ctk.BooleanVar(value=self.settings.AUTO_NEXT)
        self._switch_row(frame, "Автопереход к следующему вопросу", self.auto_next_var)

        self.telegram_on_result_var = ctk.BooleanVar(value=self.settings.TELEGRAM_SEND_ON_RESULT)
        self._switch_row(frame, "Отправлять результат в Telegram при завершении", self.telegram_on_result_var)

        self.telegram_on_save_var = ctk.BooleanVar(value=self.settings.TELEGRAM_SEND_ON_SAVE)
        self._switch_row(frame, "Отправлять в Telegram при сохранении", self.telegram_on_save_var)

        self.default_save_var = ctk.StringVar(value="" if self.settings.DEFAULT_SAVE_DIR is None else str(self.settings.DEFAULT_SAVE_DIR))
        self._entry_row(frame, "Папка сохранения", "Пусто/None = диалог, auto = папка приложения, либо путь", self.default_save_var)

        theme_frame = ctk.CTkFrame(frame)
        theme_frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(theme_frame, text="Тема оформления", width=420, anchor="w").pack(side="left", padx=8, pady=8)
        self.theme_var = ctk.StringVar(value=self.settings.THEME)
        ctk.CTkOptionMenu(theme_frame, variable=self.theme_var, values=["dark", "light", "system"]).pack(side="right", padx=8, pady=8)

        actions = ctk.CTkFrame(frame)
        actions.pack(fill="x", padx=20, pady=8)
        ctk.CTkButton(actions, text="Выбрать папку сохранения", command=self._pick_dir).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(actions, text="Удалить пользовательские имена", command=self._delete_user_names, fg_color="#FF9800").pack(side="left", padx=8, pady=8)
        ctk.CTkButton(actions, text="Удалить загруженные тесты", command=self._delete_user_tests, fg_color="#FF5722").pack(side="left", padx=8, pady=8)
        ctk.CTkButton(actions, text="Сбросить настройки по умолчанию", command=self._reset_defaults, fg_color="#607D8B").pack(side="left", padx=8, pady=8)

        buttons = ctk.CTkFrame(frame)
        buttons.pack(fill="x", padx=20, pady=(8, 20))
        ctk.CTkButton(buttons, text="Сохранить", command=self._save, fg_color="#4CAF50").pack(side="right", padx=8, pady=8)
        ctk.CTkButton(buttons, text="Отмена", command=self.window.destroy, fg_color="#9E9E9E").pack(side="right", padx=8, pady=8)

    def _entry_row(self, parent, title, hint, var):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=20, pady=6)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ctk.CTkLabel(left, text=title, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=hint, anchor="w", justify="left", text_color=("#5f5f5f", "#b5b5b5"), wraplength=470).pack(anchor="w")

        ctk.CTkEntry(row, textvariable=var, width=260).pack(side="right", padx=8, pady=8)

    def _switch_row(self, parent, title, var):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(row, text=title, anchor="w", justify="left", wraplength=700).pack(side="left", padx=8, pady=8, fill="x", expand=True)
        ctk.CTkSwitch(row, text="", variable=var).pack(side="right", padx=8, pady=8)

    def _apply_settings_to_ui(self, settings: AppSettings):
        self.timer_var.set(str(settings.TIMER))
        self.show_timer_var.set(settings.SHOW_TIMER)
        self.max_questions_var.set(str(settings.MAX_QUESTIONS))
        self.show_stats_var.set(settings.SHOW_STATS_BUTTON)
        self.disable_focus_var.set(settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS)
        self.hide_builtin_tests_var.set(settings.HIDE_BUILTIN_TESTS)
        self.name_restrict_var.set(settings.NAME_RESTRICT_TO_LIST)
        grade_mode = settings.GRADE_MODE if isinstance(settings.GRADE_MODE, str) else ",".join(settings.GRADE_MODE)
        self.grade_mode_var.set(grade_mode)
        self.pass_threshold_var.set(str(settings.PASS_THRESHOLD))
        self.auto_next_var.set(settings.AUTO_NEXT)
        self.telegram_on_result_var.set(settings.TELEGRAM_SEND_ON_RESULT)
        self.telegram_on_save_var.set(settings.TELEGRAM_SEND_ON_SAVE)
        self.default_save_var.set("" if settings.DEFAULT_SAVE_DIR is None else str(settings.DEFAULT_SAVE_DIR))
        self.theme_var.set(settings.THEME)

    def _reset_defaults(self):
        if not messagebox.askyesno("Сброс настроек", "Вернуть настройки по умолчанию?"):
            return
        defaults = AppSettings()
        self.settings_manager.save(defaults)
        self.settings = defaults
        self._apply_settings_to_ui(defaults)
        apply_global_appearance(defaults)
        messagebox.showinfo("Настройки", "Сброшено на значения по умолчанию")

    def _pick_dir(self):
        path = filedialog.askdirectory(title="Выберите папку для сохранения")
        if path:
            self.default_save_var.set(path)

    def _delete_user_names(self):
        if not messagebox.askyesno("Подтверждение", "Удалить все пользовательские имена?"):
            return
        self.file_manager.clear_user_names()
        messagebox.showinfo("Готово", "Пользовательские имена удалены")

    def _delete_user_tests(self):
        if not messagebox.askyesno("Подтверждение", "Удалить все загруженные пользователем тесты?"):
            return
        removed = self.file_manager.clear_user_tests()
        messagebox.showinfo("Готово", f"Удалено тестов: {removed}")

    def _save(self):
        try:
            timer_raw = self.timer_var.get().strip()
            timer: object = timer_raw
            if timer_raw.replace(".", "", 1).isdigit():
                timer = float(timer_raw)

            mode_text = self.grade_mode_var.get().strip()
            if "," in mode_text:
                grade_mode = [p.strip() for p in mode_text.split(",") if p.strip()]
            else:
                grade_mode = mode_text

            save_dir = self.default_save_var.get().strip()
            if save_dir.lower() == "none" or save_dir == "":
                save_dir = None

            settings = AppSettings(
                TIMER=timer,
                SHOW_TIMER=self.show_timer_var.get(),
                MAX_QUESTIONS=int(self.max_questions_var.get() or 0),
                SHOW_STATS_BUTTON=self.show_stats_var.get(),
                DISABLE_MINIMIZE_AND_FOCUS_LOSS=self.disable_focus_var.get(),
                NAME_RESTRICT_TO_LIST=self.name_restrict_var.get(),
                GRADE_MODE=grade_mode,
                PASS_THRESHOLD=float(self.pass_threshold_var.get() or 65),
                AUTO_NEXT=self.auto_next_var.get(),
                TELEGRAM_SEND_ON_RESULT=self.telegram_on_result_var.get(),
                TELEGRAM_SEND_ON_SAVE=self.telegram_on_save_var.get(),
                DEFAULT_SAVE_DIR=save_dir,
                THEME=self.theme_var.get(),
                HIDE_BUILTIN_TESTS=self.hide_builtin_tests_var.get(),
            )

            normalized = self.settings_manager._normalize(settings.__dict__, AppSettings())
            self.settings_manager.save(AppSettings(**normalized))
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте числовые значения в настройках")
            return

        apply_global_appearance(AppSettings(**normalized))
        messagebox.showinfo("Настройки", "Настройки сохранены")
        self.window.destroy()
        if self.on_saved:
            self.on_saved()

    def show(self):
        self.parent.wait_window(self.window)

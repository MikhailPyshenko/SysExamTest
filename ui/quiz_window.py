import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, TclError
from typing import Optional, Dict, Any
import os
from PIL import Image, ImageTk

from core.models import Question, QuestionType
from core.quiz_logic import QuizEngine
from core.settings import AppSettings
from core.file_manager import FileManager
from ui.widgets.custom_dropdown import CustomDropdown
from ui.ui_config import apply_adaptive_scaling


class QuizWindow:
    """Окно тестирования с поддержкой изображений"""

    def __init__(self, quiz_engine: QuizEngine, on_finish: callable, settings: Optional[AppSettings] = None, on_cancel: Optional[callable] = None):
        self.quiz_engine = quiz_engine
        self.on_finish = on_finish
        self.settings = settings or AppSettings()
        self.on_cancel = on_cancel

        self._closed = False
        self.root = ctk.CTk()
        self.scale, self.font_scale = apply_adaptive_scaling(self.root)
        self._setup_ui()

        self._apply_fullscreen_safe()

        if self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS:
            try:
                self.root.attributes("-topmost", True)
            except Exception:
                pass
            self.root.bind("<Unmap>", self._prevent_minimize)

        self.current_question: Optional[Question] = None
        self.user_inputs: Dict[str, Any] = {}
        self.images_cache = []
        self._image_path_cache = {}
        self.image_overlay = None
        self.image_overlay_label = None
        self._timer_after_id = None
        self._focus_guard_after_id = None
        self._allow_external_focus = False

        # Карусель пропущенных вопросов
        self.pending_questions = []
        self.answered_ids = set()

        self._load_next_question()
        self._schedule_focus_guard()

    def _apply_fullscreen_safe(self):
        """Безопасное включение полноэкранного режима (с fallback)."""
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Рассчитываем высоту для каждого раздела
        if screen_height <= 768:
            # Для очень маленьких экранов (768p)
            top_height = 60
            bottom_height = 80
            question_ratio = 0.35
            answer_ratio = 0.40
        elif screen_height <= 1080:
            # Для FullHD
            top_height = 70
            bottom_height = 90
            question_ratio = 0.40
            answer_ratio = 0.45
        else:
            # Для больших экранов
            top_height = 80
            bottom_height = 100
            question_ratio = 0.45
            answer_ratio = 0.50

        # Вычисляем доступную высоту для вопросов и ответов
        available_height = screen_height - top_height - bottom_height - 40  # 40px для отступов

        question_height = int(available_height * question_ratio)
        answer_height = int(available_height * answer_ratio)

        print(f"DEBUG: Screen: {screen_width}x{screen_height}")
        print(f"DEBUG: Available: {available_height}, Q: {question_height}, A: {answer_height}")

        try:
            self.root.attributes("-fullscreen", True)
        except Exception:
            # Если полноэкранный режим не работает, устанавливаем размер вручную
            self.root.geometry(f"{screen_width}x{screen_height}")

    def _setup_ui(self):
        self.root.title("Тестирование")

        # Создаем основную сетку
        self.root.grid_rowconfigure(0, weight=0)  # верхняя панель (таймер)
        self.root.grid_rowconfigure(1, weight=1)  # вопрос
        self.root.grid_rowconfigure(2, weight=1)  # ответы
        self.root.grid_rowconfigure(3, weight=0)  # кнопки
        self.root.grid_columnconfigure(0, weight=1)

        # Верхняя панель с таймером и прогрессом
        top_frame = ctk.CTkFrame(self.root)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=0)

        # Таймер слева
        self.timer_label = ctk.CTkLabel(
            top_frame,
            text="",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.timer_label.grid(row=0, column=0, sticky="w", padx=12, pady=5)

        if not self.settings.SHOW_TIMER:
            self.timer_label.grid_remove()

        # Прогресс справа
        self.progress_label = ctk.CTkLabel(
            top_frame,
            text="",
            font=ctk.CTkFont(size=16)
        )
        self.progress_label.grid(row=0, column=1, sticky="e", padx=12, pady=5)

        # Фрейм с вопросом
        self.question_frame = ctk.CTkScrollableFrame(self.root)
        self.question_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Фрейм с ответами
        self.answers_frame = ctk.CTkScrollableFrame(self.root)
        self.answers_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # КОНТЕЙНЕР ДЛЯ КНОПОК - ВСЕГДА ВИДИМЫЙ
        bottom_frame = ctk.CTkFrame(self.root, height=80)  # фиксированная высота
        bottom_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))
        bottom_frame.grid_propagate(False)  # фиксируем высоту

        # Конфигурация столбцов в нижнем фрейме
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=0)
        bottom_frame.grid_columnconfigure(2, weight=0)
        bottom_frame.grid_columnconfigure(3, weight=1)

        # Кнопки в нижнем фрейме
        screen_width = self.root.winfo_screenwidth()

        if screen_width < 1366:
            # Для маленьких экранов - маленькие кнопки
            btn_width = 120
            btn_height = 38
            font_size = 13
            padx = 5
        elif screen_width < 1920:
            # Для средних экранов
            btn_width = 140
            btn_height = 42
            font_size = 14
            padx = 10
        else:
            # Для больших экранов
            btn_width = 160
            btn_height = 46
            font_size = 15
            padx = 15

        # Кнопка Пропустить
        self.skip_btn = ctk.CTkButton(
            bottom_frame,
            text="Пропустить",
            command=self._skip_question,
            width=btn_width,
            height=btn_height,
            fg_color="#FF9800",
            font=ctk.CTkFont(size=font_size, weight="bold")
        )
        self.skip_btn.grid(row=0, column=1, sticky="ew", padx=padx, pady=15)

        # Кнопка Далее (если не AUTO_NEXT)
        if not self.settings.AUTO_NEXT:
            self.next_btn = ctk.CTkButton(
                bottom_frame,
                text="Далее",
                command=self._next_question,
                width=btn_width,
                height=btn_height,
                fg_color="#4CAF50",
                font=ctk.CTkFont(size=font_size, weight="bold")
            )
            self.next_btn.grid(row=0, column=2, sticky="ew", padx=padx, pady=15)

        # Кнопка Выйти - всегда справа
        exit_btn = ctk.CTkButton(
            bottom_frame,
            text="❌ Выйти",
            command=self._exit_test,
            width=btn_width,
            height=btn_height,
            fg_color="#F44336",
            font=ctk.CTkFont(size=font_size, weight="bold")
        )
        exit_btn.grid(row=0, column=3, sticky="e", padx=padx, pady=15)

        # Обновляем геометрию для правильного распределения
        self.root.update_idletasks()

    def _schedule_focus_guard(self):
        if self._closed or not self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS:
            return
        try:
            self._focus_guard_after_id = self.root.after(350, self._enforce_focus_guard)
        except Exception:
            self._focus_guard_after_id = None

    def _enforce_focus_guard(self):
        self._focus_guard_after_id = None
        if self._closed or not self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS or self._allow_external_focus:
            return

        try:
            if self.root.state() == "iconic":
                self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

        self._schedule_focus_guard()

    def _prevent_minimize(self, _event):
        if not self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS:
            return
        try:
            if self.root.state() == "iconic":
                self.root.deiconify()
                self.root.lift()
                self.root.after(80, self.root.focus_force)
        except Exception:
            pass

    def _update_timer(self):
        if self._closed or not self.quiz_engine.timer_active:
            return

        if not self.root.winfo_exists():
            return

        self.quiz_engine.update_timer()

        if self.quiz_engine.timeout_occurred:
            self._finish_test(timeout=True)
            return

        if self.quiz_engine.time_left > 0 and self.settings.SHOW_TIMER:
            mins, secs = divmod(self.quiz_engine.time_left, 60)
            self.timer_label.configure(text=f"⏱ {mins:02d}:{secs:02d}")

        try:
            self._timer_after_id = self.root.after(1000, self._update_timer)
        except Exception:
            self._timer_after_id = None

    def _get_next_question(self):
        next_q = self.quiz_engine.get_next_question()
        if next_q:
            return next_q

        # Если основной банк закончился — берём из карусели пропущенных
        while self.pending_questions:
            q = self.pending_questions.pop(0)
            if id(q) not in self.answered_ids:
                return q
        return None

    def _load_next_question(self):
        self._close_image_overlay()
        self.current_question = self._get_next_question()

        if not self.current_question:
            self._finish_test()
            return

        self.images_cache.clear()
        self._display_question()
        self._display_answers()
        self._update_progress()

    def _ensure_buttons_visible(self):
        """Гарантирует, что кнопки всегда видны."""
        self.root.update_idletasks()

        # Получаем координаты нижнего фрейма
        try:
            bottom_frame_y = self.root.grid_bbox(row=3, column=0)[1]
            screen_height = self.root.winfo_height()

            # Если нижний фрейм вне экрана, корректируем размеры
            if bottom_frame_y > screen_height * 0.8:  # Если занимает больше 80% экрана
                # Уменьшаем размеры scrollable frames
                self.question_frame.configure(height=int(screen_height * 0.3))
                self.answers_frame.configure(height=int(screen_height * 0.4))

                # Перерисовываем
                self.root.update_idletasks()
        except Exception as e:
            print(f"DEBUG: Error ensuring buttons: {e}")

    def _question_type_text(self, qtype: QuestionType) -> str:
        mapping = {
            QuestionType.SINGLE: "Один вариант",
            QuestionType.MULTIPLE: "Несколько вариантов",
            QuestionType.MATCHING: "Сопоставление",
            QuestionType.FREEFORM: "Свободный ввод",
        }
        return mapping.get(qtype, "Неизвестный тип")

    def _resolve_image_path(self, image_path: str) -> Optional[str]:
        """Надежно резолвит путь к картинке в рантайме."""
        if not image_path:
            return None

        normalized = image_path.strip().replace("\\", os.sep).replace("/", os.sep)
        if os.path.exists(normalized):
            return normalized

        file_manager = FileManager()
        rooted_candidates = [
            os.path.join(os.getcwd(), normalized),
            os.path.join(file_manager.get_base_tests_dir(), normalized),
            os.path.join(file_manager.get_user_tests_dir(), normalized),
            os.path.join(file_manager.get_base_tests_dir(), "images", normalized),
            os.path.join(file_manager.get_user_tests_dir(), "images", normalized),
        ]
        for candidate in rooted_candidates:
            if os.path.exists(candidate):
                return candidate

        filename = os.path.basename(normalized)
        key = filename.lower()
        if key in self._image_path_cache:
            cached = self._image_path_cache[key]
            return cached if cached and os.path.exists(cached) else None

        roots = [
            os.getcwd(),
            os.path.join(os.getcwd(), "images"),
            file_manager.get_base_tests_dir(),
            os.path.join(file_manager.get_base_tests_dir(), "images"),
            file_manager.get_user_tests_dir(),
            os.path.join(file_manager.get_user_tests_dir(), "images"),
        ]

        # Локальный поиск рядом с CWD в ограниченную глубину
        for root in roots:
            if not root or not os.path.isdir(root):
                continue
            try:
                for dirpath, _dirnames, files in os.walk(root):
                    for f in files:
                        if f.lower() == key:
                            found = os.path.join(dirpath, f)
                            self._image_path_cache[key] = found
                            return found
            except Exception:
                continue

        self._image_path_cache[key] = None
        return None

    def _load_tk_image(self, image_path: str, max_w: int, max_h: int):
        """Грузит картинку и возвращает ImageTk.PhotoImage либо None."""
        resolved = self._resolve_image_path(image_path)
        if not resolved:
            return None, None
        try:
            with Image.open(resolved) as src:
                image = src.convert("RGBA")
            image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            if image.width <= 0 or image.height <= 0:
                return None, resolved

            tk_image = ImageTk.PhotoImage(image, master=self.root)
            self.images_cache.append(tk_image)
            return tk_image, resolved
        except Exception:
            return None, resolved

    def _display_question(self):
        for widget in self.question_frame.winfo_children():
            widget.destroy()

        screen_width = self.root.winfo_screenwidth()

        # Адаптивные размеры шрифтов
        if screen_width <= 1366:
            info_font_size = 12
            question_font_size = 18
            image_size = (220, 180)
        else:
            info_font_size = 14
            question_font_size = 20
            image_size = (280, 220)

        info_label = ctk.CTkLabel(
            self.question_frame,
            text=f"Тип вопроса: {self._question_type_text(self.current_question.question_type)}",
            font=ctk.CTkFont(size=info_font_size, weight="bold"),
            text_color=("#505050", "#BFBFBF"),
        )
        info_label.pack(anchor="center", pady=(6, 4))

        source = getattr(self.current_question, "source_topic", "")
        if source:
            ctk.CTkLabel(
                self.question_frame,
                text=f"Тема: {source}",
                font=ctk.CTkFont(size=info_font_size - 1),
                text_color=("#5f5f5f", "#b5b5b5"),
                justify="center",
            ).pack(anchor="center", pady=(0, 4))

        question_label = ctk.CTkLabel(
            self.question_frame,
            text=self.current_question.text,
            font=ctk.CTkFont(size=question_font_size),
            justify="center",
            wraplength=min(1400, self.root.winfo_screenwidth() - 120),
        )
        question_label.pack(anchor="center", pady=10, padx=10)

        if self.current_question.images:
            images_frame = ctk.CTkFrame(self.question_frame)
            images_frame.pack(anchor="center", pady=10, padx=10)

            for desc, img_path in self.current_question.images:
                max_w, max_h = image_size
                tk_image, resolved = self._load_tk_image(img_path, max_w, max_h)

                if tk_image is None:
                    miss = resolved or img_path
                    ctk.CTkLabel(images_frame, text=f"[Не найдено изображение: {desc} | {os.path.basename(miss)}]",
                                 text_color="gray", font=ctk.CTkFont(size=10)).pack(anchor="w", pady=2)
                    continue

                img_frame_width = max_w + 20
                img_frame_height = max_h + 40

                img_frame = ctk.CTkFrame(images_frame, width=img_frame_width, height=img_frame_height)
                img_frame.pack_propagate(False)
                img_frame.pack(side="left", padx=6, pady=6)

                try:
                    img_label = tk.Label(img_frame, image=tk_image, bd=0, highlightthickness=0)
                    img_label._image_ref = tk_image
                    img_label.pack(pady=4)
                    img_label.bind("<Button-1>", lambda _e, p=resolved or img_path, d=desc: self._open_image_popup(p, d))
                except TclError:
                    ctk.CTkLabel(
                        img_frame,
                        text=f"[Ошибка отображения: {desc}]",
                        text_color="#FF9800",
                        wraplength=img_frame_width - 20,
                        font=ctk.CTkFont(size=10)
                    ).pack(pady=5)

                ctk.CTkLabel(img_frame, text=desc,
                             font=ctk.CTkFont(size=10),
                             wraplength=img_frame_width - 20).pack(pady=2)

    def _open_image_popup(self, image_path: str, description: str):
        """Показывает увеличенное изображение поверх текущего окна с затемнением."""
        self._close_image_overlay()
        self.root.update_idletasks()

        sw = self.root.winfo_width()
        sh = self.root.winfo_height()
        margin_x = max(60, int(sw * 0.08))
        margin_y = max(60, int(sh * 0.1))
        max_w = max(320, sw - margin_x * 2)
        max_h = max(240, sh - margin_y * 2 - 50)

        tk_image, resolved = self._load_tk_image(image_path, max_w, max_h)
        if tk_image is None:
            messagebox.showwarning("Изображение", f"Не удалось открыть изображение: {os.path.basename(image_path)}")
            return

        self.image_overlay = ctk.CTkFrame(self.root, fg_color=("#000000", "#000000"), corner_radius=0)
        self.image_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.image_overlay.lift()

        container = ctk.CTkFrame(self.image_overlay)
        container.place(relx=0.5, rely=0.5, anchor="center")

        try:
            self.image_overlay_label = tk.Label(container, image=tk_image, bd=0, highlightthickness=0)
            self.image_overlay_label._image_ref = tk_image
            self.image_overlay_label.pack(padx=18, pady=(18, 8))
        except TclError:
            ctk.CTkLabel(container, text="Не удалось отобразить изображение", text_color="#FF9800").pack(padx=18, pady=18)
            return

        if description:
            ctk.CTkLabel(container, text=description, justify="center", wraplength=max_w).pack(padx=14, pady=(0, 12))

        # Любой клик закрывает overlay
        self.image_overlay.bind("<Button-1>", lambda _e: self._close_image_overlay())
        container.bind("<Button-1>", lambda _e: self._close_image_overlay())
        self.image_overlay_label.bind("<Button-1>", lambda _e: self._close_image_overlay())

    def _close_image_overlay(self):
        if self.image_overlay is not None:
            try:
                self.image_overlay.destroy()
            except Exception:
                pass
        self.image_overlay = None
        self.image_overlay_label = None

    def _display_answers(self):
        for widget in self.answers_frame.winfo_children():
            widget.destroy()

        self.user_inputs.clear()

        self.answers_content = ctk.CTkFrame(self.answers_frame, fg_color="transparent")
        self.answers_content.pack(anchor="center", pady=8)

        if self.current_question.question_type in [QuestionType.SINGLE, QuestionType.MULTIPLE]:
            self._display_choice_answers()
        elif self.current_question.question_type == QuestionType.MATCHING:
            self._display_matching_answers()
        elif self.current_question.question_type == QuestionType.FREEFORM:
            self._display_freeform_answer()

    def _display_choice_answers(self):
        for option in self.current_question.options:
            var = ctk.BooleanVar(value=False)
            option_frame = ctk.CTkFrame(self.answers_content, fg_color="transparent")
            option_frame.pack(fill="x", pady=2, padx=20)

            checkbox = ctk.CTkCheckBox(
                option_frame,
                text=option,
                variable=var,
                command=lambda l=option[0]: self._on_checkbox_click(l),
                font=ctk.CTkFont(size=17),
            )
            checkbox.pack(anchor="w")
            self.user_inputs[option[0]] = var

    def _display_matching_answers(self):
        key_letters = {pair[0] for pair in self.current_question.correct_answer}
        key_texts = {}
        value_texts = {}

        for opt in self.current_question.options:
            letter = opt[0]
            text = opt[2:].strip()
            if letter in key_letters:
                key_texts[letter] = text
            else:
                value_texts[letter] = text

        value_options = list(value_texts.values())
        self.matching_inputs = {}

        host = ctk.CTkFrame(self.answers_content, fg_color="transparent")
        host.pack(anchor="center", pady=4)

        for key_letter in sorted(key_letters):
            row = ctk.CTkFrame(host, fg_color="transparent")
            row.pack(fill="x", pady=6, padx=20)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            key_label = ctk.CTkLabel(
                row,
                text=f"{key_letter}) {key_texts.get(key_letter, '')}",
                font=ctk.CTkFont(size=17),
                anchor="w",
                wraplength=min(980, int(self.root.winfo_screenwidth() * 0.5)),
                justify="left",
            )
            key_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

            dropdown = CustomDropdown(
                row,
                options=value_options,
                width=min(520, max(320, int(self.root.winfo_screenwidth() * 0.26))),
                height=44,
                font=ctk.CTkFont(size=14),
            )
            dropdown.grid(row=0, column=1, sticky="e")
            self.matching_inputs[key_letter] = dropdown

    def _display_freeform_answer(self):
        self.freeform_var = ctk.StringVar()

        container = ctk.CTkFrame(self.answers_content, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=16)

        width = min(1000, max(540, int(self.root.winfo_screenwidth() * 0.5)))
        self.freeform_entry = ctk.CTkEntry(
            container,
            textvariable=self.freeform_var,
            placeholder_text="Введите ваш ответ...",
            height=46,
            width=width,
            font=ctk.CTkFont(size=18),
        )
        self.freeform_entry.pack(anchor="center")
        self.freeform_entry.focus()
        self.freeform_entry.bind("<Return>", lambda e: self._next_question())

    def _on_checkbox_click(self, letter):
        if self.current_question.question_type == QuestionType.SINGLE:
            for l, var in self.user_inputs.items():
                if l != letter:
                    var.set(False)

        if self.settings.AUTO_NEXT:
            self.root.after(50, self._next_question)

    def _update_progress(self):
        total = len(self.quiz_engine.prepared_questions)
        answered = len(self.answered_ids)
        pending = len([q for q in self.pending_questions if id(q) not in self.answered_ids])
        self.progress_label.configure(text=f"Отвечено: {answered}/{total} | Пропущено: {pending}")

    def _skip_question(self):
        if self.current_question:
            qid = id(self.current_question)
            if qid not in self.answered_ids and self.current_question not in self.pending_questions:
                self.pending_questions.append(self.current_question)

        self._load_next_question()
        self._schedule_focus_guard()

    def _next_question(self):
        if not self._validate_answer():
            return

        user_answer = self._get_user_answer()
        if user_answer is not None:
            self.quiz_engine.check_answer(self.current_question, user_answer)
            qid = id(self.current_question)
            self.answered_ids.add(qid)

        self._load_next_question()
        self._schedule_focus_guard()

    def _validate_answer(self) -> bool:
        if self.current_question.question_type == QuestionType.FREEFORM:
            freeform_text = self.freeform_entry.get().strip() if hasattr(self, "freeform_entry") else self.freeform_var.get().strip()
            if not freeform_text:
                messagebox.showwarning("Внимание", "Введите ответ!")
                return False

        elif self.current_question.question_type in [QuestionType.SINGLE, QuestionType.MULTIPLE]:
            selected = [l for l, v in self.user_inputs.items() if v.get()]
            if not selected:
                messagebox.showwarning("Внимание", "Выберите хотя бы один вариант!")
                return False

        elif self.current_question.question_type == QuestionType.MATCHING:
            for dropdown in self.matching_inputs.values():
                if not dropdown.get().strip():
                    messagebox.showwarning("Внимание", "Заполните все сопоставления!")
                    return False

        return True

    def _get_user_answer(self):
        if self.current_question.question_type == QuestionType.FREEFORM:
            value = self.freeform_entry.get().strip() if hasattr(self, "freeform_entry") else self.freeform_var.get().strip()
            return value.lower()

        if self.current_question.question_type == QuestionType.SINGLE:
            for letter, var in self.user_inputs.items():
                if var.get():
                    return letter

        if self.current_question.question_type == QuestionType.MULTIPLE:
            return {l for l, v in self.user_inputs.items() if v.get()}

        if self.current_question.question_type == QuestionType.MATCHING:
            pairs = []
            for key_letter, dropdown in self.matching_inputs.items():
                selected_text = dropdown.get()
                for opt in self.current_question.options:
                    if opt[2:].strip() == selected_text:
                        pairs.append((key_letter, opt[0]))
                        break
            return pairs

        return None

    def _exit_test(self):
        self._allow_external_focus = True
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("Подтверждение")
        dlg.transient(self.root)
        dlg.grab_set()

        try:
            if self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS:
                dlg.attributes("-topmost", True)
        except Exception:
            pass

        w, h = 420, 180
        x = self.root.winfo_rootx() + max(40, (self.root.winfo_width() - w) // 2)
        y = self.root.winfo_rooty() + max(40, (self.root.winfo_height() - h) // 2)
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkLabel(dlg, text="Вы уверены, что хотите выйти?", font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(24, 18))

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=(0, 14))

        def _close_dialog(confirmed: bool):
            self._allow_external_focus = False
            try:
                dlg.grab_release()
            except Exception:
                pass
            try:
                dlg.destroy()
            except Exception:
                pass

            if confirmed:
                self._finish_test(cancelled=True)
                return

            if self.settings.DISABLE_MINIMIZE_AND_FOCUS_LOSS:
                try:
                    self.root.attributes("-topmost", True)
                    self.root.lift()
                    self.root.focus_force()
                except Exception:
                    pass

        ctk.CTkButton(btns, text="Да, выйти", width=140, fg_color="#F44336", command=lambda: _close_dialog(True)).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Нет", width=140, command=lambda: _close_dialog(False)).pack(side="left", padx=8)

        dlg.protocol("WM_DELETE_WINDOW", lambda: _close_dialog(False))
        self.root.wait_window(dlg)

    def _finish_test(self, timeout: bool = False, cancelled: bool = False):
        self._closed = True
        self._allow_external_focus = True

        try:
            if self._timer_after_id:
                self.root.after_cancel(self._timer_after_id)
        except Exception:
            pass
        self._timer_after_id = None

        try:
            if self._focus_guard_after_id:
                self.root.after_cancel(self._focus_guard_after_id)
        except Exception:
            pass
        self._focus_guard_after_id = None

        self._close_image_overlay()

        if cancelled:
            try:
                self.root.attributes("-topmost", False)
            except Exception:
                pass

            def _close_and_restart():
                try:
                    self.root.destroy()
                except Exception:
                    pass
                if self.on_cancel:
                    self.on_cancel()

            try:
                self.root.after(120, _close_and_restart)
            except Exception:
                _close_and_restart()
            return

        self.quiz_engine.timeout_occurred = timeout
        result = self.quiz_engine.calculate_result()

        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass

        def _close_and_finish():
            try:
                self.root.destroy()
            except Exception:
                pass
            self.on_finish(result)

        try:
            self.root.after(120, _close_and_finish)
        except Exception:
            _close_and_finish()

    def show(self):
        self.root.mainloop()

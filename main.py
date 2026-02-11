import sys
import os

# Добавляем текущую директорию в путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.models import Quiz
from core.quiz_logic import QuizEngine
from core.parser import QuizParser
from core.file_manager import FileManager
from core.settings import SettingsManager, resolve_time_limit_seconds

from ui.main_window import MainWindow
from ui.name_input import NameInputWindow
from ui.preparation import PreparationWindow
from ui.quiz_window import QuizWindow
from ui.results_window import ResultsWindow
from ui.ui_config import apply_global_appearance

class PyQuizApp:
    """Основной класс приложения"""

    def __init__(self):
        self.quizzes: list[Quiz] = []
        self.current_quiz_engine: QuizEngine = None
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()
        apply_global_appearance(self.settings)

    def run(self):
        """Запуск приложения"""
        print("Запуск PyQuiz...")

        # Главное окно выбора тестов
        self.settings = self.settings_manager.load()
        apply_global_appearance(self.settings)
        main_window = MainWindow(self.on_tests_selected)
        main_window.show()

    def on_tests_selected(self, quizzes: list[Quiz]):
        """Обработка выбранных тестов"""
        self.settings = self.settings_manager.load()
        self.quizzes = quizzes

        # Объединяем все вопросы из всех тестов
        all_questions = []
        for quiz in quizzes:
            all_questions.extend(quiz.questions)

        # Ограничение числа вопросов
        if self.settings.MAX_QUESTIONS > 0 and len(all_questions) > self.settings.MAX_QUESTIONS:
            import random
            all_questions = random.sample(all_questions, self.settings.MAX_QUESTIONS)

        # Окно ввода имени
        name_window = NameInputWindow(self.on_name_entered, settings=self.settings)
        name_window.questions = all_questions
        name_window.show()

    def on_name_entered(self, name: str, questions: list):
        """Обработка введенного имени"""
        # Окно подготовки
        prep_window = PreparationWindow(name, questions, self.start_quiz, settings=self.settings)
        prep_window.show()

    def start_quiz(self, student_name: str, questions: list):
        """Начало тестирования"""
        # Создаем движок тестирования
        time_limit = resolve_time_limit_seconds(self.settings.TIMER, len(questions))

        self.current_quiz_engine = QuizEngine(
            questions=questions,
            student_name=student_name,
            time_limit=time_limit,
            pass_threshold=self.settings.PASS_THRESHOLD
        )

        # Окно тестирования
        quiz_window = QuizWindow(
            self.current_quiz_engine,
            self.on_quiz_finished,
            settings=self.settings,
            on_cancel=self.restart_app
        )
        quiz_window.show()

    def on_quiz_finished(self, result):
        """Обработка завершения теста"""
        # Окно результатов
        results_window = ResultsWindow(result, self.restart_app, settings=self.settings)
        results_window.show()

    def restart_app(self):
        """Перезапуск приложения"""
        self.quizzes = []
        self.current_quiz_engine = None
        self.run()

if __name__ == "__main__":
    # Создаем необходимые директории
    file_manager = FileManager()
    file_manager._setup_directories()

    app = PyQuizApp()
    app.run()
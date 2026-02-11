import random
import string
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .models import Question, QuestionType, TestResult

from typing import Optional

class QuizEngine:
    """Движок тестирования"""

    def __init__(self, questions: List[Question], student_name: str, time_limit: int = 0, pass_threshold: float = 65.0):
        self.questions = questions
        self.student_name = student_name
        self.time_limit = time_limit  # в секундах
        self.pass_threshold = pass_threshold

        self._prepare_questions()
        self.reset()

    def _prepare_questions(self):
        """Подготовка вопросов: перемешивание и т.д."""
        prepared = []
        for q in self.questions:
            if q.question_type in [QuestionType.MATCHING, QuestionType.FREEFORM]:
                prepared.append(q)
            else:
                shuffled_q = self._shuffle_options(q)
                prepared.append(shuffled_q)

        random.shuffle(prepared)
        self.prepared_questions = prepared

    def _shuffle_options(self, question: Question) -> Question:
        """Перемешивает варианты ответов для вопросов с выбором"""
        if question.question_type not in [QuestionType.SINGLE, QuestionType.MULTIPLE]:
            return question

        option_pairs = [(opt[0], opt[2:]) for opt in question.options]
        random.shuffle(option_pairs)

        n = len(option_pairs)
        new_letters = list(string.ascii_uppercase[:n])
        if len(new_letters) < n:
            new_letters = [f"Opt{i+1}" for i in range(n)]

        old_to_new = {}
        new_options = []
        for i, (old_letter, text) in enumerate(option_pairs):
            new_letter = new_letters[i]
            old_to_new[old_letter] = new_letter
            new_options.append(f"{new_letter}) {text.strip()}")

        # Обновляем правильный ответ
        if question.question_type == QuestionType.SINGLE:
            new_correct = old_to_new.get(question.correct_answer, question.correct_answer)
        elif question.question_type == QuestionType.MULTIPLE:
            new_correct = {old_to_new.get(old_letter, old_letter) for old_letter in question.correct_answer}
        else:
            new_correct = question.correct_answer

        return Question(
            text=question.text,
            options=new_options,
            question_type=question.question_type,
            correct_answer=new_correct,
            images=question.images,
            source_topic=question.source_topic
        )

    def reset(self):
        """Сброс состояния теста"""
        self.current_index = -1
        self.score = 0
        self.results = []
        self.time_left = self.time_limit if self.time_limit > 0 else -1
        self.timer_active = (self.time_limit > 0)
        self.timeout_occurred = False

    def get_next_question(self) -> Optional[Question]:
        """Получение следующего вопроса"""
        if self.current_index + 1 >= len(self.prepared_questions):
            return None

        self.current_index += 1
        return self.prepared_questions[self.current_index]

    def check_answer(self, question: Question, user_answer: Any) -> bool:
        """Проверка ответа пользователя"""
        is_correct = self._compare_answers(
            question.question_type,
            user_answer,
            question.correct_answer
        )

        # Сохраняем результат
        result = {
            'question': question.text,
            'options': question.options,
            'question_type': question.question_type.value,
            'user_answer': user_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct
        }
        self.results.append(result)

        if is_correct:
            self.score += 1

        return is_correct

    def _compare_answers(self, qtype: QuestionType, user: Any, correct: Any) -> bool:
        """Сравнение ответов в зависимости от типа вопроса"""
        if qtype == QuestionType.SINGLE:
            return user == correct
        elif qtype == QuestionType.MULTIPLE:
            return user == correct
        elif qtype == QuestionType.MATCHING:
            return set(user) == set(correct)
        elif qtype == QuestionType.FREEFORM:
            # Для свободных ответов нормализуем пробелы
            if isinstance(user, str):
                user_normalized = " ".join(user.lower().split())
                return user_normalized in [self._normalize_freeform(ans) for ans in correct]
            return False
        return False

    def _normalize_freeform(self, text: str) -> str:
        """Нормализация текста для свободных ответов"""
        return " ".join(text.lower().split())

    def calculate_result(self) -> TestResult:
        """Расчёт итогового результата"""
        total = len(self.prepared_questions)
        percentage = (self.score / total * 100) if total > 0 else 0

        # Оценка по 12-балльной системе
        grade12 = self._calculate_12_grade(percentage)
        grade5 = self._calculate_5_grade(percentage)

        return TestResult(
            student_name=self.student_name,
            quiz_name="Тест",  # Можно передавать название
            total_questions=total,
            correct_answers=self.score,
            percentage=percentage,
            grade_12=grade12,
            grade_5=grade5,
            passed=percentage >= self.pass_threshold,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            time_left=self._get_time_left_tuple(),
            timeout=self.timeout_occurred,
            detailed_results=self.results
        )

    def _calculate_12_grade(self, percentage: float) -> int:
        """Расчёт оценки по 12-балльной системе"""
        if percentage >= 92: return 12
        elif percentage >= 83: return 11
        elif percentage >= 75: return 10
        elif percentage >= 67: return 9
        elif percentage >= 58: return 8
        elif percentage >= 50: return 7
        elif percentage >= 42: return 6
        elif percentage >= 33: return 5
        elif percentage >= 25: return 4
        elif percentage >= 17: return 3
        elif percentage >= 8: return 2
        elif percentage >= 1: return 1
        else: return 0

    def _calculate_5_grade(self, percentage: float) -> int:
        """Расчёт оценки по 5-балльной системе"""
        if percentage >= 90: return 5
        elif percentage >= 70: return 4
        elif percentage >= 50: return 3
        else: return 2

    def _get_time_left_tuple(self) -> Optional[Tuple[int, int]]:
        """Получение оставшегося времени в формате (минуты, секунды)"""
        if self.time_left <= 0:
            return None
        return divmod(self.time_left, 60)

    def update_timer(self, seconds: int = 1):
        """Обновление таймера"""
        if not self.timer_active or self.time_left <= 0:
            return

        self.time_left -= seconds
        if self.time_left <= 0:
            self.timeout_occurred = True
            self.timer_active = False
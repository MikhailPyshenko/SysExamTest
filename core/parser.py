import re
import os
from typing import Any, List, Optional, Tuple
from .models import Question, QuestionType, Quiz

class QuizParser:
    """Парсер тестов из текстовых файлов"""

    SECTION_HEADER_RE = re.compile(r"^(\d+)\.\s+(.+)$")
    QUESTION_HEADER_RE = re.compile(r"^(\d+(?:\.\d+)*)(?:\s+\(([^)]+)\))?\s+(.+)$")
    IMAGE_RE = re.compile(r"!\(\s*([^)]+?)\s*\)\[\s*([^]]+\.(?:png|jpg|jpeg|gif|bmp|webp))\s*\]", re.IGNORECASE)

    OPTION_RE = re.compile(r"^([A-ZА-ЯЁ])\)\s*(.+)$")
    ANSWER_CANDIDATE_RE = re.compile(r"^[A-ZА-ЯЁ](?:\s*-\s*[A-ZА-ЯЁ])?(?:\s*,\s*[A-ZА-ЯЁ](?:\s*-\s*[A-ZА-ЯЁ])?)*\s*$")

    @staticmethod
    def _strip_section_prefix(text: str) -> str:
        """Удаляет префикс нумерации вида `1.2. ` из строки."""
        return re.sub(r"^\d+(?:\.\d+)*\.\s*", "", text).strip()

    @staticmethod
    def _find_image_by_basename(filename: str, roots: List[str]) -> Optional[str]:
        """Ищет файл изображения по имени в наборах директорий (ограниченно)."""
        target = os.path.basename(filename).lower()
        for root in roots:
            if not root or not os.path.isdir(root):
                continue
            try:
                for dirpath, _dirnames, files in os.walk(root):
                    for f in files:
                        if f.lower() == target:
                            return os.path.join(dirpath, f)
            except Exception:
                continue
        return None

    @staticmethod
    def parse_answer_line(line: str) -> Tuple[Optional[QuestionType], Any]:
        """Парсит строку ответа"""
        line = line.strip().upper()
        pairs = []
        letters = []

        parts = [part.strip() for part in line.split(",") if part.strip()]
        for part in parts:
            match_pair = re.fullmatch(r"([A-ZА-ЯЁ])\s*-\s*([A-ZА-ЯЁ])", part)
            if match_pair:
                left, right = match_pair.group(1), match_pair.group(2)
                pairs.append((left, right))
            elif re.fullmatch(r"[A-ZА-ЯЁ]", part):
                letters.append(part)
            else:
                return None, None

        if pairs and not letters:
            return QuestionType.MATCHING, pairs
        elif letters and not pairs:
            if len(letters) == 1:
                return QuestionType.SINGLE, letters[0]
            else:
                return QuestionType.MULTIPLE, set(letters)
        else:
            return None, None

    @staticmethod
    def parse_question_file(filepath: str) -> Quiz:
        """Парсит файл с вопросами"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [line.rstrip() for line in f]
        except Exception:
            raise ValueError(f"Не удалось прочитать файл: {filepath}")

        if not lines:
            raise ValueError("Файл пуст")

        # Название теста
        title_line = lines[0].strip()
        test_name = QuizParser._strip_section_prefix(title_line) if title_line else os.path.basename(filepath)
        questions = []
        i = 1

        tests_root = os.path.abspath("tests")
        file_abs = os.path.abspath(filepath)
        if file_abs.startswith(tests_root):
            source_topic = os.path.dirname(os.path.relpath(file_abs, tests_root)).replace(os.sep, " / ")
        else:
            source_topic = os.path.basename(os.path.dirname(filepath))

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue


            question_text = QuizParser._strip_section_prefix(line)
            i += 1
            options = []
            images = []

            # Извлекаем изображения из текста вопроса
            file_dir = os.path.dirname(filepath)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            tests_root_abs = os.path.join(project_root, "tests")
            cwd = os.getcwd()
            for match in QuizParser.IMAGE_RE.finditer(question_text):
                rel_image_path = match.group(2).strip().replace("\\", os.sep).replace("/", os.sep)
                rel_image_path = rel_image_path.lstrip("/\\")

                candidates = [
                    os.path.join(file_dir, rel_image_path),
                    os.path.join(file_dir, "images", rel_image_path),
                    os.path.join(tests_root_abs, "images", rel_image_path),
                    os.path.join(project_root, "images", rel_image_path),
                    os.path.join(project_root, "tests", "images", rel_image_path),
                    os.path.join(cwd, rel_image_path),
                    os.path.join(cwd, "images", rel_image_path),
                ]
                resolved = next((c for c in candidates if os.path.exists(c)), None)

                if not resolved:
                    fallback = QuizParser._find_image_by_basename(
                        rel_image_path,
                        [
                            os.path.dirname(file_dir),
                            file_dir,
                            os.path.join(file_dir, "images"),
                            tests_root_abs,
                            os.path.join(tests_root_abs, "images"),
                            os.path.join(project_root, "images"),
                            cwd,
                        ],
                    )
                    resolved = fallback or candidates[0]

                images.append((match.group(1).strip(), resolved))

            # Очищаем текст вопроса от markdown-вставок изображений
            question_text = QuizParser.IMAGE_RE.sub("", question_text).strip()

            # Сбор вариантов ответов
            while i < len(lines) and lines[i].strip():
                s = lines[i].strip()
                if QuizParser.OPTION_RE.match(s):
                    options.append(s)
                    i += 1
                else:
                    break

            # Вопрос со свободным ответом
            if not options:
                correct_answers = []
                while i < len(lines) and lines[i].strip():
                    ans_line = lines[i].strip()
                    # Если дошли до следующего вопроса — завершаем текущий freeform.
                    if re.match(r"^\d+(?:\.\d+)*\.\s+", ans_line):
                        break

                    if QuizParser.OPTION_RE.match(ans_line):
                        break

                    if ',' in ans_line:
                        parts = [part.strip().lower() for part in ans_line.split(',') if part.strip()]
                        correct_answers.extend(parts)
                    else:
                        correct_answers.append(ans_line.lower())
                    i += 1

                while i < len(lines) and not lines[i].strip():
                    i += 1

                if correct_answers:
                    questions.append(Question(
                        text=question_text,
                        options=[],
                        question_type=QuestionType.FREEFORM,
                        correct_answer=correct_answers,
                        images=images,
                        source_topic=source_topic
                    ))
                continue

            # Обычный вопрос
            if i >= len(lines):
                break

            answer_line = lines[i].strip()
            i += 1

            if not QuizParser.ANSWER_CANDIDATE_RE.match(answer_line.upper()):
                while i < len(lines) and not lines[i].strip():
                    i += 1
                continue

            qtype, correct = QuizParser.parse_answer_line(answer_line)
            if not qtype or not correct:
                continue

            # Проверка валидности
            option_letters = {opt[0] for opt in options}
            valid = True

            if qtype == QuestionType.SINGLE:
                valid = correct in option_letters
            elif qtype == QuestionType.MULTIPLE:
                valid = correct.issubset(option_letters)
            elif qtype == QuestionType.MATCHING:
                lefts = {p[0] for p in correct}
                valid = lefts.issubset(option_letters)

            if valid and question_text and options:
                questions.append(Question(
                    text=question_text,
                    options=options,
                    question_type=qtype,
                    correct_answer=correct,
                    images=images,
                    source_topic=source_topic
                ))

            # Пропуск пустых строк
            while i < len(lines) and not lines[i].strip():
                i += 1

        return Quiz(name=test_name, questions=questions, file_path=filepath)

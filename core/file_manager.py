import os
import sys
import shutil
from typing import Dict, List, Union, Optional
import json

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FileManager:
    """Менеджер файлов приложения"""

    def __init__(self):
        self._setup_directories()

    def _setup_directories(self):
        """Создание необходимых директорий"""
        directories = [
            self.get_user_data_dir(),
            self.get_user_tests_dir(),
            self.get_user_results_dir(),
            self.get_base_tests_dir()
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_user_data_dir(self) -> str:
        """Путь к пользовательской директории данных"""
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            base = os.path.expanduser("~/.local/share")

        return os.path.join(base, "pyquiz")

    def get_user_tests_dir(self) -> str:
        """Путь к пользовательской папке с тестами"""
        user_dir = self.get_user_data_dir()
        tests_dir = os.path.join(user_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)
        return tests_dir

    def get_user_results_dir(self) -> str:
        """Путь к папке с результатами"""
        user_dir = self.get_user_data_dir()
        results_dir = os.path.join(user_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        return results_dir

    def get_base_tests_dir(self) -> str:
        """Путь к базовой директории тестов"""
        return resource_path("tests")

    def get_base_names_file(self) -> str:
        """Путь к базовому файлу имен"""
        return resource_path("names_base.txt")

    def get_user_names_file(self) -> str:
        """Путь к пользовательскому файлу имен"""
        user_dir = self.get_user_data_dir()
        return os.path.join(user_dir, "names_user.txt")

    def find_question_files_recursive(self, include_base: bool = True) -> Dict:
        """
        Рекурсивный поиск файлов тестов

        Returns:
            Иерархическое дерево файлов
        """
        base_dir = self.get_base_tests_dir()
        user_dir = self.get_user_tests_dir()

        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(user_dir, exist_ok=True)

        def build_tree_from_paths(file_paths, root):
            """Строит дерево из списка абсолютных путей файлов"""
            tree = {}
            for full_path in file_paths:
                rel_path = os.path.relpath(full_path, root)
                parts = rel_path.split(os.sep)
                current = tree
                for part in parts[:-1]:  # все кроме последнего — папки
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                # последний — файл
                current[parts[-1]] = full_path
            return tree

        def collect_all_files(root_dir):
            """Сбор всех .txt файлов рекурсивно"""
            files = []
            for dirpath, dirnames, filenames in os.walk(root_dir):
                for f in filenames:
                    if f.endswith('.txt'):
                        files.append(os.path.join(dirpath, f))
            return files

        # Собираем файлы из обеих директорий
        base_files = collect_all_files(base_dir) if include_base and os.path.exists(base_dir) else []
        user_files = collect_all_files(user_dir)

        base_tree = build_tree_from_paths(base_files, base_dir) if base_files else {}
        user_tree = build_tree_from_paths(user_files, user_dir) if user_files else {}

        # Объединение: пользовательские файлы заменяют базовые
        def merge_trees(user, base):
            result = base.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_trees(value, result[key])
                else:
                    result[key] = value
            return result

        return merge_trees(user_tree, base_tree)

    def get_all_test_files(self, include_base: bool = True) -> List[str]:
        """Получить все файлы тестов"""
        tree = self.find_question_files_recursive(include_base=include_base)

        def collect_paths(node):
            paths = []
            for key, value in node.items():
                if isinstance(value, dict):
                    paths.extend(collect_paths(value))
                else:
                    paths.append(value)
            return paths

        return collect_paths(tree)

    def copy_to_user_tests(self, source_path: str) -> str:
        """
        Копирование файла теста в пользовательскую директорию

        Args:
            source_path: Путь к исходному файлу

        Returns:
            Путь к скопированному файлу
        """
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Файл не найден: {source_path}")

        user_tests_dir = self.get_user_tests_dir()
        filename = os.path.basename(source_path)
        dest_path = os.path.join(user_tests_dir, filename)

        # Добавляем суффикс если файл уже существует
        counter = 1
        orig_name, ext = os.path.splitext(filename)
        while os.path.exists(dest_path):
            dest_path = os.path.join(user_tests_dir, f"{orig_name}_{counter}{ext}")
            counter += 1

        shutil.copy2(source_path, dest_path)

        # Пытаемся скопировать папку images рядом с исходным тестом
        src_dir = os.path.dirname(source_path)
        src_images = os.path.join(src_dir, "images")
        if os.path.isdir(src_images):
            dest_images = os.path.join(user_tests_dir, "images")
            os.makedirs(dest_images, exist_ok=True)
            for dirpath, _dirnames, filenames in os.walk(src_images):
                rel = os.path.relpath(dirpath, src_images)
                target_dir = dest_images if rel == "." else os.path.join(dest_images, rel)
                os.makedirs(target_dir, exist_ok=True)
                for fname in filenames:
                    src_file = os.path.join(dirpath, fname)
                    dst_file = os.path.join(target_dir, fname)
                    try:
                        shutil.copy2(src_file, dst_file)
                    except Exception:
                        pass

        return dest_path

    def save_result(self, result_data: Dict, filename: Optional[str] = None) -> str:
        """
        Сохранение результата теста

        Args:
            result_data: Данные результата
            filename: Имя файла (если None, генерируется автоматически)

        Returns:
            Путь к сохраненному файлу
        """
        results_dir = self.get_user_results_dir()

        if filename is None:
            timestamp = result_data.get('timestamp', '').replace(':', '-').replace(' ', '_')
            student_name = result_data.get('student_name', 'Unknown')
            filename = f"{student_name}_{timestamp}.json"

        filepath = os.path.join(results_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        return filepath

    def load_results(self) -> List[Dict]:
        """Загрузка всех сохраненных результатов"""
        results_dir = self.get_user_results_dir()
        results = []

        if not os.path.exists(results_dir):
            return results

        for filename in os.listdir(results_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        result_data['_filepath'] = filepath
                        results.append(result_data)
                except Exception:
                    continue

        return sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)

    def load_names(self) -> tuple[List[str], List[str]]:
        """
        Загрузка имен из файлов

        Returns:
            Кортеж (базовые имена, пользовательские имена)
        """
        base_names = []
        user_names = []

        # Базовые имена
        base_file = self.get_base_names_file()
        if os.path.isfile(base_file):
            try:
                with open(base_file, "r", encoding="utf-8") as f:
                    base_names = [line.strip() for line in f if line.strip()]
            except Exception:
                pass

        # Пользовательские имена
        user_file = self.get_user_names_file()
        if os.path.isfile(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    user_names = [line.strip() for line in f if line.strip()]
            except Exception:
                pass

        # Удаление дублей
        seen = set(base_names)
        user_names = [n for n in user_names if n not in seen]

        return base_names, user_names


    def clear_user_names(self) -> None:
        """Удаление всех пользовательских имен"""
        user_file = self.get_user_names_file()
        try:
            if os.path.exists(user_file):
                os.remove(user_file)
        except Exception:
            pass

    def clear_user_tests(self) -> int:
        """Удаление всех загруженных пользователем тестов"""
        user_tests_dir = self.get_user_tests_dir()
        removed = 0
        for dirpath, _dirnames, filenames in os.walk(user_tests_dir):
            for filename in filenames:
                if filename.endswith('.txt'):
                    try:
                        os.remove(os.path.join(dirpath, filename))
                        removed += 1
                    except Exception:
                        pass
        return removed

    def save_name(self, name: str) -> None:
        """Сохранение нового имени в пользовательский файл"""
        if not name or not name.strip():
            return

        name = name.strip()
        base_names, user_names = self.load_names()

        # Проверка на существование
        all_existing = set(base_names) | set(user_names)
        if name in all_existing:
            return

        # Сохранение
        user_file = self.get_user_names_file()
        try:
            with open(user_file, "a", encoding="utf-8") as f:
                f.write(name + "\n")
        except Exception:
            pass
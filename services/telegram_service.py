import json
import os
import urllib.request
import urllib.parse
from typing import Optional, List
from core.models import TestResult

class TelegramService:
    """Сервис для отправки результатов в Telegram"""

    def __init__(self):
        self.config_path = self._get_config_path()
        self.bot_token = "1234567890:AbCdEfGi"
        self.admin_chat_ids = ["1234567890"]
        self._load_config()

    def _get_config_path(self) -> str:
        """Получение пути к конфигурационному файлу"""
        if os.name == 'nt':  # Windows
            base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        else:  # Linux/Mac
            base = os.path.expanduser('~/.config')

        config_dir = os.path.join(base, 'pyquiz')
        os.makedirs(config_dir, exist_ok=True)

        return os.path.join(config_dir, 'telegram_config.json')

    def _load_config(self):
        """Загрузка конфигурации из файла"""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.bot_token = config.get('bot_token')
            self.admin_chat_ids = config.get('admin_chat_ids', [])
        except Exception:
            pass

    def is_configured(self) -> bool:
        """Проверка наличия конфигурации"""
        return bool(self.bot_token and self.admin_chat_ids)

    def save_config(self, bot_token: str, admin_chat_ids: List[str]) -> bool:
        """Сохранение конфигурации"""
        try:
            config = {
                'bot_token': bot_token,
                'admin_chat_ids': admin_chat_ids
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            self.bot_token = bot_token
            self.admin_chat_ids = admin_chat_ids
            return True

        except Exception:
            return False

    def send_result(self, result: TestResult) -> bool:
        """Отправка результата в Telegram"""
        if not self.is_configured():
            return False

        try:
            message = self._format_result_message(result)

            for chat_id in self.admin_chat_ids:
                self._send_message(chat_id, message)

            return True

        except Exception:
            return False

    def _format_result_message(self, result: TestResult) -> str:
        """Форматирование сообщения с результатом"""
        passed_icon = "✅" if result.passed else "❌"
        passed_text = "СДАЛ" if result.passed else "НЕ СДАЛ"

        message = (
            f"🎓 *Новый результат теста!*\n\n"
            f"{passed_icon} *{passed_text}*\n"
            f"👤 *Студент:* {result.student_name}\n"
            f"📅 *Дата:* {result.timestamp}\n\n"
            f"📊 *Статистика:*\n"
            f"• Всего вопросов: {result.total_questions}\n"
            f"• Правильных: {result.correct_answers}\n"
            f"• Процент: {result.percentage:.1f}%\n"
            f"• Оценка (12): {result.grade_12}\n"
            f"• Оценка (5): {result.grade_5}\n"
        )

        if result.timeout:
            message += f"\n⏰ *Завершено по таймауту!*"

        if result.time_left:
            mins, secs = result.time_left
            message += f"\n⏱️ Осталось времени: {mins:02d}:{secs:02d}"

        return message

    def _send_message(self, chat_id: str, text: str) -> None:
        """Отправка сообщения через Telegram API"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
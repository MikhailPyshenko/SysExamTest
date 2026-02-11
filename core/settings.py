import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Union

from core.file_manager import FileManager


TimerValue = Union[str, int, float]
GradeMode = Union[str, List[str]]


@dataclass
class AppSettings:
    TIMER: TimerValue = "A(1.1)"
    SHOW_TIMER: bool = True
    MAX_QUESTIONS: int = 60
    SHOW_STATS_BUTTON: bool = True
    DISABLE_MINIMIZE_AND_FOCUS_LOSS: bool = False
    NAME_RESTRICT_TO_LIST: bool = False
    GRADE_MODE: GradeMode = "all"
    PASS_THRESHOLD: float = 65.0
    AUTO_NEXT: bool = False

    TELEGRAM_SEND_ON_RESULT: bool = False
    TELEGRAM_SEND_ON_SAVE: bool = False

    DEFAULT_SAVE_DIR: Optional[str] = None
    THEME: str = "system"  # dark/light/system
    HIDE_BUILTIN_TESTS: bool = False


class SettingsManager:
    def __init__(self):
        self.file_manager = FileManager()
        self.path = os.path.join(self.file_manager.get_user_data_dir(), "settings.json")

    def load(self) -> AppSettings:
        defaults = AppSettings()
        if not os.path.isfile(self.path):
            self.save(defaults)
            return defaults

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return defaults

        normalized = self._normalize(raw, defaults)
        settings = AppSettings(**normalized)
        self.save(settings)
        return settings

    def save(self, settings: AppSettings) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)

    def _normalize(self, raw: Dict[str, Any], defaults: AppSettings) -> Dict[str, Any]:
        result = asdict(defaults)

        for key in result.keys():
            if key not in raw:
                continue
            result[key] = raw[key]

        result["SHOW_TIMER"] = bool(result["SHOW_TIMER"])
        result["SHOW_STATS_BUTTON"] = bool(result["SHOW_STATS_BUTTON"])
        result["DISABLE_MINIMIZE_AND_FOCUS_LOSS"] = bool(result["DISABLE_MINIMIZE_AND_FOCUS_LOSS"])
        result["NAME_RESTRICT_TO_LIST"] = bool(result["NAME_RESTRICT_TO_LIST"])
        result["AUTO_NEXT"] = bool(result["AUTO_NEXT"])
        result["TELEGRAM_SEND_ON_RESULT"] = bool(result["TELEGRAM_SEND_ON_RESULT"])
        result["TELEGRAM_SEND_ON_SAVE"] = bool(result["TELEGRAM_SEND_ON_SAVE"])
        result["HIDE_BUILTIN_TESTS"] = bool(result.get("HIDE_BUILTIN_TESTS", defaults.HIDE_BUILTIN_TESTS))

        try:
            result["MAX_QUESTIONS"] = max(0, int(result["MAX_QUESTIONS"]))
        except Exception:
            result["MAX_QUESTIONS"] = defaults.MAX_QUESTIONS

        try:
            result["PASS_THRESHOLD"] = max(0.0, min(100.0, float(result["PASS_THRESHOLD"])))
        except Exception:
            result["PASS_THRESHOLD"] = defaults.PASS_THRESHOLD

        if not self._is_valid_timer(result["TIMER"]):
            result["TIMER"] = defaults.TIMER

        if isinstance(result["GRADE_MODE"], str):
            if result["GRADE_MODE"] not in {"all", "%", "12", "5"}:
                result["GRADE_MODE"] = defaults.GRADE_MODE
        elif isinstance(result["GRADE_MODE"], list):
            allowed = {"%", "12", "5"}
            result["GRADE_MODE"] = [x for x in result["GRADE_MODE"] if x in allowed]
            if not result["GRADE_MODE"]:
                result["GRADE_MODE"] = defaults.GRADE_MODE
        else:
            result["GRADE_MODE"] = defaults.GRADE_MODE

        if result["DEFAULT_SAVE_DIR"] not in (None, "auto"):
            if not isinstance(result["DEFAULT_SAVE_DIR"], str):
                result["DEFAULT_SAVE_DIR"] = None

        if result["THEME"] not in {"dark", "light", "system"}:
            result["THEME"] = defaults.THEME

        return result

    @staticmethod
    def _is_valid_timer(value: Any) -> bool:
        if isinstance(value, (int, float)):
            return True
        if not isinstance(value, str):
            return False
        if value.upper() == "A":
            return True
        return bool(re.fullmatch(r"A\(\d+(?:\.\d+)?\)", value.upper()))


def resolve_time_limit_seconds(timer_value: TimerValue, question_count: int) -> int:
    """Возвращает лимит времени в секундах. 0 = без лимита."""
    if isinstance(timer_value, (int, float)):
        minutes = float(timer_value)
        return max(0, int(minutes * 60))

    if not isinstance(timer_value, str):
        return 0

    raw = timer_value.strip().upper()
    if raw == "A":
        return int(question_count * 60)

    match = re.fullmatch(r"A\((\d+(?:\.\d+)?)\)", raw)
    if match:
        per_question = float(match.group(1))
        return int(question_count * per_question * 60)

    return 0

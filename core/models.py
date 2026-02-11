from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional, Dict, Any
from enum import Enum

class QuestionType(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    MATCHING = "matching"
    FREEFORM = "freeform"

@dataclass
class Question:
    text: str
    options: List[str]
    question_type: QuestionType
    correct_answer: Any  # Может быть str, set, list кортежей, или list строк
    images: List[Tuple[str, str]] = field(default_factory=list)  # (описание, путь)
    source_topic: str = ""

@dataclass
class Quiz:
    name: str
    questions: List[Question]
    file_path: Optional[str] = None

@dataclass
class TestResult:
    student_name: str
    quiz_name: str
    total_questions: int
    correct_answers: int
    percentage: float
    grade_12: int
    grade_5: int
    passed: bool
    timestamp: str
    time_left: Optional[Tuple[int, int]] = None
    timeout: bool = False
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)
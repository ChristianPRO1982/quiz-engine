import json
import secrets
import string
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.db.models import Quiz


PHASE_LOBBY = "LOBBY"
PHASE_QUESTION = "QUESTION"
PHASE_REVEAL = "REVEAL"
PHASE_TRANSITION = "TRANSITION"
PHASE_ENDED = "ENDED"


def generate_session_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


@dataclass
class LiveQuestion:
    id: int
    index: int
    kind: str
    prompt: str
    media: Optional[str]
    choices: List[dict]
    config: dict


@dataclass
class LiveSessionState:
    session_id: int
    session_code: str
    quiz_id: int
    questions: List[LiveQuestion]
    phase: str = PHASE_LOBBY
    current_question_index: int = -1
    locked: bool = False
    players_count: int = 0
    answers_by_question: Dict[int, Dict[int, int]] = field(default_factory=dict)

    def current_question(self) -> Optional[LiveQuestion]:
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None


def quiz_to_live_questions(quiz: Quiz) -> List[LiveQuestion]:
    questions = []
    for index, question in enumerate(sorted(quiz.questions, key=lambda q: q.position)):
        config = json.loads(question.config_json or "{}")
        choices = [
            {"id": choice.id, "label": choice.label}
            for choice in sorted(question.choices, key=lambda c: c.position)
        ]
        questions.append(
            LiveQuestion(
                id=question.id,
                index=index,
                kind=question.kind,
                prompt=question.prompt,
                media=question.media_url,
                choices=choices,
                config=config,
            )
        )
    return questions

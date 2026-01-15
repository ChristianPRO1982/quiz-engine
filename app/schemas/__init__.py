from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChoiceCreate(BaseModel):
    position: int
    label: str


class QuestionCreate(BaseModel):
    position: int
    kind: str = Field(default="MULTIPLE_CHOICE")
    prompt: str
    media_url: Optional[str] = None
    config: dict = Field(default_factory=dict)
    choices: List[ChoiceCreate] = Field(default_factory=list)


class QuizCreate(BaseModel):
    title: str
    questions: List[QuestionCreate] = Field(default_factory=list)


class ChoiceOut(BaseModel):
    id: int
    position: int
    label: str

    model_config = ConfigDict(from_attributes=True)


class QuestionOut(BaseModel):
    id: int
    position: int
    kind: str
    prompt: str
    media_url: Optional[str]
    config: dict
    choices: List[ChoiceOut]

    model_config = ConfigDict(from_attributes=True)


class QuizOut(BaseModel):
    id: int
    title: str
    questions: List[QuestionOut]

    model_config = ConfigDict(from_attributes=True)


class SessionStartRequest(BaseModel):
    quiz_id: int


class SessionStartResponse(BaseModel):
    session_code: str
    host_token: str
    join_url: str


class SessionJoinRequest(BaseModel):
    nickname: str


class SessionJoinResponse(BaseModel):
    player_id: int


class SessionReviewAnswer(BaseModel):
    question_id: int
    total_answers: int
    by_choice: List[dict]


class SessionReviewResponse(BaseModel):
    session_code: str
    quiz: QuizOut
    players_count: int
    answers: List[SessionReviewAnswer]

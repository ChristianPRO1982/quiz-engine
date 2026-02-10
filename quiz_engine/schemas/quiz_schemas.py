"""Pydantic schemas for quiz APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizQuestionIn(BaseModel):
    type: Literal["qcm_single"]
    text: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2)


class QuizCreateRequest(BaseModel):
    schema_version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    questions: list[QuizQuestionIn]

    @model_validator(mode="after")
    def _validate_choices(self) -> QuizCreateRequest:
        for question in self.questions:
            cleaned = [choice.strip() for choice in question.choices]
            if any(not choice for choice in cleaned):
                raise ValueError("Question choices cannot be empty")
        return self


class QuizSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schema_version: str
    title: str
    description: str | None = None


class QuizDetailResponse(QuizSummaryResponse):
    questions: list[QuizQuestionIn]

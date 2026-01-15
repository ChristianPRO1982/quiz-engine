import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Choice, Question, Quiz
from app.db.session import get_db
from app.schemas import QuizCreate, QuizOut


router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizOut)
def create_quiz(payload: QuizCreate, db: Session = Depends(get_db)):
    quiz = Quiz(title=payload.title)
    db.add(quiz)
    db.flush()

    for question_payload in payload.questions:
        question = Question(
            quiz_id=quiz.id,
            position=question_payload.position,
            kind=question_payload.kind,
            prompt=question_payload.prompt,
            media_url=question_payload.media_url,
            config_json=json.dumps(question_payload.config or {}),
        )
        db.add(question)
        db.flush()

        for choice_payload in question_payload.choices:
            choice = Choice(
                question_id=question.id,
                position=choice_payload.position,
                label=choice_payload.label,
            )
            db.add(choice)

    db.commit()
    db.refresh(quiz)
    return QuizOut.model_validate(quiz, from_attributes=True)


@router.get("", response_model=list[QuizOut])
def list_quizzes(db: Session = Depends(get_db)):
    quizzes = db.query(Quiz).all()
    return [QuizOut.model_validate(quiz, from_attributes=True) for quiz in quizzes]


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="QUIZ_NOT_FOUND")
    return QuizOut.model_validate(quiz, from_attributes=True)

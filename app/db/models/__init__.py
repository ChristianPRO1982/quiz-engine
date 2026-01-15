import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func


Base = declarative_base()


class Quiz(Base):
    __tablename__ = "quiz"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"), nullable=False)
    position = Column(Integer, nullable=False)
    kind = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    media_url = Column(String(255), nullable=True)
    config_json = Column(Text, nullable=False, default="{}")

    quiz = relationship("Quiz", back_populates="questions")
    choices = relationship("Choice", back_populates="question", cascade="all, delete-orphan")

    @property
    def config(self) -> dict:
        return json.loads(self.config_json or "{}")


class Choice(Base):
    __tablename__ = "choice"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    position = Column(Integer, nullable=False)
    label = Column(String(255), nullable=False)

    question = relationship("Question", back_populates="choices")


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"), nullable=False)
    session_code = Column(String(6), unique=True, nullable=False, index=True)
    host_token_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="LOBBY")
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)

    quiz = relationship("Quiz")
    players = relationship("Player", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    nickname = Column(String(50), nullable=False)
    joined_at = Column(DateTime, server_default=func.now())

    session = relationship("Session", back_populates="players")
    answers = relationship("Answer", back_populates="player", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answer"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("player.id"), nullable=False)
    submitted_at = Column(DateTime, server_default=func.now())
    choice_id = Column(Integer, ForeignKey("choice.id"), nullable=True)
    value_text = Column(Text, nullable=True)
    value_number = Column(Integer, nullable=True)

    session = relationship("Session", back_populates="answers")
    player = relationship("Player", back_populates="answers")

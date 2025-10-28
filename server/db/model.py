# server/db/models.py
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./drowni.db")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AudioEvent(Base):
    __tablename__ = "audio_events"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False)
    prob_help = Column(Float, nullable=False)
    accepted = Column(Boolean, nullable=False, default=False)
    ts = Column(DateTime, nullable=False)
    battery = Column(Float, nullable=True)
    features = Column(Text, nullable=True)  # JSON 문자열
    meta = Column(Text, nullable=True)      # JSON 문자열
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    ts = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


def init_db():
    """마이그레이션 SQL을 대체하는 최소 초기화 (테이블 생성)"""
    Base.metadata.create_all(bind=engine)

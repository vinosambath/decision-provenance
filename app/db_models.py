from __future__ import annotations

from datetime import date as Date
from datetime import datetime

from sqlalchemy import Boolean, Computed, Date as DateColumn, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class Corpus(Base):
    __tablename__ = "corpora"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    meetings: Mapped[list["Meeting"]] = relationship(back_populates="corpus", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (UniqueConstraint("corpus_id", "external_id", name="uq_meetings_corpus_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    corpus_id: Mapped[int] = mapped_column(ForeignKey("corpora.id", ondelete="CASCADE"))
    # Filename stem (e.g. "2025-03-19_kafka-event-backbone-decision") — unique
    # within a corpus, not globally, hence the surrogate `id` above.
    external_id: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    date: Mapped[Date | None] = mapped_column(DateColumn, nullable=True)
    participants: Mapped[list[str]] = mapped_column(ARRAY(String))
    line_count: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    corpus: Mapped[Corpus] = relationship(back_populates="meetings")
    segments: Mapped[list["Segment"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = (Index("ix_segments_search_vector", "search_vector", postgresql_using="gin"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    decision_density: Mapped[float] = mapped_column(Float)
    has_alternatives: Mapped[bool] = mapped_column(Boolean)
    has_objection: Mapped[bool] = mapped_column(Boolean)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)
    )

    meeting: Mapped[Meeting] = relationship(back_populates="segments")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String)
    corpus_id: Mapped[int] = mapped_column(ForeignKey("corpora.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="queued")
    progress: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

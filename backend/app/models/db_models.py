import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, unique=True, index=True)

    basics = Column(JSON, nullable=False)
    skills = Column(JSON, nullable=False, default=list)
    experience = Column(JSON, nullable=False, default=list)
    education = Column(JSON, nullable=False, default=list)
    projects = Column(JSON, nullable=False, default=list)
    raw_text = Column(Text, nullable=False)

    verification_flags = Column(JSON, nullable=False, default=list)
    flagged_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
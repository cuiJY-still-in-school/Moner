from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .base import Base

class RelationshipStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"

class RelationshipType(enum.Enum):
    FRIEND = "FRIEND"
    COLLEAGUE = "COLLEAGUE"
    MENTOR = "MENTOR"
    MENTEE = "MENTEE"
    OTHER = "OTHER"

class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RelationshipStatus), default=RelationshipStatus.PENDING)
    relationship_type = Column(Enum(RelationshipType), default=RelationshipType.FRIEND)
    notes = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="sent_relationships"
    )
    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="received_relationships"
    )
    
    def __repr__(self):
        return f"<Relationship(from={self.from_user_id}, to={self.to_user_id}, status={self.status})>"
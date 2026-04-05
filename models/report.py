from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="unread")  # unread, read, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="sent_reports"
    )
    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="received_reports"
    )
    
    def __repr__(self):
        return f"<Report(from={self.from_user_id}, to={self.to_user_id}, title={self.title})>"
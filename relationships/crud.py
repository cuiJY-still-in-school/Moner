from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import or_, and_

from models.relationship import Relationship, RelationshipStatus
from models.report import Report
from relationships.schemas import RelationshipCreate, RelationshipUpdate, ReportCreate, ReportUpdate

# 关系 CRUD

def create_relationship(db: Session, from_user_id: int, relationship: RelationshipCreate) -> Optional[Relationship]:
    # 检查是否已存在关系
    existing = db.query(Relationship).filter(
        and_(
            Relationship.from_user_id == from_user_id,
            Relationship.to_user_id == relationship.to_user_id
        )
    ).first()
    
    if existing:
        return None
    
    db_relationship = Relationship(
        from_user_id=from_user_id,
        to_user_id=relationship.to_user_id,
        relationship_type=relationship.relationship_type,
        notes=relationship.notes,
        status=RelationshipStatus.PENDING
    )
    
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

def get_relationship(db: Session, relationship_id: int) -> Optional[Relationship]:
    return db.query(Relationship).filter(Relationship.id == relationship_id).first()

def get_relationships_by_user(db: Session, user_id: int, status: Optional[str] = None) -> List[Relationship]:
    query = db.query(Relationship).filter(
        or_(
            Relationship.from_user_id == user_id,
            Relationship.to_user_id == user_id
        )
    )
    
    if status:
        query = query.filter(Relationship.status == status)
    
    return query.all()

def get_pending_requests_to_user(db: Session, user_id: int) -> List[Relationship]:
    return db.query(Relationship).filter(
        and_(
            Relationship.to_user_id == user_id,
            Relationship.status == RelationshipStatus.PENDING
        )
    ).all()

def update_relationship_status(db: Session, relationship_id: int, status: RelationshipStatus) -> Optional[Relationship]:
    db_relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not db_relationship:
        return None
    
    db_relationship.status = status
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

def delete_relationship(db: Session, relationship_id: int) -> bool:
    db_relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not db_relationship:
        return False
    
    db.delete(db_relationship)
    db.commit()
    return True

# 汇报 CRUD

def create_report(db: Session, from_user_id: int, report: ReportCreate) -> Optional[Report]:
    db_report = Report(
        from_user_id=from_user_id,
        to_user_id=report.to_user_id,
        title=report.title,
        content=report.content,
        status="unread"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).first()

def get_reports_by_user(db: Session, user_id: int, direction: str = "received") -> List[Report]:
    if direction == "sent":
        return db.query(Report).filter(Report.from_user_id == user_id).all()
    else:  # received
        return db.query(Report).filter(Report.to_user_id == user_id).all()

def update_report_status(db: Session, report_id: int, status: str) -> Optional[Report]:
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None
    
    db_report.status = status
    db.commit()
    db.refresh(db_report)
    return db_report

def update_report(db: Session, report_id: int, report_update: ReportUpdate) -> Optional[Report]:
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None
    
    # 更新字段
    if report_update.title is not None:
        db_report.title = report_update.title
    if report_update.content is not None:
        db_report.content = report_update.content
    if report_update.status is not None:
        db_report.status = report_update.status
    
    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: int) -> bool:
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return False
    
    db.delete(db_report)
    db.commit()
    return True
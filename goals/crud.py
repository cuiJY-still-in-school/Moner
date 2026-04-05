from sqlalchemy.orm import Session
from typing import List, Optional

from models.goal import Goal, GoalStatus
from goals.schemas import GoalCreate, GoalUpdate

def create_goal(db: Session, user_id: int, goal: GoalCreate) -> Goal:
    db_goal = Goal(
        user_id=user_id,
        title=goal.title,
        description=goal.description,
        status=goal.status,
        progress=goal.progress,
        priority=goal.priority,
        deadline=goal.deadline
    )
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_goal(db: Session, goal_id: int) -> Optional[Goal]:
    return db.query(Goal).filter(Goal.id == goal_id).first()

def get_goals_by_user(db: Session, user_id: int, status: Optional[str] = None) -> List[Goal]:
    query = db.query(Goal).filter(Goal.user_id == user_id)
    if status:
        query = query.filter(Goal.status == status)
    return query.order_by(Goal.priority, Goal.created_at).all()

def update_goal(db: Session, goal_id: int, goal_update: GoalUpdate) -> Optional[Goal]:
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        return None
    
    update_data = goal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_goal, field, value)
    
    db.commit()
    db.refresh(db_goal)
    return db_goal

def delete_goal(db: Session, goal_id: int) -> bool:
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        return False
    
    db.delete(db_goal)
    db.commit()
    return True

def update_goal_progress(db: Session, goal_id: int, progress: float) -> Optional[Goal]:
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        return None
    
    db_goal.progress = max(0.0, min(100.0, progress))
    
    # 自动更新状态
    if db_goal.progress >= 100.0:
        db_goal.status = GoalStatus.COMPLETED
    elif db_goal.progress > 0.0:
        db_goal.status = GoalStatus.IN_PROGRESS
    
    db.commit()
    db.refresh(db_goal)
    return db_goal
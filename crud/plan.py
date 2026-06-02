from models.plan import Plan
from sqlalchemy.orm import Session
from sqlalchemy import func


def get_plans_cache_metadata(db: Session):
    return {
        "last_updated": db.query(func.max(Plan.updated_at)).scalar(),
        "count": db.query(func.count(Plan.id)).scalar()
    }


def get_all_plans(db: Session):
    return db.query(Plan).all()


def get_plan_by_id(db: Session, plan_id: int):
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_plan_by_name(db: Session, name: str):
    return db.query(Plan).filter(Plan.name == name).first()


def create_plan(db: Session, data: dict):
    plan = Plan(**data)

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


def update_plan(db: Session, plan: Plan, data: dict):
    update_data = {
        key: value
        for key, value in data.items()
        if value is not None
    }

    for key, value in update_data.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)

    return plan


def delete_plan(db: Session, plan: Plan):
    db.delete(plan)
    db.commit()

    return True
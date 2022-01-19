from sqlalchemy.orm import Session

from . import models


def get_users(db: Session):
    return db.query(models.User).all()


def get_user(db: Session, data_id: int):
    return db.query(models.User).filter(models.User.data_id == data_id).first()


def create_user(db: Session, data_id: str, name: str):
    db_user = models.User(data_id=data_id, name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_sched(db: Session, busy_start: str,
                      busy_end: str, data_id: str):
    db_sched = models.Sched(busy_start=busy_start,
                            busy_end=busy_end, owner_id=data_id)
    db.add(db_sched)
    db.commit()
    db.refresh(db_sched)
    return db_sched

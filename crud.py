from sqlalchemy.orm import Session

from . import models

def get_user(db: Session, data_id: int):
    """
    get_user: returns a user object
    """
    return db.query(models.User).filter(models.User.data_id == data_id).first()


def get_scheds(db: Session, data_id: int):
    """
    get_scheds: returns all scheds of a user
    """
    return db.query(models.Sched).filter(models.Sched.owner_id == data_id).all()


def create_user(db: Session, data_id: str, name: str):
    """
    create_user: create a user object and save it to database
    """
    db_user = models.User(data_id=data_id, name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_sched(db: Session, busy_start: str, busy_end: str, data_id: str):
    """
    create_user_sched: create a sched object and save it to database
    """
    db_sched = models.Sched(busy_start=busy_start, busy_end=busy_end, owner_id=data_id)
    db.add(db_sched)
    db.commit()
    db.refresh(db_sched)
    return db_sched

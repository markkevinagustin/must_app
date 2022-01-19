from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(String, index=True)
    name = Column(String, index=True)

    scheds = relationship("Sched", back_populates="owner")


class Sched(Base):
    __tablename__ = "scheds"

    id = Column(Integer, primary_key=True, index=True)
    busy_start = Column(String, index=True)
    busy_end = Column(String, index=True)
    owner_id = Column(String, ForeignKey("users.data_id"))

    owner = relationship("User", back_populates="scheds")

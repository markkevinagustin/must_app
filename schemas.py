from typing import List

from pydantic import BaseModel


class SchedBase(BaseModel):
    busy_start: str
    busy_end: str


class SchedCreate(SchedBase):
    pass


class Sched(SchedBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    data_id: str


class UserCreate(UserBase):
    name: str


class User(UserBase):
    id: int
    name: str
    scheds: List[Sched] = []

    class Config:
        orm_mode = True


class Meeting(BaseModel):
    user_ids: List[str] = []
    meeting_length: int
    earliest_latest: List[str] = []
    office_hours: List[str] = []
    timezone: str

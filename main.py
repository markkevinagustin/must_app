from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine
import pandas as pd
from datetime import datetime, timedelta
import pathlib
import dateutil.parser
import pytz

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/update_db/", response_model=schemas.User)
def update_db(db: Session = Depends(get_db)):
    filename = str(pathlib.Path(__file__).parent.resolve()) + '/freebusy.txt'
    df = pd.read_csv(filename, sep=';', header=None)

    names = [[k, v] for k, v in zip(df[0], df[1]) if is_time(v) is False]
    for name in names:
        crud.create_user(db=db, data_id=name[0], name=name[1])

    busy_start_and_end = [[k, v, vv] for k, v, vv in
                          zip(df[0], df[1], df[2]) if is_time(v)]
    for sched in busy_start_and_end:
        crud.create_user_sched(db=db, busy_start=sched[1],
                               busy_end=sched[2], data_id=sched[0])


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 999999,
               db: Session = Depends(get_db)):
    q = crud.get_users(db, skip=skip, limit=limit)

    return q


@app.post("/meetings/")
def meetings(
    meeting: schemas.Meeting, db: Session = Depends(get_db)
):
    user_ids = meeting.user_ids
    meeting_length = meeting.meeting_length
    earliest_latest = [client_to_utc(meeting.earliest_latest[0]),
                       client_to_utc(meeting.earliest_latest[0])]
    office_hours = meeting.office_hours

    el_map = [dt for dt in
              datetime_range(earliest_latest[0], earliest_latest[1],
                             timedelta(minutes=meeting_length))]

    users = [crud.get_user(db, user, earliest_latest) for user in user_ids]

    x = [x.scheds for x in users]


    return x


# get user
# build a table using earliest_latest using office hours as start and end for every day and using meeting length
# build a table using earliest_latest using office hours as start and end for every day and using meeting length from db
# get all users
# loop through users


# office hours is outer boundary and for getting lunch time
# earliest
# latest + meeting_length
# this will also filter out unneeded dates from db


# request
# employee_ids: [],
# meeting_length: 'in minutes',
# inner_bound: [earliest, latest], # datetime with timezone
# office hours # with timezone
# timezone = 'Asia/Manila'

# sample datatime with timezone
# 2020-10-31 12:00:00-07:00

def datetime_range(start, end, delta):
    current = start
    while current < end:
        yield current
        current += delta

def is_time(date):
    fmt = '%m/%d/%Y %I:%M:%S %p'
    try:
        return datetime.strptime(str(date), fmt)
    except ValueError:
        return False


def client_to_utc(data):
    fmt = '%m/%d/%Y %I:%M:%S %p'
    data_datetime = datetime.strptime(str(data), fmt)
    return data_datetime.astimezone(pytz.UTC)


def utc_to_client(data, timezone):
    utc_timezone = pytz.timezone('UTC')
    data_datetime = dateutil.parser.parse(data)
    parse_data_utc = utc_timezone.localize(data_datetime)
    return parse_data_utc.astimezone(pytz.timezone(timezone))

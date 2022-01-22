from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine
import pandas as pd
import pathlib
from .utils import is_time, convert_to_datetime, validate, build_requested_meeting_scheds, build_daily_scheds, build_suggested_schedules

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
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/freebusy.txt"
    df = pd.read_csv(filename, sep=";", header=None)

    names = [[k, v] for k, v in zip(df[0], df[1]) if is_time(v) is False]
    for name in names:
        crud.create_user(db=db, data_id=name[0], name=name[1])

    busy_start_and_end = [
        [k, v, vv] for k, v, vv in zip(df[0], df[1], df[2]) if is_time(v)
    ]
    for sched in busy_start_and_end:
        crud.create_user_sched(
            db=db, busy_start=sched[1], busy_end=sched[2], data_id=sched[0]
        )


@app.post("/meetings/")
def meetings(meeting: schemas.Meeting, db: Session = Depends(get_db)):
    # initialize variables
    user_ids = meeting.user_ids
    meeting_length = int(meeting.meeting_length)
    timezone = meeting.timezone
    office_hours = meeting.office_hours
    # initialize variables

    earliest_latest_datetime = [
        convert_to_datetime(meeting.earliest_latest[0], timezone),
        convert_to_datetime(meeting.earliest_latest[1], timezone),
    ]

    # validations
    valid, error = validate(earliest_latest_datetime, timezone, office_hours, meeting_length)
    if not valid:
        return error

    # requested_meeting_scheds
    requested_meeting_scheds = build_requested_meeting_scheds(earliest_latest_datetime,
                                                              office_hours,
                                                              meeting_length)
    # daily_scheds
    daily_scheds = build_daily_scheds(earliest_latest_datetime, office_hours)
    # daily_scheds

    user_id = user_ids[0]
    return build_suggested_schedules(crud, db, user_id,
                              office_hours, earliest_latest_datetime,
                              timezone, daily_scheds, requested_meeting_scheds, meeting_length)

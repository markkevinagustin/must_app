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


@app.post("/suggestion_individual/")
def suggestion_individual(meeting: schemas.Meeting, db: Session = Depends(get_db)):
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

    suggested_schedules_all_users = [
           build_suggested_schedules(crud, db, user,
              office_hours, earliest_latest_datetime,
              timezone, daily_scheds, requested_meeting_scheds, meeting_length)
           for user in user_ids]
    return suggested_schedules_all_users


@app.post("/suggestion_all/")
def suggestion_all(meeting: schemas.Meeting, db: Session = Depends(get_db)):
    individual_schedules = suggestion_individual(meeting=meeting, db=db)

    combined_schedules_unflattened = [ 
        individual_schedule['suggested_schedules']
        for individual_schedule in
        individual_schedules
    ] 

    individual_scheds  = [item
                          for sublist in combined_schedules_unflattened
                          for item in sublist
                          ]

    combined_schedules = [set([item
                          for sublist in individual_scheds 
                          for item in sublist
                          ])]

    names = {name['user_id']: name['username'] for name in individual_schedules}
    schedules = [set(combined_schedules[0]).intersection(*individual_scheds)]
    names['suggested_schedules_all_users'] = schedules

    return names

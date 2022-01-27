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


@app.get("/update_db/")
def update_db(db: Session = Depends(get_db)):
    """
    db: database connection/session
    """

    # read freebusy.txt and load it to pandas for parsing
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/freebusy.txt"
    df = pd.read_csv(filename, sep=";", header=None)

    # save data to table User if the second item in the line can't be converted to time
    names = [[k, v] for k, v in zip(df[0], df[1]) if is_time(v) is False]
    for name in names:
        crud.create_user(db=db, data_id=name[0], name=name[1])

    # save data to table Sched if the second item in the line can be converted to time
    busy_start_and_end = [
        [k, v, vv] for k, v, vv in zip(df[0], df[1], df[2]) if is_time(v)
    ]
    for sched in busy_start_and_end:
        crud.create_user_sched(
            db=db, busy_start=sched[1], busy_end=sched[2], data_id=sched[0]
        )
    return ["Database update Success"]


@app.post("/suggestion_individual/")
def suggestion_individual(meeting: schemas.Meeting, db: Session = Depends(get_db)):
    # initialize variables
    user_ids = meeting.user_ids
    meeting_length = int(meeting.meeting_length)
    timezone = meeting.timezone
    office_hours = meeting.office_hours

    # convert earliest_latest to timezone aware datetime object (UTC)
    earliest_latest_datetime = [
        convert_to_datetime(meeting.earliest_latest[0], timezone),
        convert_to_datetime(meeting.earliest_latest[1], timezone),
    ]

    # validations for making sure that the input from the client is valid
    valid, error = validate(earliest_latest_datetime, timezone, office_hours, meeting_length)
    if not valid:
        return error

    # build the requested schedules using earliest_latest_datetime office_hours and meeting_length
    requested_meeting_scheds = build_requested_meeting_scheds(earliest_latest_datetime,
                                                              office_hours,
                                                              meeting_length)
    # daily_scheds
    # build the daily schedules using earliest_latest_datetime office_hours
    daily_scheds = build_daily_scheds(earliest_latest_datetime, office_hours)

    # build the suggested_schedules by eliminating the unavailable schedules to the availabilties of the user
    suggested_schedules_all_users = [
           build_suggested_schedules(db, user,
              office_hours, earliest_latest_datetime,
              timezone, daily_scheds, requested_meeting_scheds, meeting_length)
           for user in user_ids]
    return suggested_schedules_all_users


@app.post("/suggestion_all/")
def suggestion_all(meeting: schemas.Meeting, db: Session = Depends(get_db)):
    # reuse suggestion_individual to get the available schedules for each individuals
    individual_schedules = suggestion_individual(meeting=meeting, db=db)

    # combine them if users have multiple available scheds per day
    combined_schedules_unflattened = [ 
        individual_schedule['suggested_schedules']
        for individual_schedule in
        individual_schedules
    ] 

    # flatten the list for individual scheds
    individual_scheds  = [item
                          for sublist in combined_schedules_unflattened
                          for item in sublist
                          ]

    # make a list of all the available schedules earliest - latest
    combined_schedules = [set([item
                          for sublist in individual_scheds 
                          for item in sublist
                          ])]

    # build a dictionary of user_id and username
    names = {name['user_id']: name['username'] for name in individual_schedules}

    # make schedules that is available to ALL the users
    schedules = [set(combined_schedules[0]).intersection(*individual_scheds)]
    names['suggested_schedules_all_users'] = schedules
    return names

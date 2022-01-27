from datetime import datetime, timedelta
import dateutil.parser
import pytz
from . import crud

FMT = "%m/%d/%Y %I:%M:%S %p"
RANGE = 30


def validate(data, timezone, office_hours, meeting_length):
    # earliest and latest from client
    earliest = data[0]
    latest = data[1]

    # create a datetime object to be used for checking if the earliest and latest is inside office hours
    office_start  = earliest.replace(hour=int(office_hours[0])).replace(minute=0).replace(second=0)
    office_end = latest.replace(hour=int(office_hours[1])).replace(minute=0).replace(second=0)

    # check if the input is within the bounds of office hours
    inside_left_bound = office_start.time()  <=  earliest.time()
    inside_right_bound = office_end.time() >= latest.time()

    # check if the earliest plus the meeting length is withing office hours
    earliest_plus_meeting_length = earliest + timedelta(minutes=meeting_length)
    earliest_with_allowance = earliest_plus_meeting_length <= office_end

    # check if the latest plus the meeting length is withing office hours
    latest_plus_meeting_length = latest + timedelta(minutes=meeting_length)
    latest_with_allowance = latest_plus_meeting_length <= office_end

    earliest_minute = earliest.minute
    latest_minute = latest.minute

    # make sure earliest is less than latest
    if not earliest.time() < latest.time():
        return (False, ["earliest should be less than latest"])

    # make sure earliest is within office hours
    if not inside_left_bound:
        return (False, ["earliest should be inside office_hours"])
    # make sure latest is within office hours
    if not inside_right_bound:
        return (False, ["latest should be inside office_hours"])

    # make sure earliest plus meeting length is within office hours
    if not earliest_with_allowance:
        return (False, ["earliest should be {} minutes earlier to accomodate the meeting length".format(meeting_length)])
    # make sure latest plus meeting length is within office hours
    if not latest_with_allowance:
        return (False, ["latest should be {} minutes earlier to accomodate the meeting length".format(meeting_length)])

    # make sure earliest is an increment of 30 mins
    if earliest_minute != 0 and earliest_minute != 30:
        return (False, ["earliest should be in an increment of 30 mins"])
    # make sure latest is an increment of 30 mins
    if latest_minute != 0 and latest_minute != 30:
        return (False, ["latest should be in an increment of 30 mins"])

    return (True, None)


def daterange_requested(start, end, delta, office_hours, meeting_length):
    # create a daterange generator that respects office hours
    current = start
    latest_plus_meeting_length = end + timedelta(minutes=meeting_length)
    end_plus_meeting_length = end + timedelta(minutes=meeting_length)
    while current <= end_plus_meeting_length:
        yield current
        if current.time() == latest_plus_meeting_length.time():
            current = current.replace(hour=start.hour).replace(minute=start.minute).replace(second=0) + timedelta(days=1)
        else:
            current += delta

def daterange_daily(start, end, delta, office_hours):
    # create a daterange generator that respects office hours DAILY
    current = start.replace(hour=int(office_hours[0])).replace(minute=0).replace(second=0)
    current_end = end.replace(hour=int(office_hours[1])).replace(minute=0).replace(second=0)
    while current <= current_end:
        yield current
        if current.time() == current_end.time():
            current = current.replace(hour=int(office_hours[0])).replace(minute=0).replace(second=0) + timedelta(days=1)
        else:
            current += delta

def busy_days_db(data, earliest_latest, timezone):
    # get busy datetime from db with respect to timezones
    busy_start_datetime = datetime.strptime(str(data.busy_start), FMT)
    busy_start = pytz.timezone("UTC").localize(busy_start_datetime)
    earliest = earliest_latest[0]
    latest = earliest_latest[1]
    return data if earliest.date() == busy_start.date() or latest.date() == busy_start.date() else None


def build_unavailable_scheds(schedules_db, office_hours, earliest_latest_datetime, timezone):
    # build unavailable_scheds and make sure it is converted from UTC to localtime(client)
    unavailable_scheds = [busy_days_db(sched, earliest_latest_datetime, timezone) for sched in schedules_db[0]]
    unavailable_scheds_clean = [clean for clean in unavailable_scheds if clean]
    unavailable_scheds_list_unflattened = []
    for unavailable_sched in unavailable_scheds_clean:
        busy_start = utc_to_client(unavailable_sched.busy_start, timezone)
        busy_end =   utc_to_client(unavailable_sched.busy_end, timezone)
        unavailable_scheds_list_unflattened.append([
            dt.strftime(FMT)
            for dt in datetime_range(
                busy_start,
                busy_end,
                timedelta(minutes=RANGE),
                office_hours
            )])

    return [item for sublist in unavailable_scheds_list_unflattened for item in sublist]
 

def build_daily_scheds(earliest_latest_datetime, office_hours):
    # build daily cheds
    daily_start = earliest_latest_datetime[0]
    daily_end = earliest_latest_datetime[1]
    return [
        dt.strftime(FMT)
        for dt in daterange_daily(
            daily_start,
            daily_end,
            timedelta(minutes=RANGE),
            office_hours
        )
    ]

def build_requested_meeting_scheds(earliest_latest_datetime, office_hours, meeting_length):
    # build requested_meeting_scheds
    requested_start = earliest_latest_datetime[0]
    requested_end = earliest_latest_datetime[1]
    return [
        dt.strftime(FMT)
        for dt in daterange_requested(
            requested_start,
            requested_end,
            timedelta(minutes=RANGE),
            office_hours,
            meeting_length
        )
    ]

def datetime_range(start, end, delta, office_hours):
    # datetime range generator
    current = start
    while current <= end:
        yield current
        current += delta

def convert_to_datetime(data, timezone):
    # parse string into timezone aware datetime object
    data_datetime = datetime.strptime(str(data), FMT)
    return pytz.timezone(timezone).localize(data_datetime)

def is_time(date):
    # check if a string can be converted to datetime object
    try:
        return datetime.strptime(str(date), FMT)
    except ValueError:
        return False
        return False


def client_to_utc(data):
    # parse string into timezone(UTC) aware datetime object
    data_datetime = datetime.strptime(str(data), FMT)
    return data_datetime.astimezone(pytz.UTC)


def utc_to_client(data, timezone):
    # parse string into timezone(client localtime) aware datetime object
    data_datetime = dateutil.parser.parse(data)
    parse_data_utc = pytz.timezone("UTC").localize(data_datetime)
    return parse_data_utc.astimezone(pytz.timezone(timezone))


def suggest_sched(data, meeting_length): 
    # suggest scheds based on meeting length
    length = int(meeting_length) // int(30)
    suggested_schedules = []
    for item in data:
        minutes = 0
        for i in range(length):
            minutes += 30
            item_datetime_plus_meeting_length = datetime.strptime(item, FMT) + timedelta(minutes=minutes)
            if item_datetime_plus_meeting_length.strftime(FMT) in data:
                if minutes == meeting_length:
                    suggested_schedules.append(str(item) + " - " + item_datetime_plus_meeting_length.strftime(FMT))
            elif item_datetime_plus_meeting_length.strftime(FMT) not in data:
                break
    return suggested_schedules



def build_suggested_schedules(db, user_id,
                              office_hours, earliest_latest_datetime,
                              timezone, daily_scheds, requested_meeting_scheds, meeting_length):
    # get user from db
    user = crud.get_user(db, data_id=user_id)

    # get schedules
    schedules_db = [crud.get_scheds(db, user_id)]
    # build unavailable_scheds
    unavailable_scheds = build_unavailable_scheds(schedules_db, office_hours, earliest_latest_datetime, timezone)

    # build suggested_scheds by removing unavailable scheds
    remaining_scheds = [sched for sched in daily_scheds if sched not in unavailable_scheds]
    possible_scheds  = [sched_ for sched_ in requested_meeting_scheds if sched_ in remaining_scheds]
    suggested_scheds = suggest_sched(possible_scheds, meeting_length)

    #PRINT THIS FOR DEBUGGING PURPOSES ONLY
    #(["requested_meeting_scheds", requested_meeting_scheds],
    #        ["daily_scheds", daily_scheds],
    #        ["unavailable_scheds", unavailable_scheds],
    #        ["daily_scheds - unavailable_scheds", remaining_scheds],
    #        ["possible_scheds", possible_scheds],
    #        ["suggested_scheds", suggested_scheds],
    #        ["user_name", {"username": user.name,
    #                       "user_id": user_id,
    #                       "suggested_schedules": [suggested_scheds]
    #                       }],
    #        )

    return {"username": user.name,
                           "user_id": user_id,
                           "suggested_schedules": [suggested_scheds]
                           }

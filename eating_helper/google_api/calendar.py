from typing import List

from beautiful_date import D, hours
from gcsa.calendar import AccessRoles
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from pydantic import BaseModel

from ..secrets import GOOGLE_API_CREDENTIALS_FILE_PATH, GOOGLE_MEAL_PLAN_CALENDAR_NAME


class Calendar(BaseModel):
    id: str = ""
    name: str = ""


def test():
    print(list(get_meal_plan_events()))


def create_meal_plan_events():
    start = D.today()[12:00]
    end = start + 1 * hours
    event = Event("Meeting", start=start, end=end)


def get_meal_plan_events() -> List[Event]:
    gc = GoogleCalendar(credentials_path=GOOGLE_API_CREDENTIALS_FILE_PATH)
    cal = get_meal_plan_calendar(gc)
    events = gc.get_events(calendar_id=cal.id)
    return events


def get_meal_plan_calendar(gc: GoogleCalendar) -> Calendar:
    calendar = get_calendar_by_name(gc, GOOGLE_MEAL_PLAN_CALENDAR_NAME)
    if not calendar:
        raise Exception(f"Calendar {GOOGLE_MEAL_PLAN_CALENDAR_NAME} not found.")
    return calendar


def get_calendar_by_name(gc: GoogleCalendar, name: str) -> Calendar | None:
    calendars = gc.get_calendar_list(min_access_role=AccessRoles.READER)
    for calendar in calendars:
        if calendar.summary == name:
            return Calendar(id=calendar.calendar_id, name=calendar.summary)
    return None

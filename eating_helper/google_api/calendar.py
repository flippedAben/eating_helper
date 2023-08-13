import logging
from functools import cache
from typing import List

from beautiful_date import BeautifulDate, hours
from gcsa.calendar import AccessRoles
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from pydantic import BaseModel

from ..secrets import GOOGLE_API_CREDENTIALS_FILE_PATH, GOOGLE_MEAL_PLAN_CALENDAR_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Calendar(BaseModel):
    id: str = ""
    name: str = ""


def test():
    print(list(get_meal_plan_events()))


def get_calendar_service() -> GoogleCalendar:
    return GoogleCalendar(credentials_path=GOOGLE_API_CREDENTIALS_FILE_PATH)


def add_event_to_meal_plan_calendar(
    gc: GoogleCalendar, name: str, meal_time: BeautifulDate
):
    event = Event(
        name,
        start=meal_time,
        end=meal_time + 1 * hours,
    )
    calendar = get_meal_plan_calendar(gc)
    gc.add_event(
        event,
        calendar_id=calendar.id,
    )


def get_meal_plan_events() -> List[Event]:
    gc = get_calendar_service()
    cal = get_meal_plan_calendar(gc)
    events = gc.get_events(calendar_id=cal.id)
    return events


def get_meal_plan_calendar(gc: GoogleCalendar) -> Calendar:
    calendar = get_calendar_by_name(gc, GOOGLE_MEAL_PLAN_CALENDAR_NAME)
    if not calendar:
        raise Exception(f"Calendar {GOOGLE_MEAL_PLAN_CALENDAR_NAME} not found.")
    return calendar


@cache
def get_calendar_by_name(gc: GoogleCalendar, name: str) -> Calendar | None:
    logger.info("Hit Google API: get_calendar_list")
    calendars = gc.get_calendar_list(min_access_role=AccessRoles.READER)
    for calendar in calendars:
        if calendar.summary == name:
            return Calendar(id=calendar.calendar_id, name=calendar.summary)
    return None

from collections import defaultdict
from datetime import datetime
from threading import Event
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

import objc
from EventKit import EKEntityTypeReminder
from EventKit import EKEventStore
from Foundation import NSCalendar
from Foundation import NSDate


class Reminder(NamedTuple):
    title: str
    due_date: Optional[datetime]
    notes: Optional[str]
    completed: bool
    url: Optional[str]


class RemindersAPI:
    def __init__(self):
        self.event_store = self._grant_permission()

    def _grant_permission(self) -> EKEventStore:
        event_store = EKEventStore.alloc().init()
        done = Event()
        result = {}

        def completion_handler(granted: bool, error: objc.objc_object) -> None:
            result["granted"] = granted
            result["error"] = error
            done.set()

        event_store.requestFullAccessToRemindersWithCompletion_(completion_handler)
        done.wait(timeout=60)
        if not result.get("granted"):
            raise PermissionError("No access to reminder")

        return event_store

    def _convert_reminder(self, reminder) -> Reminder:
        # Convert NSDate to datetime if exists
        due_date = None
        if reminder.dueDateComponents():
            ns_date = reminder.dueDateComponents().date()
            if ns_date:
                due_date = datetime.fromtimestamp(ns_date.timeIntervalSince1970())

        return Reminder(
            title=reminder.title(),
            due_date=due_date,
            notes=reminder.notes(),
            completed=reminder.isCompleted(),
            url=reminder.URL(),
        )

    def get_all_calendars(self):
        """Get list of all reminder calendar names"""
        calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
        return [calendar.title() for calendar in calendars]

    def get_incomplete_reminders(
        self, calendar_names: Optional[List[str]] = None
    ) -> Dict[str, List[Reminder]]:
        """
        Fetch incomplete reminders grouped by calendar

        Args:
            calendar_names: Optional list of calendar names to filter by. If None, fetches from all calendars.

        Returns:
            Dict with calendar names as keys and lists of Reminder objects as values
        """
        # Get all calendars or filter by provided names
        all_calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
        if calendar_names:
            calendars = [cal for cal in all_calendars if cal.title() in calendar_names]
        else:
            calendars = all_calendars

        # Get end of today
        calendar = NSCalendar.currentCalendar()
        now = NSDate.date()
        end_date = calendar.dateBySettingHour_minute_second_ofDate_options_(
            23, 59, 59, now, 0
        )

        reminders_by_calendar = defaultdict(list)
        fetch_done = Event()

        def fetch_completion(reminders):
            if reminders:
                for reminder in reminders:
                    calendar_title = reminder.calendar().title()
                    reminders_by_calendar[calendar_title].append(
                        self._convert_reminder(reminder)
                    )
            fetch_done.set()

        # Get predicate for incomplete reminders
        predicate = self.event_store.predicateForIncompleteRemindersWithDueDateStarting_ending_calendars_(
            None,  # Starting date as None to include all past reminders
            end_date,  # End date as end of today
            calendars,
        )

        # Fetch reminders
        self.event_store.fetchRemindersMatchingPredicate_completion_(
            predicate, fetch_completion
        )
        fetch_done.wait(timeout=60)

        return dict(reminders_by_calendar)


# Usage example:
def print_reminders(reminders_dict: Dict[str, List[Reminder]]):
    for calendar_name, reminders in reminders_dict.items():
        print(f"\n=== {calendar_name} Calendar ===")
        for reminder in reminders:
            print(f"Title: {reminder.title}")
            if reminder.due_date:
                print(f"Due Date: {reminder.due_date}")
            if reminder.notes:
                print(f"Notes: {reminder.notes}")
            if reminder.url:
                print(f"URL: {reminder.url}")
            print("---")


if __name__ == "__main__":
    # Create API instance
    api = RemindersAPI()

    # Get all calendar names
    calendars = api.get_all_calendars()
    print("Available calendars:", calendars)

    # Get all incomplete reminders
    all_reminders = api.get_incomplete_reminders()
    print_reminders(all_reminders)

    # Get reminders only from specific calendars
    # bookmarks_reminders = api.get_incomplete_reminders(["Bookmarks"])
    # print_reminders(bookmarks_reminders)

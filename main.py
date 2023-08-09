from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from decouple import config
import json
import pandas as pd
import os.path
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError


class Shift:
    def __init__(
        self,
        shift_id,
        day,
        date,
        time_start,
        time_end,
        location,
        unformatted_start,
        unformatted_end,
    ):
        self.shift_id = shift_id
        self.day = day
        self.date = date
        self.time_start = time_start
        self.time_end = time_end
        self.location = location
        self.unformatted_start = unformatted_start
        self.unformatted_end = unformatted_end

    def get_start_time(self):
        return self.unformatted_start

    def get_end_time(self):
        return self.unformatted_end

    def get_location(self):
        return self.location

    def get_id(self):
        return self.shift_id

    def __str__(self):
        return self.shift_id


class Roster:
    def __init__(self):
        self.shifts = []

        # Google Calendar Service
        SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "google_calendar_credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)
        self.calendar_id = "882faf51384ae373f5cf26226ebd11d99300c3a3f320e2fe7507f5dcc26cce83@group.calendar.google.com"
        self.timezone = "Australia/Sydney"

        self.google_shifts = []

    def add_shift(self, shift):
        self.shifts.append(shift)

    def get_shifts(self):
        return self.shifts

    def add_shift_to_google_calendar(self, shift):
        try:
            event = {
                "summary": "Work",
                "start": {
                    "dateTime": shift.get_start_time(),
                    "timeZone": self.timezone,
                },
                "end": {"dateTime": shift.get_end_time(), "timeZone": self.timezone},
                "location": shift.get_location(),
                "description": shift.get_id(),
            }

            # Create event
            event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event)
                .execute()
            )
            print("Event created:", event.get("htmlLink"))
        except HttpError as error:
            print("An error occurred: %s" % error)

    def delete_shift_from_google_calendar(self, event_id):
        try:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
            print("Event deleted")
        except HttpError as error:
            print("An error occurred: %s" % error)

    def get_future_shifts_from_google(self):
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            print("Getting upcoming shifts")
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    maxResults=25,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No shifts found.")
                return []
            shifts = []
            for event in events:
                if event["summary"] == "Work":
                    shifts.append(event)
            return shifts
        except HttpError as error:
            print("An error occurred: %s" % error)

    def delete_all_shifts_from_google_calendar(self):
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            print("Getting upcoming shifts")
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    maxResults=25,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No shifts found.")
                return []
            shifts = []
            for event in events:
                if event["summary"] == "Work":
                    shifts.append(event)
            for shift in shifts:
                self.delete_shift_from_google_calendar(shift["id"])
        except HttpError as error:
            print("An error occurred: %s" % error)

    def process_shifts(self):
        google_shifts = self.get_future_shifts_from_google()
        roster_shifts_temp = self.get_shifts()

        # We only want to look at future shifts from todays date

        roster_shifts = []
        for shift in roster_shifts_temp:
            if pd.to_datetime(shift.unformatted_start) > pd.to_datetime(
                datetime.datetime.now()
            ):
                roster_shifts.append(shift)

        # Print shift dates for debugging
        print("Google Shifts:")
        for shift in google_shifts:
            print(
                shift["start"]["dateTime"], shift["end"]["dateTime"], shift["location"]
            )

        print("Roster Shifts:")
        for shift in roster_shifts:
            print(shift.get_start_time(), shift.get_end_time(), shift.get_location())

        # If there is a shift in google that is not in roster, delete it from google
        for google_shift in google_shifts:
            found = False
            for roster_shift in roster_shifts:
                if (
                    roster_shift.get_start_time()
                    == google_shift["start"]["dateTime"].split("+")[0]
                    and roster_shift.get_end_time()
                    == google_shift["end"]["dateTime"].split("+")[0]
                    and roster_shift.get_location() == google_shift["location"]
                ):
                    found = True
                    break
            if not found:
                print("Deleting shift from google calendar")
                self.delete_shift_from_google_calendar(google_shift["id"])

        # If there is a shift in roster that is not in google, add it to google
        for roster_shift in roster_shifts:
            found = False
            for google_shift in google_shifts:
                if (
                    roster_shift.get_start_time()
                    == google_shift["start"]["dateTime"].split("+")[0]
                    and roster_shift.get_end_time()
                    == google_shift["end"]["dateTime"].split("+")[0]
                    and roster_shift.get_location() == google_shift["location"]
                ):
                    found = True
                    break
            if not found:
                print("Adding shift to google calendar")
                self.add_shift_to_google_calendar(roster_shift)


class CalendarHero:
    def __init__(self, username, password):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--incognito")
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.username = username
        self.password = password
        self.roster = Roster()

    def login(self):
        login_url = "https://employmenthero.yourpayroll.com.au/Public/Login"
        self.driver.get(login_url)

        username_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "Username"))
        )
        password_field = self.wait.until(
            EC.presence_of_element_located((By.ID, "Password"))
        )

        username = self.username
        password = self.password

        username_field.send_keys(username)
        password_field.send_keys(password)

        password_field.send_keys(Keys.RETURN)

        self.wait.until(EC.presence_of_element_located((By.ID, "header")))
        print("Successfully logged in")

    def get_schedule_data(self, from_date, to_date):
        schedule_url = f"https://employmenthero.yourpayroll.com.au/Employee/6620264/Home/GetScheduleEvents?fromDate={from_date}&toDate={to_date}&showAllLeave=False"
        self.driver.get(schedule_url)

        pre_tag = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))

        schedule_data = pre_tag.text

        return json.loads(schedule_data)

    def get_shifts(self, from_date, to_date):
        shifts_data = self.get_schedule_data(from_date, to_date)
        shifts = shifts_data["data"]["Shifts"]
        return shifts

    def print_shifts(self):
        shifts = self.roster.get_shifts()
        print("--------------------------------------------------")
        for shift in shifts:
            print(shift.shift_id)
            print(
                shift.day,
                shift.date,
                shift.time_start,
                shift.time_end,
                shift.location,
            )
            print("Unformatted Start:", shift.unformatted_start)
            print("Unformatted End:", shift.unformatted_end)
            print("--------------------------------------------------")

    def process_shifts(self, from_date, to_date):
        shifts_list = self.get_shifts(from_date, to_date)

        for shift in shifts_list:
            date = pd.to_datetime(shift["start"].split("T")[0]).strftime("%d-%m-%Y")
            time_start = shift["start"].split("T")[1]
            time_end = shift["end"].split("T")[1]
            day = pd.Timestamp(shift["start"].split("T")[0]).day_name()
            location_unformatted = shift["LocationName"]
            location = "".join(location_unformatted.split()[1:])

            if time_start.split(":")[1] != "00":
                formatted_time_start = pd.to_datetime(time_start).strftime("%I%M%p")
            else:
                formatted_time_start = pd.to_datetime(time_start).strftime("%I%p")

            if time_end.split(":")[1] != "00":
                formatted_time_end = pd.to_datetime(time_end).strftime("%I%M%p")
            else:
                formatted_time_end = pd.to_datetime(time_end).strftime("%I%p")

            shift_id = (
                date
                + "_"
                + formatted_time_start
                + "-"
                + formatted_time_end
                + "_"
                + location
            )
            new_shift = Shift(
                shift_id,
                day,
                date,
                pd.to_datetime(time_start).strftime("%I:%M%p"),
                pd.to_datetime(time_end).strftime("%I:%M%p"),
                location,
                shift["start"],
                shift["end"],
            )
            self.roster.add_shift(new_shift)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    app = CalendarHero("luke@simurina.com", config("PASSWORD"))
    try:
        app.login()
        app.process_shifts("2023-01-01", "2023-12-31")
        app.roster.process_shifts()
    finally:
        app.close()
        pass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from decouple import config
import json
import pandas as pd


class Shift:
    def __init__(self, shift_id, day, date, time_start, time_end, location):
        self.shift_id = shift_id
        self.day = day
        self.date = date
        self.time_start = time_start
        self.time_end = time_end
        self.location = location


class Roster:
    def __init__(self):
        self.shifts = []

    def add_shift(self, shift):
        self.shifts.append(shift)

    def get_shifts(self):
        return self.shifts


class CalenderHero:
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
            print("--------------------------------------------------")

    def process_shifts(self, from_date, to_date):
        shifts_list = self.get_shifts(from_date, to_date)

        for shift in shifts_list:
            date = pd.to_datetime(shift["start"].split("T")[0]).strftime("%d-%m-%Y")
            time_start = shift["start"].split("T")[1]
            time_end = shift["end"].split("T")[1]
            day = pd.Timestamp(date).day_name()
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
            )
            self.roster.add_shift(new_shift)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    app = CalenderHero("luke@simurina.com", config("PASSWORD"))
    try:
        app.login()

        # shifts = app.get_schedule_data("2023-07-31", "2023-09-11")
        # print(shifts)

        # get_shifts = app.get_shifts("2023-07-31", "2023-09-11")
        # print(get_shifts)
        app.process_shifts("2023-07-31", "2023-09-11")
        app.print_shifts()
    finally:
        app.close()

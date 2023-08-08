from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from decouple import config
import json


class Shift:
    def __init__(self, day, date, time_start, time_end, role):
        self.day = day
        self.date = date
        self.time_start = time_start
        self.time_end = time_end
        self.role = role


class CalenderHero:
    def __init__(self, username, password):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--incognito")
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.username = username
        self.password = password

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

    def print_shifts(self, from_date, to_date):
        shifts = self.get_shifts(from_date, to_date)
        for shift in shifts:
            print("Shift Title:", shift["title"])
            print("Start Time:", shift["start"])
            print("End Time:", shift["end"])
            print("Location:", shift["LocationName"])
            print("Role:", shift["Role"])
            print("=" * 40)

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

        app.print_shifts("2023-08-17", "2023-08-20")
    finally:
        app.close()

## CalendarHero: Sync Employment Hero to Google Calendar

Need to keep your Google Calendar in sync with Employment Hero shifts?

CalendarHero is here to help! This simple app automates the process, saving you time and effort.

Here's how to get started:

1. **Clone the app**:
   ```bash
   git clone https://github.com/lukesimurina/CalendarHero.git```

2. **Create a Google Cloud Project**: [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Calendar API.
   - Create OAuth client ID credentials (Desktop app).
   - Download the JSON file and rename it to `google_calendar_credentials.json`.
   - Place `google_calendar_credentials.json` in the same folder as the app's `main.py` file.

3. **Install app requirements**:
   ```bash
   cd CalendarHero
   pip install -r requirements.txt
   ```
   *(Optional)* Create a virtual environment (recommended):
   - Use `venv` or `virtualenv` tools.
   - Activate the environment (instructions vary by OS).

4. **Set your Google Calendar ID**:
   - Open `main.py` and find `self.calendar_id = ""`.
   - Replace the empty string with your calendar's ID (found in settings of the new calendar you created).

5. **Run the app**:
   ```bash
   python main.py
   ```
   
That's it! CalendarHero will attempt to sync your shifts.

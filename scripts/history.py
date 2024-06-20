import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

current_directory = Path(__file__).resolve().parent

box_info = pd.read_csv(current_directory.parent / "daten" / "box_info" / "box_info.csv")

# Getting the dates for past week
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

end_date_str = end_date.isoformat() + 'Z'
start_date_str = start_date.isoformat() + 'Z'

file_ending_today = str(end_date.date())

# Request
url = f'https://api.opensensemap.org/boxes/{box_info["ID"][0]}/data/{box_info["Temperature_sensor_id"][0]}?from-date={start_date_str}&to-date={end_date_str}'

response = requests.get(url)
response = response.json()

past_week_temperature = pd.DataFrame(response).drop("location", axis=1)

# Adjust dtypes
past_week_temperature['createdAt'] = pd.to_datetime(past_week_temperature['createdAt'])
past_week_temperature["value"] = pd.to_numeric(past_week_temperature["value"])

# New index
past_week_temperature = past_week_temperature.set_index("createdAt")

# Resample
past_week_temperature = past_week_temperature.resample('h').mean()
past_week_temperature["value"] = past_week_temperature["value"].round(1)

past_week_temperature.to_csv(current_directory.parent / "daten" / "past_week" / f"past_week_{file_ending_today}.csv")


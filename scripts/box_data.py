import pandas as pd
import requests
import folium
from pathlib import Path

current_directory = Path(__file__).resolve().parent

# Box we want to investigate
box_id = "63cbcc462b62690008f2fe1e"


# Data request for box information
url = f'https://api.opensensemap.org/boxes/{box_id}?format=json'

response = requests.get(url)
response = response.json()

# Getting temperature sensor _id
sensors = response["sensors"]

for sensor in sensors:
    if sensor["unit"] == "°C":
        sensor_id = sensor["_id"]
        break

# Data structure for df
box_data = [[response["_id"], response["name"], response["currentLocation"]["coordinates"], sensor_id]]
columns = ["ID", "Name", "Coordinates", "Temperature_sensor_id"]

box_info = pd.DataFrame(box_data, columns=columns)
box_info.to_csv(current_directory.parent / "daten" / "box_info" / "box_info.csv")

lat = box_info["Coordinates"][0][1]
lon = box_info["Coordinates"][0][0]

map_ = folium.Map(location=[lat, lon], zoom_start=15)
folium.Marker(
    location=[lat, lon],
    popup=f"{box_info.at[0, 'Name']} (ID: {box_info.at[0, 'ID']})",
    icon=folium.Icon(color="red"),
    tooltip=box_info.at[0, 'Name']
).add_to(map_)

map_.save(current_directory.parent / "graphs_static" / "location" / "map.html")


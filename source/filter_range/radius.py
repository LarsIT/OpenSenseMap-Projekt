import math
import json
import os

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    r = 6371  # Radius of Earth in kilometers. Use 3956 for miles. Determines return value units.
    return r * c


if __name__ == "__main__":
    
    target_name = "cologne"
    target_distance = 100
    target_lat, target_long = 50.56147, 6.57370 # cologne

    in_range = []

    file_location = "source/requests/sense_boxes_data.json"
    save_location = "source/filter_range/radius"

    with open(file_location, 'r') as json_file:
        data = json.load(json_file)

    for box in data:
        lat = box["currentLocation"]["coordinates"][1]
        long = box["currentLocation"]["coordinates"][0]
        
        distance = haversine(target_lat, target_long, lat, long)

        if distance <= target_distance:
            in_range.append(box)
        
    with open(f"{save_location}/{target_name}_{target_distance}.json", 'w') as json_file:
        json.dump(in_range, json_file, indent=4)  # indent=4 for pretty formatting
    print(f"{len(in_range)} boxes near {target_name}")

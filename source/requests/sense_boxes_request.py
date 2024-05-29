import requests
import json

def request():
    # API URL, um alle Boxen zu erhalten
    url = 'https://api.opensensemap.org/boxes'

    save_location = "source/requests/sense_boxes_data.json"

    # GET Anfrage an die API
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        # Print the keys of the first item to verify the response structure
        print(data[0].keys())
        
        # Save the response data as a JSON file
        with open(save_location, 'w') as json_file:
            json.dump(data, json_file, indent=4)  # indent=4 for pretty formatting
    else:
        print(f"Error: {response.status_code}")


if __name__ == "__main__":
    request()

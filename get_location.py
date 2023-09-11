import json
import requests

def get_locationId(destination):
    url = "https://travel-advisor.p.rapidapi.com/locations/search"`

    querystring = {"query":destination,"limit":"1","offset":"0","units":"km","location_id":"1","currency":"USD","sort":"relevance","lang":"en_US"}

    headers = {
	    "X-RapidAPI-Key": "7e2044af5fmsh645c3016f861157p104f11jsnca6fe90724fe",
	    "X-RapidAPI-Host": "travel-advisor.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    # response.text.loads(response.text)
    return response.json()['data'][0]['result_object']['location_id']

def get_locationId(destination):
    # Use the Google Maps Geocoding API to get location data
    google_maps_api_key = "YOUR_GOOGLE_MAPS_API_KEY"  # Replace with your Google Maps API key
    google_maps_url = "https://maps.googleapis.com/maps/api/geocode/json"

    # Prepare the request parameters
    params = {
        "address": destination,
        "key": google_maps_api_key,
    }

    # Send the request to the Google Maps Geocoding API
    google_maps_response = requests.get(google_maps_url, params=params)

    # Check if the request was successful
    if google_maps_response.status_code == 200:
        # Parse the response JSON
        google_maps_data = google_maps_response.json()

        # Extract the location data from the Google Maps response (e.g., latitude and longitude)
        if google_maps_data["status"] == "OK" and google_maps_data.get("results"):
            # You may need to adapt this part depending on the structure of the Google Maps response
            location_data = google_maps_data["results"][0]["geometry"]["location"]

            # Return the location data
            return {
                "latitude": location_data["lat"],
                "longitude": location_data["lng"],
            }
        else:
            # Handle cases where no results were found or other errors
            return None
    else:
        # Handle HTTP errors from the Google Maps API
        return None

# Example usage:
destination = "New York, USA, Europe, canada, france, united kingdom"
location_id = get_locationId(destination)
if location_id:
    print(f"Location ID for {destination}: {location_id}")
else:
    print(f"Failed to retrieve location data for {destination}")


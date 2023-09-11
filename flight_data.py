import os
from dotenv import load_dotenv
import requests

load_dotenv()

def text_to_code(text):
    # convert text to airport code
    url = "https://aerodatabox.p.rapidapi.com/airports/search/term"

    querystring = {"q": text, "limit": "10"}

    headers = {
        "X-RapidAPI-Key": os.getenv('RAPID_API_KEY'),
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    
    # Check if any items were found
    if 'items' in response.json() and len(response.json()['items']) > 0:
        return response.json()['items'][0]['iata']
    else:
        raise Exception(f"No airport found for '{text}'")

def get_flight_data(source, destination, date):
    # date format: YYYY-MM-DD
    # Get flight data from the Skyscanner API
    source = text_to_code(source)
    destination = text_to_code(destination)
    url = "https://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/US/USD/en-US/1/"

    querystring = {
        "originPlace": source,
        "destinationPlace": destination,
        "outboundDate": date,
        "apiKey": os.getenv('SKYSCANNER_API_KEY')
    }

    headers = {
        "X-RapidAPI-Host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        "X-RapidAPI-Key": os.getenv('RAPID_API_KEY')
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        quotes = data.get('Quotes', [])
        carriers = data.get('Carriers', [])

        flight_data = []

        for quote in quotes:
            carrier_id = quote.get('OutboundLeg', {}).get('CarrierIds', [])[0]
            carrier = next((c for c in carriers if c['CarrierId'] == carrier_id), None)

            if carrier:
                flight_data.append({
                    'name': carrier.get('Name'),
                    'price': quote.get('MinPrice')
                })

        flight_data.sort(key=lambda x: x['price'])
        
        return flight_data
    else:
        raise Exception(f"Skyscanner API request failed with status code {response.status_code}")

# Example usage:
try:
    flight_data = get_flight_data('New York', 'Los Angeles', '2023-02-01')
    for i, flight in enumerate(flight_data, start=1):
        print(f"Option {i}: {flight['name']} - Price: {flight['price']} USD")
except Exception as e:
    print(f"An error occurred: {str(e)}")


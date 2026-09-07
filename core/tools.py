import datetime
import requests

def get_current_time() -> str:
    """Returns the current date and time."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_weather(latitude: float, longitude: float) -> str:
    """
    Fetches the current real-time weather for a specific latitude and longitude.
    The AI will automatically guess the coordinates if the user names a city.
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            weather = data.get("current_weather", {})
            temp = weather.get("temperature")
            wind = weather.get("windspeed")
            
            # Return the exact data back to the AI so it can read it
            return f"The current temperature is {temp}°C with a wind speed of {wind} km/h."
        else:
            return "Error: Could not fetch weather data."
            
    except Exception as e:
        return f"Error connecting to weather service: {e}"
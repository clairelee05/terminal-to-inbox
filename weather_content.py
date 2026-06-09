import requests
from datetime import datetime

def get_current_location():
    response = requests.get("https://ipapi.co/json/")
    response.raise_for_status()
    data = response.json()

    return {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "location_name": f"{data.get('city', 'Current Location')}, {data.get('region', '')}".strip(
            ", "
        ),
    }


def add_weather(config, latitude=None, longitude=None, location_name=None):
    for item in config.get("content", []):
        if item["type"] == "weather":
            return "Weather content already exists."

    if latitude is None or longitude is None:
        location = get_current_location()
        latitude = location["latitude"]
        longitude = location["longitude"]

        if location_name is None:
            location_name = location["location_name"]

    if location_name is None:
        location_name = "Custom Location"

    config["content"].append(
        {
            "type": "weather",
            "latitude": latitude,
            "longitude": longitude,
            "location_name": location_name,
        }
    )

    return f"Added weather for {location_name}"

def get_weather_emoji(weather_code):
    if weather_code == 0:
        return "☀️"

    if weather_code in {1, 2}:
        return "🌤️"

    if weather_code == 3:
        return "☁️"

    if weather_code in {45, 48}:
        return "🌫️"

    if weather_code in {51, 53, 55, 56, 57}:
        return "🌦️"

    if weather_code in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "🌧️"

    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "🌨️"

    if weather_code in {95, 96, 99}:
        return "⛈️"

    return "🌤️"

def get_weather_html(item):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "sunrise,"
            "sunset"
        ),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "forecast_days": 1,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    current = data["current"]
    daily = data["daily"]

    current_temp = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    wind_speed = current["wind_speed_10m"]
    weather_code = current["weather_code"]
    weather_emoji = get_weather_emoji(weather_code)
    high_temp = daily["temperature_2m_max"][0]
    low_temp = daily["temperature_2m_min"][0]
    sunrise = datetime.fromisoformat(daily["sunrise"][0]).strftime("%-I:%M %p")
    sunset = datetime.fromisoformat(daily["sunset"][0]).strftime("%-I:%M %p")


    return f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif;">
        <h2 style="margin-top:0; margin-bottom:10px; font-size:18px;">
            {weather_emoji} Weather for {item["location_name"]}
        </h2>

        <div style="font-size:32px; font-weight:bold; margin-bottom:8px;">
            {current_temp}°F
        </div>

        <div style="font-size:14px; margin-bottom:12px;">
            High: {high_temp}°F &nbsp; | &nbsp; Low: {low_temp}°F
        </div>

        <table style="font-size:13px;">
            <tr>
                <td style="padding-right:20px;"><strong>Humidity</strong></td>
                <td>{humidity}%</td>
            </tr>
            <tr>
                <td style="padding-right:20px;"><strong>Wind Speed</strong></td>
                <td>{wind_speed} mph</td>
            </tr>
            <tr>
                <td style="padding-right:20px;">
                    <strong>Sunrise🌅</strong>
                </td>
                <td>{sunrise}</td>
            </tr>
            <tr>
                <td style="padding-right:20px;">
                    <strong>Sunset🌇</strong>
                </td>
                <td>{sunset}</td>
            </tr>
        </table>
    </div>
    """

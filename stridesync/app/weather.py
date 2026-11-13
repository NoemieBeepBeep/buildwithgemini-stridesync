# ruff: noqa
import httpx
import datetime
from typing import Dict, Any, Optional, List

DEFAULT_COORDINATES = {
    "hong kong": {"lat": 22.3193, "lon": 114.1694},
    "singapore": {"lat": 1.3521, "lon": 103.8198},
    "tokyo": {"lat": 35.6762, "lon": 139.6503},
    "london": {"lat": 51.5074, "lon": -0.1278},
    "new york": {"lat": 40.7128, "lon": -74.0060},
    "sydney": {"lat": -33.8688, "lon": 151.2093},
    "san francisco": {"lat": 37.7749, "lon": -122.4194},
}

DEMO_WEATHER_PRESETS = {
    "33c_humid": {
        "city": "Demo (Tropical Heat)",
        "temperature_c": 33.2,
        "relative_humidity": 86,
        "precipitation_mm": 0.0,
        "condition": "Tropical Heat & High Humidity",
        "is_extreme_heat": True,
        "is_rain": False,
        "is_cold": False,
    },
    "heavy_rain": {
        "city": "Demo (Downpour)",
        "temperature_c": 22.0,
        "relative_humidity": 94,
        "precipitation_mm": 18.5,
        "condition": "Heavy Rain & Slippery Conditions",
        "is_extreme_heat": False,
        "is_rain": True,
        "is_cold": False,
    },
}

async def fetch_city_weather(city_name: Optional[str] = "Hong Kong", demo_override: Optional[str] = None) -> Dict[str, Any]:
    """Fetches real-time current weather and 7-day daily forecast from Open-Meteo or demo presets."""
    city_clean = (city_name or "Hong Kong").strip().lower()
    coords = DEFAULT_COORDINATES.get(city_clean, DEFAULT_COORDINATES["hong kong"])

    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={coords['lat']}&longitude={coords['lon']}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code"
        f"&timezone=auto"
    )

    current_data = None
    daily_forecast: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(forecast_url)
            if resp.status_code == 200:
                res_json = resp.json()
                cur = res_json.get("current", {})
                daily = res_json.get("daily", {})

                # Current
                temp = cur.get("temperature_2m", 26.0)
                humidity = cur.get("relative_humidity_2m", 70)
                precip = cur.get("precipitation", 0.0)
                weather_code = cur.get("weather_code", 0)

                is_rain = precip > 1.0 or weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]
                is_extreme_heat = temp >= 30.0 or (temp >= 28.0 and humidity >= 78)
                is_cold = temp <= 5.0

                cond = "Mild & Clear"
                if is_rain:
                    cond = "Rain / Wet Ground"
                elif is_extreme_heat:
                    cond = "High Heat & Humidity"
                elif is_cold:
                    cond = "Cold / Frigid"

                current_data = {
                    "city": city_name or "Hong Kong",
                    "temperature_c": round(temp, 1),
                    "relative_humidity": humidity,
                    "precipitation_mm": precip,
                    "condition": cond,
                    "is_extreme_heat": is_extreme_heat,
                    "is_rain": is_rain,
                    "is_cold": is_cold,
                }

                # 7-day daily forecast
                dates = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                precip_sums = daily.get("precipitation_sum", [])
                precip_probs = daily.get("precipitation_probability_max", [])
                codes = daily.get("weather_code", [])

                for i in range(min(7, len(dates))):
                    d_str = dates[i]
                    # Parse date to get day name like Fri, Nov 13
                    d_obj = datetime.date.fromisoformat(d_str)
                    label = d_obj.strftime("%a, %b %d")
                    t_max = max_temps[i] if i < len(max_temps) else 26
                    t_min = min_temps[i] if i < len(min_temps) else 20
                    p_sum = precip_sums[i] if i < len(precip_sums) else 0.0
                    p_prob = precip_probs[i] if i < len(precip_probs) else 10
                    c_code = codes[i] if i < len(codes) else 0

                    d_rain = p_sum > 2.0 or p_prob > 55 or c_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]
                    d_heat = t_max >= 31.0
                    
                    if d_rain:
                        icon = "🌧️"
                        cond_name = "Rain / Showers"
                    elif d_heat:
                        icon = "☀️"
                        cond_name = "Hot & Humid"
                    elif c_code in [1, 2, 3]:
                        icon = "⛅"
                        cond_name = "Partly Cloudy"
                    else:
                        icon = "🌤️"
                        cond_name = "Clear / Pleasant"

                    daily_forecast.append({
                        "date_iso": d_str,
                        "date_label": label,
                        "temp_max": round(t_max, 1),
                        "temp_min": round(t_min, 1),
                        "precip_prob": p_prob,
                        "icon": icon,
                        "condition": cond_name,
                        "is_indoor_recommended": d_rain or d_heat
                    })
    except Exception as e:
        pass

    # Fallback if network or error
    if not current_data:
        current_data = {
            "city": city_name or "Hong Kong",
            "temperature_c": 28.5,
            "relative_humidity": 80,
            "precipitation_mm": 0.0,
            "condition": "Warm & Humid (Fallback)",
            "is_extreme_heat": False,
            "is_rain": False,
            "is_cold": False,
        }

    if not daily_forecast:
        today = datetime.date.today()
        for i in range(7):
            d = today + datetime.timedelta(days=i)
            daily_forecast.append({
                "date_iso": d.isoformat(),
                "date_label": d.strftime("%a, %b %d"),
                "temp_max": 28.0 + (i % 3),
                "temp_min": 22.0,
                "precip_prob": 20 + (i * 10 % 60),
                "icon": "⛅" if i % 2 == 0 else "🌧️",
                "condition": "Humid / Periodic Rain" if i % 2 == 1 else "Partly Cloudy",
                "is_indoor_recommended": (i % 2 == 1)
            })

    # Apply demo overrides to current & day 0 if active
    if demo_override and demo_override in DEMO_WEATHER_PRESETS:
        preset = DEMO_WEATHER_PRESETS[demo_override].copy()
        current_data.update(preset)
        if daily_forecast:
            daily_forecast[0]["temp_max"] = preset["temperature_c"]
            daily_forecast[0]["icon"] = "🌧️" if preset["is_rain"] else "🔥"
            daily_forecast[0]["condition"] = preset["condition"]
            daily_forecast[0]["is_indoor_recommended"] = True

    return {
        "current": current_data,
        "daily_forecast": daily_forecast
    }

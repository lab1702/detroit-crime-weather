#!/usr/bin/env python3
"""
Step 0 — Download all raw inputs.

Produces:
  detroit_crime.csv          (Detroit Open Data Portal, ~305 MB)
  detroit_weather.csv        (daily mean/max/min temp + precip, °F)
  detroit_weather_full.csv   (daily weather_code, precip, rain, snow, wind)
  detroit_weather_hourly.csv (hourly 2 m temperature, °F)

The analysis window is fixed to match the published report. Detroit downtown
coordinates are used for the weather point. Re-running later will fetch newer
crime rows; keep END_DATE in sync with the latest full day of crime data.
"""
import requests, pandas as pd

CRIME_URL = ("https://data.detroitmi.gov/api/download/v1/items/"
             "8e532daeec1149879bd5e67fdd9c8be0/csv?layers=0")
LAT, LON = 42.3314, -83.0458
START_DATE, END_DATE = "2017-01-01", "2026-06-03"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def fetch_crime():
    print("Downloading crime CSV (large, ~305 MB)…")
    with requests.get(CRIME_URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open("detroit_crime.csv", "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    print("  saved detroit_crime.csv")


def fetch_weather():
    base = dict(latitude=LAT, longitude=LON, start_date=START_DATE,
                end_date=END_DATE, timezone="America/Detroit")

    # daily basic (temperature in °F, precip in inches)
    d = requests.get(ARCHIVE, params={**base, "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum"},
        timeout=180).json()["daily"]
    pd.DataFrame(d).to_csv("detroit_weather.csv", index=False)
    print("  saved detroit_weather.csv")

    # daily full (codes, precip type, wind)
    d = requests.get(ARCHIVE, params={**base, "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch", "wind_speed_unit": "mph",
        "daily": "weather_code,temperature_2m_mean,precipitation_sum,rain_sum,"
                 "snowfall_sum,precipitation_hours,wind_speed_10m_max"},
        timeout=180).json()["daily"]
    pd.DataFrame(d).to_csv("detroit_weather_full.csv", index=False)
    print("  saved detroit_weather_full.csv")

    # hourly temperature
    d = requests.get(ARCHIVE, params={**base, "temperature_unit": "fahrenheit",
        "hourly": "temperature_2m"}, timeout=180).json()["hourly"]
    h = pd.DataFrame(d); h["time"] = pd.to_datetime(h["time"])
    h.to_csv("detroit_weather_hourly.csv", index=False)
    print("  saved detroit_weather_hourly.csv")


if __name__ == "__main__":
    fetch_crime()
    fetch_weather()
    print("Done. Next: python3 01_build_datasets.py")

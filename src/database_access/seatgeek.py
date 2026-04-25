# Importing Python Libraries
import os
import pandas as pd
import requests

class SeatGeek:

    """ 
    to get the seatgeek API Key 
    1) go to the following website to create an account or login in: https://developer.seatgeek.com/login
    2) Select Explorer table 
    3) Select Get API 
    4) Select "ADD a New APP" 
    5) add required infomraiton
    5.1) if you are not using OAuth product, fill out Redicrec URl 1* with "http://localhost"
    6) Create applicaiton 
    7) Select the dropw down to find the consumer key 
    8) copy and paste the consumer key 
    """

    @staticmethod
    def fetch_events(url, params):
        if not params.get("client_id"):
            raise ValueError("Missing SEATGEEK_CLIENT_ID.")

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        events = []

        for event in data.get("events", []):
            venue = event.get("venue", {})

            events.append({
                "event_name": event.get("title"),
                "date_time_utc": event.get("datetime_utc"),
                "date_time_local": event.get("datetime_local"),
                "venue": venue.get("name"),
                "address": venue.get("address"),
                "city": venue.get("city"),
                "state": venue.get("state"),
                "postal_code": venue.get("postal_code"),
                "latitude": venue.get("location", {}).get("lat"),
                "longitude": venue.get("location", {}).get("lon"),
                "performers": ", ".join(
                    performer.get("name", "")
                    for performer in event.get("performers", [])
                    if performer.get("name")
                ),
                "score": event.get("score"),
                "average_price": event.get("stats", {}).get("average_price"),
                "lowest_price": event.get("stats", {}).get("lowest_price"),
                "highest_price": event.get("stats", {}).get("highest_price"),
                "visible_listing_count": event.get("stats", {}).get("visible_listing_count"),
                "url": event.get("url"),
            })

        return events

    @staticmethod
    def save_events_to_excel(events, output_file):
        df = pd.DataFrame(events)

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_excel(output_file, index=False)

        print(f"Saved {output_file}")
        print(f"Rows: {len(df)}")
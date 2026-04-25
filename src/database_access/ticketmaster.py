# Importing Python Libraries
import os
import pandas as pd
import requests


class TicketMaster:

    @staticmethod
    def get_capacity(venue_name, venue_capacity):
        venue_name = str(venue_name or "").lower()

        for venue, capacity in venue_capacity.items():
            if venue.lower() in venue_name or venue_name in venue.lower():
                return capacity

        return None

    @classmethod
    def estimate_event_size(cls, event_name, venue_name, venue_capacity):
        capacity = cls.get_capacity(venue_name, venue_capacity)

        if capacity is None:
            return None

        name = str(event_name or "").lower()

        if "vs" in name or "mariners" in name or "seahawks" in name or "sounders" in name:
            fill_rate = 0.75
        elif "concert" in name or "tour" in name or "live" in name:
            fill_rate = 0.85
        elif "festival" in name:
            fill_rate = 0.90
        else:
            fill_rate = 0.60

        return int(capacity * fill_rate)

    @staticmethod
    def crowd_rank(estimated_size):
        if estimated_size is None or pd.isna(estimated_size):
            return "Unknown"

        if estimated_size >= 50000:
            return "Very High"
        if estimated_size >= 20000:
            return "High"
        if estimated_size >= 5000:
            return "Medium"
        if estimated_size >= 1000:
            return "Low"

        return "Very Low"

    @classmethod
    def fetch_events(cls, api_key, venue_capacity, size=200):
        if not api_key:
            raise ValueError("Missing API key")

        url = "https://app.ticketmaster.com/discovery/v2/events.json"

        params = {
            "apikey": api_key,
            "city": "Seattle",
            "stateCode": "WA",
            "countryCode": "US",
            "size": size,
            "sort": "date,asc",
        }

        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        events = []

        for event in data.get("_embedded", {}).get("events", []):
            venue = event.get("_embedded", {}).get("venues", [{}])[0]

            event_name = event.get("name")
            venue_name = venue.get("name")

            estimated_size = cls.estimate_event_size(
                event_name,
                venue_name,
                venue_capacity
            )

            events.append({
                "event_name": event_name,
                "date": event.get("dates", {}).get("start", {}).get("localDate"),
                "time": event.get("dates", {}).get("start", {}).get("localTime"),
                "venue": venue_name,
                "estimated_event_size": estimated_size,
                "crowd_rank": cls.crowd_rank(estimated_size),
            })

        return events

    @staticmethod
    def save_filtered_events_to_excel(events, min_size, max_size, output_file):
        df = pd.DataFrame(events)

        df = df[
            (df["estimated_event_size"].notna()) &
            (df["estimated_event_size"] >= min_size) &
            (df["estimated_event_size"] <= max_size)
        ]

        df.sort_values(
            by=["estimated_event_size", "date", "time"],
            ascending=[False, True, True],
            inplace=True
        )

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_excel(output_file, index=False)

        print(f"Saved {output_file}")
        print(f"Filtered Rows: {len(df)}")
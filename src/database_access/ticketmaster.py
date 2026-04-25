
# Importing Python Libraries
import os
import pandas as pd
import requests


class TicketMaster:
    """
    TicketMaster API Interface and Event Processing Class

    This class provides functionality to:
    1. Fetch event data from the Ticketmaster API
    2. Estimate event sizes based on venue capacity and event type
    3. Classify crowd levels
    4. Filter and export event data to Excel

    The class is designed for event-driven workforce scheduling analysis.
    """

    @staticmethod
    def get_capacity(venue_name, venue_capacity):
        """
        Retrieve venue capacity from predefined dictionary.

        Matching is performed using partial string comparison
        to handle variations in venue naming.

        Parameters:
            venue_name (str): Name of the venue from API
            venue_capacity (dict): Dictionary mapping venue names to capacities

        Returns:
            int or None: Capacity of venue if found, otherwise None
        """
        venue_name = str(venue_name or "").lower()

        for venue, capacity in venue_capacity.items():
            # Match either direction (robust string matching)
            if venue.lower() in venue_name or venue_name in venue.lower():
                return capacity

        return None

    @classmethod
    def estimate_event_size(cls, event_name, venue_name, venue_capacity):
        """
        Estimate attendance size of an event based on:
        - Venue capacity
        - Event type (sports, concert, festival, etc.)

        Parameters:
            event_name (str): Name of the event
            venue_name (str): Venue name
            venue_capacity (dict): Venue capacity lookup

        Returns:
            int or None: Estimated event attendance
        """
        capacity = cls.get_capacity(venue_name, venue_capacity)

        # If capacity is unknown, cannot estimate
        if capacity is None:
            return None

        name = str(event_name or "").lower()

        # Heuristic-based fill rates depending on event type
        if "vs" in name or "mariners" in name or "seahawks" in name or "sounders" in name:
            fill_rate = 0.75  # Sports events
        elif "concert" in name or "tour" in name or "live" in name:
            fill_rate = 0.85  # Concerts
        elif "festival" in name:
            fill_rate = 0.90  # Festivals
        else:
            fill_rate = 0.60  # Default/general events

        return int(capacity * fill_rate)

    @staticmethod
    def crowd_rank(estimated_size):
        """
        Categorize event size into crowd levels.

        Parameters:
            estimated_size (int): Estimated attendance

        Returns:
            str: Crowd category label
        """
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
        """
        Fetch event data from Ticketmaster API.

        Parameters:
            api_key (str): Ticketmaster API key
            venue_capacity (dict): Venue capacity lookup
            size (int): Number of events to fetch

        Returns:
            list[dict]: List of processed event records
        """
        if not api_key:
            raise ValueError("Missing API key")

        url = "https://app.ticketmaster.com/discovery/v2/events.json"

        # API query parameters
        params = {
            "apikey": api_key,
            "city": "Seattle",
            "stateCode": "WA",
            "countryCode": "US",
            "size": size,
            "sort": "date,asc",
        }

        # Send API request
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        events = []

        # Parse API response
        for event in data.get("_embedded", {}).get("events", []):
            venue = event.get("_embedded", {}).get("venues", [{}])[0]

            event_name = event.get("name")
            venue_name = venue.get("name")

            # Estimate attendance size
            estimated_size = cls.estimate_event_size(
                event_name,
                venue_name,
                venue_capacity
            )

            # Build structured event record
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
        """
        Filter and save event data to Excel file.

        Filters:
            - Removes events without estimated size
            - Keeps events within specified size range

        Parameters:
            events (list[dict]): Event dataset
            min_size (int): Minimum event size threshold
            max_size (int): Maximum event size threshold
            output_file (str): Output Excel file path

        Returns:
            None
        """
        df = pd.DataFrame(events)

        # Apply filtering conditions
        df = df[
            (df["estimated_event_size"].notna()) &
            (df["estimated_event_size"] >= min_size) &
            (df["estimated_event_size"] <= max_size)
        ]

        # Sort by largest events first, then date/time
        df.sort_values(
            by=["estimated_event_size", "date", "time"],
            ascending=[False, True, True],
            inplace=True
        )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Save to Excel
        df.to_excel(output_file, index=False)

        print(f"Saved {output_file}")
        print(f"Filtered Rows: {len(df)}")
# Importing Python Libraries
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import os
from xml.sax.saxutils import escape as xml_escape
import pandas as pd
import requests
from datetime import datetime, timezone


# Script / Python File connection
from database_access.turbo_overpass import TurboOverpass
from database_access.geographic_information_system import GIS
from database_access.ticketmaster import TicketMaster

out_path = "output/5mile_radius_store_list.xlsx"
kml_out_path = "output/5mile_radius_store_list.kml"

overpass_url = "https://overpass-api.de/api/interpreter"

location_name = "3rd Avenue, Seattle"
lat = 47.6050
lon = -122.3345
radius_meters = 8047

overpass_query = f"""
[out:json][timeout:180];
(
    node["amenity"~"^(bar|biergarten|cafe|fast_food|food_court|ice_cream|pub)$"](around:{radius_meters},{lat},{lon});
    node["shop"~"^(bakery|cheese|chocolate|confectionery|convenience|dairy|deli|food|frozen_food|ice_cream|nuts|pasta|pastry|supermarket)$"](around:{radius_meters},{lat},{lon});
);
out body;
""".strip()

data = TurboOverpass.fetch_overpass(overpass_url, overpass_query)
elements = data.get("elements", [])

TurboOverpass.write_excel(elements, out_path)
print("TurboOver pass - Finish extracting resturant location ")

GIS.write_kml(
    elements=elements,
    kml_out_path=kml_out_path,
    location_name=location_name,
    lat=lat,
    lon=lon
)
print("GIS, KML - Finish plotting the resturant location ")

# Ticketmaster Parameters 
""" 
to get the tickemaster API Key 
1) go to the following website to create an account or login in: https://developer-acct.ticketmaster.com/user/login?destination=user
2) Select Explorer table 
3) Select Get API 
4) Select "ADD a New APP" 
5) add required infomraiton
5.1) if you are not using OAuth product, fill out Redicrec URl 1* with "http://localhost"
6) Create applicaiton 
7) Select the dropw down to find the consumer key 
8) copy and paste the consumer key 
"""
TICKETMASTER_API_KEY = None # edit! 
SIZE = 200
MIN_EVENT_SIZE = 5000
MAX_EVENT_SIZE = 50000
OUTPUT_FILE = "output/ticketmaster_seattle_filtered_events.xlsx"

VENUE_CAPACITY = {
    "T-Mobile Park": 47929,
    "Lumen Field": 68740,
    "Climate Pledge Arena": 17200,
    "WAMU Theater": 7200,
    "Paramount Theatre": 2807,
    "Moore Theatre": 1800,
    "Showbox SoDo": 1800,
    "The Showbox": 1150,
    "Neptune Theatre": 1000,
}

# Step 1: Fetch
events = TicketMaster.fetch_events(
    api_key=TICKETMASTER_API_KEY,
    venue_capacity=VENUE_CAPACITY,
    size=SIZE
)

# Step 2: Save
TicketMaster.save_filtered_events_to_excel(
    events=events,
    min_size=MIN_EVENT_SIZE,
    max_size=MAX_EVENT_SIZE,
    output_file=OUTPUT_FILE
)
print("Ticketmaster - Finish extracting events near seattle location ")
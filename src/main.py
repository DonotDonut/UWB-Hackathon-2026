# Importing Python Libraries
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import os
from xml.sax.saxutils import escape as xml_escape
import pandas as pd
import requests
from datetime import datetime, timezone
import random



# Script / Python File connection
from database_access.turbo_overpass import TurboOverpass
from database_access.geographic_information_system import GIS
from database_access.ticketmaster import TicketMaster
from database_access.seatgeek import SeatGeek
from database_creation.employee import EmployeeGenerator
from database_modificaiton.resturant_capacity import ResturantCapacityEstimator
from database_modificaiton.event_coordinates import EventCoordinateMapper
from machine_learning.eclat import EclatScheduleSuggestion

# 
out_path = "output data/5mile_radius_store_list.xlsx"
kml_out_path = "output data/5mile_radius_store_list.kml"
INPUT_FILE = "output data/5mile_radius_store_list.xlsx"
OUTPUT_FILE = "output data/random_employee_staffing.xlsx"

''' 
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
OUTPUT_FILE = "output data/ticketmaster_seattle_filtered_events.xlsx"

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


""" 
Reference: https://seatgeek.com/build?msockid=1f897f4131c165c437936cce30c964b5 
to get the seatgeek API Key 
1) go to the following website to create an account or login in: https://developer.seatgeek.com/login
2) Account will need to be approved to get the private token (waiting atm)
"""
""" 
URL = "https://api.seatgeek.com/2/events"

CLIENT_ID = None
CLIENT_SECRET = None   # 

PER_PAGE = 100

OUTPUT_FILE = "output/seatgeek_seattle_events.xlsx"

# Build params dynamically
params = {
    "client_id": CLIENT_ID,
    "venue.city": "Seattle",
    "venue.state": "WA",
    "per_page": PER_PAGE,
    "sort": "datetime_utc.asc",
}

if CLIENT_SECRET:
    params["client_secret"] = CLIENT_SECRET

# Step 1: Fetch
events = SeatGeek.fetch_events(
    url=URL,
    params=params
)

# Step 2: Save
SeatGeek.save_events_to_excel(
    events=events,
    output_file=OUTPUT_FILE
)
"""


# creating employee databse 

POSITIONS = [
    "Store Manager",
    "Assistant Manager",
    "Cashier",
    "Stock Associate",
    "Sales Associate",
    "Customer Service Rep"
]

AVAILABILITY = [
    "Full-time",
    "Part-time",
    "Weekends",
    "Evenings",
    "Mornings",
    "Flexible"
]

SCHEDULES = [
    "Mon-Fri 9AM-5PM",
    "Mon-Wed 8AM-2PM",
    "Thu-Sun 12PM-8PM",
    "Sat-Sun 10AM-6PM",
    "Tue-Sat 2PM-10PM",
    "Flexible / On-call"
]

PEOPLE_PER_STORE = 9

EmployeeGenerator.generate_employee_sheet(
    input_store_file=INPUT_FILE,
    output_file=OUTPUT_FILE,
    positions=POSITIONS,
    availability=AVAILABILITY,
    schedules=SCHEDULES,
    people_per_store=PEOPLE_PER_STORE
)

# 
INPUT_FILE = "output data/5mile_radius_store_list.xlsx"
OUTPUT_FILE = "output data/5mile_radius_store_list_with_capacity.xlsx"

df = pd.read_excel(INPUT_FILE)

# Apply capacity estimation
df["estimated_store_capacity"] = df["name"].apply(
    ResturantCapacityEstimator.estimate_capacity
)

# Save
df.to_excel(OUTPUT_FILE, index=False)

print(f"Saved: {OUTPUT_FILE}")
print(f"Total Stores: {len(df)}")



INPUT_FILE = "output data/ticketmaster_seattle_filtered_events.xlsx"
OUTPUT_FILE = "output data/events_with_coordinates.xlsx"

VENUE_COORDS = {
    "T-Mobile Park": (47.5914, -122.3325),
    "Lumen Field": (47.5952, -122.3316),
    "Climate Pledge Arena": (47.6221, -122.3540),
    "WAMU Theater": (47.5930, -122.3270),
    "Paramount Theatre": (47.6135, -122.3316),
    "Moore Theatre": (47.6115, -122.3425),
    "Showbox SoDo": (47.5804, -122.3345),
    "The Showbox": (47.6099, -122.3417),
    "Neptune Theatre": (47.6615, -122.3130),
}

EventCoordinateMapper.add_coordinates(
    input_file=INPUT_FILE,
    output_file=OUTPUT_FILE,
    venue_coords=VENUE_COORDS
)
''' 

EMPLOYEE_FILE = "output data/random_employee_staffing.xlsx"
STORE_FILE = "output data/5mile_radius_store_list_with_capacity.xlsx"
EVENT_FILE = "output data/events_with_coordinates.xlsx"
OUTPUT_FILE = "output data/schedule_suggestions_eclat.xlsx"

EclatScheduleSuggestion.process(
    employee_file=EMPLOYEE_FILE,
    store_file=STORE_FILE,
    event_file=EVENT_FILE,
    output_file=OUTPUT_FILE,
    radius_miles=1.0,
    min_support=3
)
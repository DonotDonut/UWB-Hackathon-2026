"""
CrowdCue: Event-Based Workforce Scheduling System 

This script performs the full data pipeline:

1. Extract store locations using Turbo Overpass API
2. Generate KML visualization
3. Extract event data from Ticketmaster in the seattle region 
4. Generate synthetic employee dataset
5. Estimate store capacity 
6. Add coordinates to events 
7. Run Eclat algorithm for scheduling suggestions
8. Validate results (statistics + train/test split)

Author: Timothy Caole 
Date: April 2026

Description:
This project implements an event driven workforce scheduling
system using the Eclat frequent pattern mining algorithm.

Note:
This code was developed with assistance from AI tools
for structuring, debugging, and optimization.
"""


# Importing Python Libraries
import os
import pandas as pd
import random
import matplotlib.pyplot as plt

# Script / Python File connection
from database_access.turbo_overpass import TurboOverpass
from database_access.geographic_information_system import GIS
from database_access.ticketmaster import TicketMaster
from database_creation.employee import EmployeeGenerator
from database_modificaiton.resturant_capacity import ResturantCapacityEstimator
from database_modificaiton.event_coordinates import EventCoordinateMapper
from machine_learning.eclat import EclatScheduleSuggestion
from machine_learning.test import EclatTest


# Global File Paths
OUTPUT_DIR = "output data"

STORE_FILE = f"{OUTPUT_DIR}/5mile_radius_store_list.xlsx"
STORE_KML_FILE = f"{OUTPUT_DIR}/5mile_radius_store_list.kml"
STORE_CAPACITY_FILE = f"{OUTPUT_DIR}/5mile_radius_store_list_with_capacity.xlsx"

EMPLOYEE_FILE = f"{OUTPUT_DIR}/random_employee_staffing.xlsx"

TICKETMASTER_EVENT_FILE = f"{OUTPUT_DIR}/ticketmaster_seattle_filtered_events.xlsx"
EVENT_COORDINATE_FILE = f"{OUTPUT_DIR}/events_with_coordinates.xlsx"

ECLAT_OUTPUT_FILE = f"{OUTPUT_DIR}/schedule_suggestions_eclat.xlsx"



# 1. Extract store locations (Turbo Overpass)
def extract_store_locations():
    """
    Extract restaurant/store locations using OpenStreetMap Overpass API.
    Outputs:
        - Excel file (store list)
        - KML file (for visualization in GIS tools)
    """

    overpass_url = "https://overpass-api.de/api/interpreter"

    location_name = "3rd Avenue, Seattle"
    lat = 47.6050
    lon = -122.3345
    radius_meters = 8047  # ~5 miles

    # Overpass Query: fetch restaurants, cafes, grocery-related shops
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

    TurboOverpass.write_excel(elements, STORE_FILE)

    # Create KML visualization
    GIS.write_kml(
        elements=elements,
        kml_out_path=STORE_KML_FILE,
        location_name=location_name,
        lat=lat,
        lon=lon
    )

    print("TurboOverpass: Finished extracting store locations")
    print("GIS: Finished generating KML file")



# 2. Extract Ticketmaster events in seattle area 
def extract_ticketmaster_events():
    """
    Extract event data using Ticketmaster API.

    NOTE:
    - API key must be stored as environment variable
    - See instructions below
    """

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

    ticketmaster_api_key = None # edit here! 

    if not ticketmaster_api_key:
        raise ValueError("Missing TICKETMASTER_API_KEY")

    venue_capacity = {
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

    events = TicketMaster.fetch_events(
        api_key=ticketmaster_api_key,
        venue_capacity=venue_capacity,
        size=200
    )

    TicketMaster.save_filtered_events_to_excel(
        events=events,
        min_size=5000,
        max_size=50000,
        output_file=TICKETMASTER_EVENT_FILE
    )

    print("Ticketmaster: Finished extracting events")


# Step 3. Create employee dataset
def create_employee_database():
    """
    Generate synthetic employee dataset.
    Ensures each store has assigned employees.
    """

    positions = [
        "Store Manager",
        "Assistant Manager",
        "Cashier",
        "Stock Associate",
        "Sales Associate",
        "Customer Service Rep"
    ]

    availability = [
        "Full-time",
        "Part-time",
        "Weekends",
        "Evenings",
        "Mornings",
        "Flexible"
    ]

    schedules = [
        "Mon-Fri 9AM-5PM",
        "Mon-Wed 8AM-2PM",
        "Thu-Sun 12PM-8PM",
        "Sat-Sun 10AM-6PM",
        "Tue-Sat 2PM-10PM",
        "Flexible / On-call"
    ]

    EmployeeGenerator.generate_employee_sheet(
        input_store_file=STORE_FILE,
        output_file=EMPLOYEE_FILE,
        positions=positions,
        availability=availability,
        schedules=schedules,
        people_per_store=9
    )

    print("Employee DB: Generated employee dataset")



# 4. Estimate store capacity
def add_store_capacity():
    """
    Estimate store capacity based on store name/type.
    """

    df = pd.read_excel(STORE_FILE)

    df["estimated_store_capacity"] = df["name"].apply(
        ResturantCapacityEstimator.estimate_capacity
    )

    df.to_excel(STORE_CAPACITY_FILE, index=False)

    print(f"Saved: {STORE_CAPACITY_FILE}")
    print(f"Total Stores: {len(df)}")



# Step 5. Add event coordinates
def add_event_coordinates():
    """
    Map venue names to coordinates.
    """

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
        input_file=TICKETMASTER_EVENT_FILE,
        output_file=EVENT_COORDINATE_FILE,
        venue_coords=VENUE_COORDS
    )

    print("Events: Added coordinates")



# Run Eclat + Validation
def run_eclat_model():
    """
    Run Eclat algorithm and validate results.
    """
    
    MIN_CONFIDENCE = 0.75  # good range: 0.6–0.8
    MIN_LIFT = 1.5
    MAX_PATTERN_LENGTH = 2
    REMOVE_COMMON_ITEM_LIMIT = 3
    FOCUS_MAXIMAL_PATTERNS = False
    
    # higher the min_support it filters the noise keeping the patterns more real, if low then it it memorizing coincidences making it look stable 
    
    
    suggestions_df, frequent_df, rules_df = EclatScheduleSuggestion.process(
        employee_file=EMPLOYEE_FILE,
        store_file=STORE_CAPACITY_FILE,
        event_file=EVENT_COORDINATE_FILE,
        output_file=ECLAT_OUTPUT_FILE,
        radius_miles=1.0,
        min_support=75,
        min_confidence=MIN_CONFIDENCE,
        min_lift=MIN_LIFT,
        max_pattern_length=MAX_PATTERN_LENGTH,
        focus_maximal_patterns=FOCUS_MAXIMAL_PATTERNS#,
        #frequent_itemsets=REMOVE_COMMON_ITEM_LIMIT
    )


    employee_df = pd.read_excel(EMPLOYEE_FILE)
    store_df = pd.read_excel(STORE_CAPACITY_FILE)
    event_df = pd.read_excel(EVENT_COORDINATE_FILE)

    transactions = EclatScheduleSuggestion.build_transactions(
        employee_df=employee_df,
        store_df=store_df,
        event_df=event_df,
        radius_miles=1.0 # assuming that people would walk 1 mile to resturant after event 
    )

    EclatTest.validate_eclat_results(
        frequent_df=frequent_df,
        suggestions_df=suggestions_df
    )

    EclatTest.validate_train_test_patterns(
        transactions=transactions
    )

    ''' Metrics 
    Train Transactions, size of training data large data is great, e.g 10k+ 
    Test Transactions, patterns generalize to new data 
        - amoubt of data split to traing, ~20 - 40% 
        - we split the data by 30% 
    Train Frequent Patterns
        How many relationships your model found
        1k - 20k is good 
    Frequent Patterns
        - want value close to training Frequent Patterns close to the test Frequent Patterns 
        - if train count < Test Frequent Patterns then over fiiting 
        - if train count > Test Frequent Patterns then under fiiting 
    Overlapping Patterns (%) = overlap / train_patters 
        - 0.75 is good, 0.75 - 0.6 is good 
        0.5 is bad 
    Pattern Overlap Rate
    '''
    
    print("Eclat: Completed modeling + validation")


# main
random.seed(42)
os.makedirs(OUTPUT_DIR, exist_ok=True)

#extract_store_locations()
#extract_ticketmaster_events()
#create_employee_database()
#add_store_capacity()
#add_event_coordinates()
run_eclat_model()

print("Pipeline completed successfully.")



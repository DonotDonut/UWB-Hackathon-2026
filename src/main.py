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

GIS.write_kml(
    elements=elements,
    kml_out_path=kml_out_path,
    location_name=location_name,
    lat=lat,
    lon=lon
)
# Importing Python Libraries
import os
import requests
from xml.sax.saxutils import escape as xml_escape
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

# Script / Python File connection
from database_access.turbo_overpass import TurboOverpass


class GIS: 
    SWAP_LOD = 256

    @staticmethod
    def kml_region(lat, lon, half_size_deg=0.001, min_lod=0, max_lod=-1):
        return f"""
        <Region>
            <LatLonAltBox>
                <north>{lat + half_size_deg}</north>
                <south>{lat - half_size_deg}</south>
                <east>{lon + half_size_deg}</east>
                <west>{lon - half_size_deg}</west>
            </LatLonAltBox>
            <Lod>
                <minLodPixels>{min_lod}</minLodPixels>
                <maxLodPixels>{max_lod}</maxLodPixels>
            </Lod>
        </Region>
        """.strip()

    @staticmethod
    def center_placemark(location_name, lat, lon):
        return f"""
        <Placemark>
            <name>{xml_escape(location_name)}</name>
            <styleUrl>#centerRed</styleUrl>
            <Point>
                <coordinates>{lon},{lat},0</coordinates>
            </Point>
        </Placemark>
        """.strip()

    @classmethod
    def element_placemarks(cls, element):
        lat = element.get("lat")
        lon = element.get("lon")

        if lat is None or lon is None:
            return []

        tags = element.get("tags", {}) if isinstance(element.get("tags", {}), dict) else {}

        el_type = element.get("type", "")
        el_id = element.get("id", "")

        name = TurboOverpass.safe_get(tags, "name", "")
        shop = TurboOverpass.safe_get(tags, "shop", "")
        amenity = TurboOverpass.safe_get(tags, "amenity", "")
        brand = TurboOverpass.safe_get(tags, "brand", "")
        operator = TurboOverpass.safe_get(tags, "operator", "")
        phone = TurboOverpass.safe_get(tags, "phone", "")
        website = TurboOverpass.safe_get(tags, "website", "")

        addr_housenumber = TurboOverpass.safe_get(tags, "addr:housenumber", "")
        addr_street = TurboOverpass.safe_get(tags, "addr:street", "")
        addr_city = TurboOverpass.safe_get(tags, "addr:city", "")
        addr_state = TurboOverpass.safe_get(tags, "addr:state", "")
        addr_postcode = TurboOverpass.safe_get(tags, "addr:postcode", "")

        display_name = name.strip() or f"{amenity or shop or 'OSM Node'} ({el_type}:{el_id})"

        address_line = " ".join(filter(None, [addr_housenumber, addr_street]))
        city_line = ", ".join(filter(None, [addr_city, addr_state, addr_postcode]))
        category = amenity or shop

        description_parts = []

        if category:
            description_parts.append(f"<b>Category:</b> {xml_escape(str(category))}<br/>")
        if brand:
            description_parts.append(f"<b>Brand:</b> {xml_escape(str(brand))}<br/>")
        if operator:
            description_parts.append(f"<b>Operator:</b> {xml_escape(str(operator))}<br/>")
        if phone:
            description_parts.append(f"<b>Phone:</b> {xml_escape(str(phone))}<br/>")
        if website:
            description_parts.append(f"<b>Website:</b> {xml_escape(str(website))}<br/>")
        if address_line:
            description_parts.append(f"<b>Address:</b> {xml_escape(address_line)}<br/>")
        if city_line:
            description_parts.append(f"<b>City/State/Zip:</b> {xml_escape(city_line)}<br/>")

        description_parts.append(
            f"<b>OSM:</b> {xml_escape(str(el_type))} {xml_escape(str(el_id))}<br/>"
        )

        lat_f = float(lat)
        lon_f = float(lon)
        description = "".join(description_parts)

        placemark_icon_only = f"""
        <Placemark>
            <styleUrl>#storeIconOnly</styleUrl>
            {cls.kml_region(lat_f, lon_f, min_lod=0, max_lod=cls.SWAP_LOD)}
            <description><![CDATA[{description}]]></description>
            <Point>
                <coordinates>{lon_f},{lat_f},0</coordinates>
            </Point>
        </Placemark>
        """.strip()

        placemark_with_label = f"""
        <Placemark>
            <name>{xml_escape(display_name)}</name>
            <styleUrl>#storeWithLabel</styleUrl>
            {cls.kml_region(lat_f, lon_f, min_lod=cls.SWAP_LOD, max_lod=-1)}
            <description><![CDATA[{description}]]></description>
            <Point>
                <coordinates>{lon_f},{lat_f},0</coordinates>
            </Point>
        </Placemark>
        """.strip()

        return [placemark_icon_only, placemark_with_label]

    @classmethod
    def write_kml(cls, elements, kml_out_path, location_name, lat, lon):
        kml_placemarks = [
            cls.center_placemark(location_name, lat, lon)
        ]

        for element in elements:
            kml_placemarks.extend(cls.element_placemarks(element))

        kml_styles = """
        <Style id="centerRed">
            <IconStyle>
                <scale>1.2</scale>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href>
                </Icon>
            </IconStyle>
        </Style>

        <Style id="storeIconOnly">
            <IconStyle>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
                </Icon>
            </IconStyle>
            <LabelStyle>
                <scale>0</scale>
            </LabelStyle>
        </Style>

        <Style id="storeWithLabel">
            <IconStyle>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
                </Icon>
            </IconStyle>
            <LabelStyle>
                <scale>1</scale>
            </LabelStyle>
        </Style>
        """

        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>5 Mile Radius Merchant Hit List</name>
                {kml_styles}
                {''.join(kml_placemarks)}
            </Document>
        </kml>
        """

        os.makedirs(os.path.dirname(kml_out_path), exist_ok=True)

        if os.path.exists(kml_out_path):
            os.remove(kml_out_path)

        with open(kml_out_path, "w", encoding="utf-8") as f:
            f.write(kml_content)

        print(f"Saved: {kml_out_path} placemarks: {len(kml_placemarks)}")
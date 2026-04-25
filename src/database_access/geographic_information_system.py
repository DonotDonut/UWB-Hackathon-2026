
# Importing Python Libraries
import os
from xml.sax.saxutils import escape as xml_escape

# Script / Python File connection
from database_access.turbo_overpass import TurboOverpass


class GIS:
    """
    GIS helper class for creating KML files from OpenStreetMap
    Overpass API results.

    This class converts extracted store/restaurant location data
    into a KML file that can be opened in mapping tools such as
    Google Earth.

    Main outputs:
        - Center location placemark
        - Store/restaurant placemarks
        - KML styling for map visualization
    """

    # Pixel threshold where the map switches from icon-only view
    # to labeled placemark view.
    SWAP_LOD = 256

    @staticmethod
    def kml_region(lat, lon, half_size_deg=0.001, min_lod=0, max_lod=-1):
        """
        Create a KML Region block for controlling placemark visibility.

        Parameters:
            lat (float): Latitude of the placemark.
            lon (float): Longitude of the placemark.
            half_size_deg (float): Size of the bounding box around the point.
            min_lod (int): Minimum level-of-detail pixel threshold.
            max_lod (int): Maximum level-of-detail pixel threshold.

        Returns:
            str: KML Region XML string.
        """
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
        """
        Create a red center placemark for the search origin.

        Parameters:
            location_name (str): Display name for the center point.
            lat (float): Latitude of the center point.
            lon (float): Longitude of the center point.

        Returns:
            str: KML Placemark XML string.
        """
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
        """
        Convert a single OpenStreetMap element into KML placemarks.

        Each store/location receives two placemarks:
            1. Icon-only placemark when zoomed out
            2. Labeled placemark when zoomed in

        Parameters:
            element (dict): OSM element containing lat, lon, tags, type, and id.

        Returns:
            list[str]: List of KML placemark strings.
        """

        # Extract coordinates from OSM element.
        lat = element.get("lat")
        lon = element.get("lon")

        # Skip elements without coordinates.
        if lat is None or lon is None:
            return []

        # Extract tag dictionary safely.
        tags = element.get("tags", {}) if isinstance(element.get("tags", {}), dict) else {}

        # OSM metadata.
        el_type = element.get("type", "")
        el_id = element.get("id", "")

        # Basic business/store information.
        name = TurboOverpass.safe_get(tags, "name", "")
        shop = TurboOverpass.safe_get(tags, "shop", "")
        amenity = TurboOverpass.safe_get(tags, "amenity", "")
        brand = TurboOverpass.safe_get(tags, "brand", "")
        operator = TurboOverpass.safe_get(tags, "operator", "")
        phone = TurboOverpass.safe_get(tags, "phone", "")
        website = TurboOverpass.safe_get(tags, "website", "")

        # Address-related fields.
        addr_housenumber = TurboOverpass.safe_get(tags, "addr:housenumber", "")
        addr_street = TurboOverpass.safe_get(tags, "addr:street", "")
        addr_city = TurboOverpass.safe_get(tags, "addr:city", "")
        addr_state = TurboOverpass.safe_get(tags, "addr:state", "")
        addr_postcode = TurboOverpass.safe_get(tags, "addr:postcode", "")

        # Use business name when available; otherwise create fallback label.
        display_name = name.strip() or f"{amenity or shop or 'OSM Node'} ({el_type}:{el_id})"

        # Build readable address lines.
        address_line = " ".join(filter(None, [addr_housenumber, addr_street]))
        city_line = ", ".join(filter(None, [addr_city, addr_state, addr_postcode]))
        category = amenity or shop

        description_parts = []

        # Build the HTML description that appears when clicking a placemark.
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

        # Include OSM reference information for traceability.
        description_parts.append(
            f"<b>OSM:</b> {xml_escape(str(el_type))} {xml_escape(str(el_id))}<br/>"
        )

        lat_f = float(lat)
        lon_f = float(lon)
        description = "".join(description_parts)

        # Icon-only placemark shown when zoomed out.
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

        # Labeled placemark shown when zoomed in.
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
        """
        Write a full KML file from OpenStreetMap elements.

        Parameters:
            elements (list[dict]): OSM elements extracted from Overpass.
            kml_out_path (str): Output path for the KML file.
            location_name (str): Name of the center/search location.
            lat (float): Latitude of the center/search location.
            lon (float): Longitude of the center/search location.

        Returns:
            None
        """

        # Start KML with the center point.
        kml_placemarks = [
            cls.center_placemark(location_name, lat, lon)
        ]

        # Add each store/restaurant placemark.
        for element in elements:
            kml_placemarks.extend(cls.element_placemarks(element))

        # KML styles:
        # - centerRed: red pushpin for search center
        # - storeIconOnly: yellow pushpin with no label
        # - storeWithLabel: yellow pushpin with visible label
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

        # Assemble final KML document.
        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <name>5 Mile Radius Merchant Hit List</name>
                {kml_styles}
                {''.join(kml_placemarks)}
            </Document>
        </kml>
        """

        # Ensure output directory exists.
        os.makedirs(os.path.dirname(kml_out_path), exist_ok=True)

        # Replace existing file if present.
        if os.path.exists(kml_out_path):
            os.remove(kml_out_path)

        # Write KML file.
        with open(kml_out_path, "w", encoding="utf-8") as f:
            f.write(kml_content)

        print(f"Saved: {kml_out_path} placemarks: {len(kml_placemarks)}")
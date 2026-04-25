import os
import requests
from xml.sax.saxutils import escape as xml_escape
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


class TurboOverpass:
    
    HEADERS = [
        "osm_type", "osm_id", "name", "lat", "lon",
        "shop", "amenity", "brand", "operator", "phone", "website",
        "addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode",
        "tags_all"
    ]

    @staticmethod
    def fetch_overpass(url, query):
        resp = requests.post(
            url,
            data={"data": query},
            headers={
                "Accept": "application/json",
                "User-Agent": "IFooDBee-Merchant-Identifier/1.0"
            },
            timeout=180
        )

        if not resp.ok:
            print("STATUS:", resp.status_code)
            print("RESPONSE TEXT:")
            print(resp.text)
            resp.raise_for_status()

        return resp.json()

    @staticmethod
    def safe_get(tags, key, default=""):
        return tags.get(key, default)

    @classmethod
    def extract_row(cls, element):
        tags = element.get("tags", {}) if isinstance(element.get("tags", {}), dict) else {}

        tags_all = "; ".join([f"{k}={v}" for k, v in sorted(tags.items())])

        return [
            element.get("type", ""),
            element.get("id", ""),
            cls.safe_get(tags, "name", ""),
            element.get("lat"),
            element.get("lon"),
            cls.safe_get(tags, "shop", ""),
            cls.safe_get(tags, "amenity", ""),
            cls.safe_get(tags, "brand", ""),
            cls.safe_get(tags, "operator", ""),
            cls.safe_get(tags, "phone", ""),
            cls.safe_get(tags, "website", ""),
            cls.safe_get(tags, "addr:housenumber", ""),
            cls.safe_get(tags, "addr:street", ""),
            cls.safe_get(tags, "addr:city", ""),
            cls.safe_get(tags, "addr:state", ""),
            cls.safe_get(tags, "addr:postcode", ""),
            tags_all
        ]

    @classmethod
    def write_excel(cls, elements, out_path):
        wb = Workbook()
        ws = wb.active
        ws.title = "Overpass Results"

        ws.append(cls.HEADERS)

        for element in elements:
            ws.append(cls.extract_row(element))

        ws.freeze_panes = "A2"

        for col_idx, col_name in enumerate(cls.HEADERS, start=1):
            max_len = len(col_name)

            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx, values_only=True):
                val = row[0]
                if val is not None:
                    max_len = max(max_len, len(str(val)))

            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 60)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        if os.path.exists(out_path):
            os.remove(out_path)

        wb.save(out_path)

        print(f"Saved: {out_path} rows: {ws.max_row - 1}")

    @staticmethod
    def fetch_overpass(url, query):
        resp = requests.post(
            url,
            data={"data": query},
            headers={
                "Accept": "application/json",
                "User-Agent": "IFooDBee-Merchant-Identifier/1.0"
            },
            timeout=180
        )

        if not resp.ok:
            print("STATUS:", resp.status_code)
            print("RESPONSE TEXT:")
            print(resp.text)
            resp.raise_for_status()

        return resp.json()

    @staticmethod
    def safe_get(tags, key, default=""):
        return tags.get(key, default)
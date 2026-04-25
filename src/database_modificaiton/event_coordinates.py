import pandas as pd


class EventCoordinateMapper:

    @staticmethod
    def get_coordinates(venue_name, venue_coords):
        venue_name = str(venue_name or "").lower()

        for venue, coords in venue_coords.items():
            if venue.lower() in venue_name or venue_name in venue.lower():
                return coords

        return (None, None)

    @classmethod
    def add_coordinates(
        cls,
        input_file,
        output_file,
        venue_coords
    ):
        df = pd.read_excel(input_file)

        # Apply coordinate lookup
        coords = df["venue"].apply(
            lambda v: cls.get_coordinates(v, venue_coords)
        )

        df["latitude"] = coords.apply(lambda x: x[0])
        df["longitude"] = coords.apply(lambda x: x[1])

        df.to_excel(output_file, index=False)

        print(f"Saved: {output_file}")
        print(f"Rows processed: {len(df)}")

        return df

# Importing Python Libraries
import pandas as pd


class EventCoordinateMapper:
    """
    Event Coordinate Mapping Class

    This class maps event venue names to geographic coordinates
    (latitude and longitude) using a predefined dictionary.

    Key functionality:
    - Match venue names (with flexible string matching)
    - Assign corresponding coordinates to each event
    - Export updated dataset with spatial information

    This is used for:
    - Distance calculations (event ↔ store)
    - GIS visualization
    - Eclat-based proximity analysis
    """

    @staticmethod
    def get_coordinates(venue_name, venue_coords):
        """
        Retrieve coordinates for a given venue name.

        Uses partial string matching to handle variations in naming.

        Parameters:
            venue_name (str): Venue name from event dataset
            venue_coords (dict): Dictionary mapping venue names to (lat, lon)

        Returns:
            tuple: (latitude, longitude) or (None, None) if not found
        """

        # Normalize venue name for case-insensitive comparison
        venue_name = str(venue_name or "").lower()

        # Iterate through known venues and attempt match
        for venue, coords in venue_coords.items():
            if venue.lower() in venue_name or venue_name in venue.lower():
                return coords

        # Return None if no match found
        return (None, None)

    @classmethod
    def add_coordinates(
        cls,
        input_file,
        output_file,
        venue_coords
    ):
        """
        Add latitude and longitude columns to event dataset.

        Parameters:
            input_file (str): Path to input event dataset (Excel)
            output_file (str): Path to save updated dataset
            venue_coords (dict): Mapping of venue names to coordinates

        Returns:
            pandas.DataFrame: Updated DataFrame with coordinates
        """

        # Load event dataset
        df = pd.read_excel(input_file)

        # Map each venue to its coordinates
        coords = df["venue"].apply(
            lambda v: cls.get_coordinates(v, venue_coords)
        )

        # Split coordinate tuples into columns
        df["latitude"] = coords.apply(lambda x: x[0])
        df["longitude"] = coords.apply(lambda x: x[1])


        # Save updated dataset
        df.to_excel(output_file, index=False)

        # Print summary
        print(f"Saved: {output_file}")
        print(f"Rows processed: {len(df)}")

        return df
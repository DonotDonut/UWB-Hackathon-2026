
# Importing Python Libraries
import random
import pandas as pd
import os


class EmployeeGenerator:
    """
    Employee Dataset Generator Class

    This class generates a synthetic employee dataset based on
    store/location data. It assigns employees to each store
    with randomized roles, availability, and schedules.

    Key features:
    - Ensures exactly one Store Manager per store
    - Generates additional staff with randomized attributes
    - Outputs structured employee dataset to Excel

    This dataset is used for:
    - Workforce scheduling analysis
    - Eclat algorithm input (pattern mining)
    """

    @staticmethod
    def generate_employee_sheet(
        input_store_file,
        output_file,
        positions,
        availability,
        schedules,
        people_per_store
    ):
        """
        Generate employee dataset and save to Excel.

        Parameters:
            input_store_file (str): Path to store dataset (Excel)
            output_file (str): Path to save generated employee dataset
            positions (list[str]): List of employee positions
            availability (list[str]): List of availability types
            schedules (list[str]): List of work schedules
            people_per_store (int): Number of employees per store

        Returns:
            pandas.DataFrame: Generated employee dataset
        """

        # Load store dataset
        stores_df = pd.read_excel(input_store_file)

        # Exclude Store Manager from random position assignment
        non_manager_positions = [
            position for position in positions
            if position != "Store Manager"
        ]

        rows = []
        employee_id = 1  # Unique identifier for each employee

        # Iterate through each store/location
        for _, store in stores_df.iterrows():

            # Assign exactly ONE Store Manager per store
            rows.append({
                "Employee ID": employee_id,
                "OSM ID": store["osm_id"],
                "Store Name": store["name"],
                "Latitude": store["lat"],
                "Longitude": store["lon"],
                "Position": "Store Manager",
                "Staff Availability": "Full-time",  # Managers assumed full-time
                "Current Work Schedule": random.choice(schedules),
            })
            employee_id += 1

            # 
            # Generate remaining employees
            # 
            for _ in range(people_per_store - 1):
                rows.append({
                    "Employee ID": employee_id,
                    "OSM ID": store["osm_id"],
                    "Store Name": store["name"],
                    "Latitude": store["lat"],
                    "Longitude": store["lon"],
                    "Position": random.choice(non_manager_positions),
                    "Staff Availability": random.choice(availability),
                    "Current Work Schedule": random.choice(schedules),
                })
                employee_id += 1

        # Convert list of dictionaries into DataFrame
        df = pd.DataFrame(rows)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Save dataset to Excel file
        df.to_excel(output_file, index=False)

        # Print summary information
        print(f"Saved: {output_file}")
        print(f"Total Employees: {len(df)}")

        return df
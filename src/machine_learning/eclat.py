import pandas as pd
from itertools import combinations
from math import radians, sin, cos, sqrt, atan2


class EclatScheduleSuggestion:

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        radius_miles = 3958.8

        lat1, lon1, lat2, lon2 = map(
            radians,
            [lat1, lon1, lat2, lon2]
        )

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return radius_miles * c

    @staticmethod
    def build_transactions(employee_df, store_df, event_df, radius_miles=1.0):
        transactions = []

        for _, event in event_df.iterrows():
            for _, store in store_df.iterrows():

                distance = EclatScheduleSuggestion.haversine_distance(
                    event["latitude"],
                    event["longitude"],
                    store["lat"],
                    store["lon"]
                )

                if distance <= radius_miles:
                    store_employees = employee_df[
                        employee_df["OSM ID"] == store["osm_id"]
                    ]

                    for _, employee in store_employees.iterrows():
                        transaction = {
                            f"event_rank={event['crowd_rank']}",
                            f"venue={event['venue']}",
                            f"store={store['name']}",
                            f"position={employee['Position']}",
                            f"availability={employee['Staff Availability']}",
                            f"schedule={employee['Current Work Schedule']}",
                        }

                        transactions.append(transaction)

        return transactions

    @staticmethod
    def run_eclat(transactions, min_support=3):
        item_tidsets = {}

        for tid, transaction in enumerate(transactions):
            for item in transaction:
                if item not in item_tidsets:
                    item_tidsets[item] = set()
                item_tidsets[item].add(tid)

        frequent_itemsets = {}

        def eclat(prefix, items):
            while items:
                item, tids = items.pop(0)
                new_itemset = prefix + [item]

                support = len(tids)

                if support >= min_support:
                    frequent_itemsets[tuple(new_itemset)] = support

                    suffix = []
                    for other_item, other_tids in items:
                        intersection = tids & other_tids
                        if len(intersection) >= min_support:
                            suffix.append((other_item, intersection))

                    eclat(new_itemset, suffix)

        sorted_items = sorted(item_tidsets.items(), key=lambda x: len(x[1]), reverse=True)
        eclat([], sorted_items)

        return frequent_itemsets

    @staticmethod
    def create_schedule_suggestions(employee_df, store_df, event_df, radius_miles=1.0):
        suggestions = []

        for _, event in event_df.iterrows():
            for _, store in store_df.iterrows():

                distance = EclatScheduleSuggestion.haversine_distance(
                    event["latitude"],
                    event["longitude"],
                    store["lat"],
                    store["lon"]
                )

                if distance <= radius_miles:
                    employees = employee_df[
                        employee_df["OSM ID"] == store["osm_id"]
                    ]

                    capacity = store["estimated_store_capacity"]
                    event_size = event["estimated_event_size"]

                    if event["crowd_rank"] in ["High", "Very High"]:
                        recommended_staff = max(3, int(capacity / 25))
                    elif event["crowd_rank"] == "Medium":
                        recommended_staff = max(2, int(capacity / 35))
                    else:
                        recommended_staff = max(1, int(capacity / 50))

                    available_employees = employees[
                        employees["Staff Availability"].isin(
                            ["Full-time", "Flexible", "Evenings", "Weekends"]
                        )
                    ]

                    selected = available_employees.head(recommended_staff)

                    for _, employee in selected.iterrows():
                        suggestions.append({
                            "event_name": event["event_name"],
                            "event_date": event["date"],
                            "event_time": event["time"],
                            "venue": event["venue"],
                            "crowd_rank": event["crowd_rank"],
                            "store_name": store["name"],
                            "distance_to_event_miles": round(distance, 2),
                            "employee_id": employee["Employee ID"],
                            "position": employee["Position"],
                            "current_schedule": employee["Current Work Schedule"],
                            "availability": employee["Staff Availability"],
                            "suggested_action": "Schedule during event window",
                            "recommended_staff_for_store": recommended_staff,
                        })

        return pd.DataFrame(suggestions)

    @classmethod
    def process(
        cls,
        employee_file,
        store_file,
        event_file,
        output_file,
        radius_miles=1.0,
        min_support=3
    ):
        employee_df = pd.read_excel(employee_file)
        store_df = pd.read_excel(store_file)
        event_df = pd.read_excel(event_file)

        transactions = cls.build_transactions(
            employee_df,
            store_df,
            event_df,
            radius_miles=radius_miles
        )

        frequent_itemsets = cls.run_eclat(
            transactions,
            min_support=min_support
        )

        suggestions_df = cls.create_schedule_suggestions(
            employee_df,
            store_df,
            event_df,
            radius_miles=radius_miles
        )

        frequent_df = pd.DataFrame([
            {
                "itemset": ", ".join(itemset),
                "support": support
            }
            for itemset, support in frequent_itemsets.items()
        ])

        with pd.ExcelWriter(output_file) as writer:
            suggestions_df.to_excel(writer, sheet_name="Schedule Suggestions", index=False)
            frequent_df.to_excel(writer, sheet_name="Eclat Frequent Patterns", index=False)

        print(f"Saved: {output_file}")
        print(f"Suggestions Created: {len(suggestions_df)}")
        print(f"Frequent Patterns Found: {len(frequent_df)}")

        return suggestions_df, frequent_df
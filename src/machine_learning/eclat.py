# Importing Python Libraries
import pandas as pd
from math import radians, sin, cos, sqrt, atan2


class EclatScheduleSuggestion:
    """
    Eclat-Based Workforce Scheduling Class

    This class implements:
    1. Distance calculation between events and stores
    2. Transaction building for Eclat algorithm
    3. Eclat frequent itemset mining
    4. Schedule recommendation generation
    5. End-to-end pipeline processing

    The goal is to identify staffing patterns and generate
    scheduling suggestions based on nearby events and store capacity.
    """

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between two geographic points using the
        Haversine formula.

        Parameters:
            lat1, lon1 (float): Coordinates of first location
            lat2, lon2 (float): Coordinates of second location

        Returns:
            float: Distance in miles
        """

        radius_miles = 3958.8  # Earth radius in miles

        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(
            radians,
            [lat1, lon1, lat2, lon2]
        )

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return radius_miles * c

    @staticmethod
    def build_transactions(employee_df, store_df, event_df, radius_miles=1.0):
        """
        Build transaction dataset for Eclat algorithm.

        Each transaction represents a relationship between:
        - Event characteristics
        - Store location
        - Employee attributes

        Only stores within a specified radius of an event are considered.

        Returns:
            list[set]: Transaction dataset
        """

        transactions = []

        # Iterate through each event and store combination
        for _, event in event_df.iterrows():
            for _, store in store_df.iterrows():

                # Calculate distance between event and store
                distance = EclatScheduleSuggestion.haversine_distance(
                    event["latitude"],
                    event["longitude"],
                    store["lat"],
                    store["lon"]
                )

                # Only include nearby stores
                if distance <= radius_miles:
                    store_employees = employee_df[
                        employee_df["OSM ID"] == store["osm_id"]
                    ]

                    # Create transactions for each employee
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
        """
        Execute Eclat algorithm to find frequent itemsets.

        Parameters:
            transactions (list[set]): Transaction dataset
            min_support (int): Minimum support threshold

        Returns:
            dict: Frequent itemsets with support counts
        """

        # Step 1: Build vertical data format (item -> transaction IDs)
        item_tidsets = {}

        for tid, transaction in enumerate(transactions):
            for item in transaction:
                if item not in item_tidsets:
                    item_tidsets[item] = set()
                item_tidsets[item].add(tid)

        frequent_itemsets = {}

        # Recursive Eclat function
        def eclat(prefix, items):
            while items:
                item, tids = items.pop(0)
                new_itemset = prefix + [item]

                support = len(tids)

                # Check support threshold
                if support >= min_support:
                    frequent_itemsets[tuple(new_itemset)] = support

                    # Build suffix for recursion
                    suffix = []
                    for other_item, other_tids in items:
                        intersection = tids & other_tids
                        if len(intersection) >= min_support:
                            suffix.append((other_item, intersection))

                    # Recursive call
                    eclat(new_itemset, suffix)

        # Sort items by support (descending)
        sorted_items = sorted(
            item_tidsets.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        eclat([], sorted_items)

        return frequent_itemsets

    @staticmethod
    def create_schedule_suggestions(employee_df, store_df, event_df, radius_miles=1.0):
        """
        Generate staffing recommendations based on:
        - Event crowd level
        - Store capacity
        - Employee availability

        Returns:
            pandas.DataFrame: Suggested scheduling assignments
        """

        suggestions = []

        for _, event in event_df.iterrows():
            for _, store in store_df.iterrows():

                # Compute distance
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

                    # Determine staffing needs based on crowd level
                    if event["crowd_rank"] in ["High", "Very High"]:
                        recommended_staff = max(3, int(capacity / 25))
                    elif event["crowd_rank"] == "Medium":
                        recommended_staff = max(2, int(capacity / 35))
                    else:
                        recommended_staff = max(1, int(capacity / 50))

                    # Filter employees by availability
                    available_employees = employees[
                        employees["Staff Availability"].isin(
                            ["Full-time", "Flexible", "Evenings", "Weekends"]
                        )
                    ]

                    # Select top available employees
                    selected = available_employees.head(recommended_staff)

                    # Create suggestion records
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
        radius_miles,
        min_support,
        min_confidence,
        min_lift,
        max_pattern_length,
        focus_maximal_patterns
    ):
        # Load datasets
        employee_df = pd.read_excel(employee_file)
        store_df = pd.read_excel(store_file)
        event_df = pd.read_excel(event_file)

        # Build transactions
        transactions = cls.build_transactions(
            employee_df,
            store_df,
            event_df,
            radius_miles=radius_miles
        )

        # Run Eclat
        frequent_itemsets = cls.run_eclat(
            transactions,
            min_support=min_support
        )

        # Limit pattern length before optional maximal filtering
        frequent_itemsets = {
            itemset: support
            for itemset, support in frequent_itemsets.items()
            if len(itemset) <= max_pattern_length
        }

        # Keep only maximal patterns if enabled
        if focus_maximal_patterns:
            frequent_itemsets = cls.filter_maximal_patterns(frequent_itemsets)

        # Generate association rules after frequent itemsets exist
        rules_df = cls.generate_association_rules(
            frequent_itemsets=frequent_itemsets,
            transaction_count=len(transactions),
            min_confidence=min_confidence,
            min_lift=min_lift
        )

        # Generate schedule suggestions
        suggestions_df = cls.create_schedule_suggestions(
            employee_df,
            store_df,
            event_df,
            radius_miles=radius_miles
        )

        # Convert frequent patterns to DataFrame
        frequent_df = pd.DataFrame([
            {
                "itemset": ", ".join(itemset),
                "support": support,
                "pattern_length": len(itemset)
            }
            for itemset, support in frequent_itemsets.items()
        ])

        # Save results
        with pd.ExcelWriter(output_file) as writer:
            suggestions_df.to_excel(writer, sheet_name="Schedule Suggestions", index=False)
            frequent_df.to_excel(writer, sheet_name="Eclat Frequent Patterns", index=False)
            rules_df.to_excel(writer, sheet_name="Association Rules", index=False)

        print(f"Saved: {output_file}")
        print(f"Suggestions Created: {len(suggestions_df)}")
        print(f"Frequent Patterns Found: {len(frequent_df)}")
        print(f"Association Rules Found: {len(rules_df)}")

        return suggestions_df, frequent_df, rules_df
    
    @staticmethod
    def generate_association_rules(frequent_itemsets, transaction_count, min_confidence=0.7, min_lift=1.2):
        rules = []

        support_lookup = {
            itemset: support for itemset, support in frequent_itemsets.items()
        }

        for itemset, itemset_support in frequent_itemsets.items():
            itemset = tuple(itemset)

            if len(itemset) < 2:
                continue

            items = list(itemset)

            for i in range(1, len(items)):
                from itertools import combinations

                for antecedent in combinations(items, i):
                    antecedent = tuple(antecedent)
                    consequent = tuple(item for item in items if item not in antecedent)

                    antecedent_support = support_lookup.get(antecedent)
                    consequent_support = support_lookup.get(consequent)

                    if not antecedent_support or not consequent_support:
                        continue

                    confidence = itemset_support / antecedent_support
                    lift = confidence / (consequent_support / transaction_count)

                    if confidence >= min_confidence and lift >= min_lift:
                        rules.append({
                            "antecedent": ", ".join(antecedent),
                            "consequent": ", ".join(consequent),
                            "support": itemset_support,
                            "confidence": round(confidence, 4),
                            "lift": round(lift, 4),
                        })

        return pd.DataFrame(rules)
    
    @staticmethod
    def filter_maximal_patterns(frequent_itemsets):
        itemsets = list(frequent_itemsets.keys())
        maximal_itemsets = {}

        for itemset in itemsets:
            itemset_set = set(itemset)

            is_subset = False
            for other_itemset in itemsets:
                other_set = set(other_itemset)

                if itemset_set < other_set:
                    is_subset = True
                    break

            if not is_subset:
                maximal_itemsets[itemset] = frequent_itemsets[itemset]

        return maximal_itemsets
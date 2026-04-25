# Importing Python Libraries
import random


class ResturantCapacityEstimator:
    """
    Restaurant Capacity Estimation Class

    This class provides a heuristic-based method to estimate
    the seating/customer capacity of restaurants based on
    their name and inferred category.

    Since exact capacity data is not available from OSM/Overpass,
    this approach uses keyword classification and randomized
    ranges to simulate realistic capacity values.

    Use cases:
    - Workforce planning
    - Demand estimation
    - Event impact analysis
    """

    @staticmethod
    def estimate_capacity(store_name):
        """
        Estimate the capacity of a restaurant/store.

        The method classifies the store based on keywords
        in its name and assigns a capacity range accordingly.

        Parameters:
            store_name (str): Name of the store/restaurant

        Returns:
            int: Estimated capacity (randomized within category range)
        """

        # Normalize store name for case-insensitive matching
        name = str(store_name or "").lower()

        # Coffee shops / cafes (small seating capacity)
        if any(k in name for k in ["coffee", "espresso", "cafe", "bakery", "tea"]):
            return random.randint(20, 50)

        # Dessert / ice cream shops (small footprint, quick turnover)
        if any(k in name for k in ["ice cream", "gelato", "dessert", "donut", "cookie"]):
            return random.randint(15, 40)

        # Fast food chains (moderate capacity, high turnover)
        if any(k in name for k in ["mcdonald", "subway", "chipotle", "kfc", "taco bell", "domino"]):
            return random.randint(30, 80)

        # Bars / pubs (larger capacity due to seating + standing)
        if any(k in name for k in ["bar", "tavern", "lounge", "pub"]):
            return random.randint(60, 150)

        # Breweries / large venues (highest capacity category)
        if any(k in name for k in ["brew", "public house", "taproom"]):
            return random.randint(120, 300)

        # Default: general restaurants
        return random.randint(50, 120)
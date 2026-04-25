# Importing Python Libraries
import random
import pandas as pd
import matplotlib.pyplot as plt

from machine_learning.eclat import EclatScheduleSuggestion


class EclatTest:
    """
    Eclat Validation and Testing Class

    This class validates the output of the Eclat scheduling model.

    It creates:
    - validation summary metrics
    - top frequent pattern reports
    - schedule suggestion summaries
    - train/test split comparisons
    - Excel validation workbooks
    - graph outputs for visual analysis

    This class is used after the EclatScheduleSuggestion model
    generates frequent patterns and schedule recommendations.
    """

    @staticmethod
    def validate_eclat_results(
        frequent_df,
        suggestions_df,
        output_prefix="output data/eclat_validation"
    ):
        """
        Validate final Eclat model outputs.

        Parameters:
            frequent_df (pandas.DataFrame): DataFrame containing Eclat frequent itemsets
            suggestions_df (pandas.DataFrame): DataFrame containing schedule suggestions
            output_prefix (str): Output path prefix for Excel and plot files

        Returns:
            pandas.DataFrame: Summary validation metrics
        """

        # Create high-level validation summary metrics.
        validation_summary = {
            "total_frequent_patterns": len(frequent_df),
            "total_schedule_suggestions": len(suggestions_df),
            "unique_events": suggestions_df["event_name"].nunique(),
            "unique_stores": suggestions_df["store_name"].nunique(),
            "unique_employees": suggestions_df["employee_id"].nunique(),
            "avg_distance_to_event": suggestions_df["distance_to_event_miles"].mean(),
        }

        summary_df = pd.DataFrame(
            list(validation_summary.items()),
            columns=["Metric", "Value"]
        )

        # Select the top frequent Eclat patterns based on support count.
        top_patterns = frequent_df.sort_values(
            by="support",
            ascending=False
        ).head(15)

        # Count how many schedule suggestions were generated per crowd rank.
        crowd_rank_counts = suggestions_df["crowd_rank"].value_counts().reset_index()
        crowd_rank_counts.columns = ["crowd_rank", "suggestion_count"]

        # Count how many schedule suggestions were generated per employee position.
        position_counts = suggestions_df["position"].value_counts().reset_index()
        position_counts.columns = ["position", "suggestion_count"]

        # Save validation metrics and summaries to Excel.
        excel_output = f"{output_prefix}.xlsx"

        with pd.ExcelWriter(excel_output) as writer:
            summary_df.to_excel(writer, sheet_name="Validation Summary", index=False)
            top_patterns.to_excel(writer, sheet_name="Top Eclat Patterns", index=False)
            crowd_rank_counts.to_excel(writer, sheet_name="By Crowd Rank", index=False)
            position_counts.to_excel(writer, sheet_name="By Position", index=False)

        print(f"Saved validation workbook: {excel_output}")

        # Plot the top frequent Eclat patterns.
        plt.figure(figsize=(12, 6))
        plt.barh(top_patterns["itemset"], top_patterns["support"])
        plt.xlabel("Support Count")
        plt.ylabel("Frequent Pattern")
        plt.title("Top Eclat Frequent Patterns")
        plt.gca().invert_yaxis()
        plt.tight_layout()

        pattern_plot = f"{output_prefix}_top_patterns.png"
        plt.savefig(pattern_plot)
        plt.close()

        # Plot schedule suggestions grouped by event crowd rank.
        plt.figure(figsize=(8, 5))
        plt.bar(crowd_rank_counts["crowd_rank"], crowd_rank_counts["suggestion_count"])
        plt.xlabel("Crowd Rank")
        plt.ylabel("Schedule Suggestions")
        plt.title("Schedule Suggestions by Crowd Rank")
        plt.tight_layout()

        crowd_plot = f"{output_prefix}_crowd_rank.png"
        plt.savefig(crowd_plot)
        plt.close()

        # Plot schedule suggestions grouped by employee position.
        plt.figure(figsize=(10, 5))
        plt.bar(position_counts["position"], position_counts["suggestion_count"])
        plt.xlabel("Position")
        plt.ylabel("Schedule Suggestions")
        plt.title("Schedule Suggestions by Position")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        position_plot = f"{output_prefix}_position.png"
        plt.savefig(position_plot)
        plt.close()

        print("Saved plots:")
        print(pattern_plot)
        print(crowd_plot)
        print(position_plot)

        return summary_df

    @staticmethod
    def validate_train_test_patterns(
        transactions,
        min_support=3,
        test_size=0.30,
        output_prefix="output data/eclat_train_test_validation"
    ):
        """
        Validate Eclat pattern stability using train/test split.

        The transaction dataset is randomly split into training and
        testing datasets. Eclat is then run separately on each dataset.

        The method compares:
        - number of training frequent patterns
        - number of testing frequent patterns
        - overlapping patterns between train and test
        - pattern overlap rate

        Parameters:
            transactions (list[set]): Transaction dataset used by Eclat
            min_support (int): Minimum support threshold for frequent patterns
            test_size (float): Portion of transactions used for testing
            output_prefix (str): Output path prefix for Excel and plot files

        Returns:
            tuple: summary_df, comparison_df, train_df, test_df
        """

        # Copy transactions to avoid modifying the original list.
        transactions = transactions.copy()

        # Randomize transaction order before splitting.
        random.shuffle(transactions)

        # Compute split index based on requested test size.
        split_index = int(len(transactions) * (1 - test_size))

        # Create training and testing transaction sets.
        train_transactions = transactions[:split_index]
        test_transactions = transactions[split_index:]

        # Run Eclat on training transactions.
        train_patterns = EclatScheduleSuggestion.run_eclat(
            train_transactions,
            min_support=min_support
        )

        # Run Eclat on testing transactions.
        test_patterns = EclatScheduleSuggestion.run_eclat(
            test_transactions,
            min_support=min_support
        )

        # Convert pattern keys to sets for overlap comparison.
        train_set = set(train_patterns.keys())
        test_set = set(test_patterns.keys())

        # Identify patterns that appear in both training and testing results.
        overlapping_patterns = train_set & test_set

        # Build summary metrics for train/test validation.
        summary_df = pd.DataFrame([
            {"Metric": "Train Transactions", "Value": len(train_transactions)},
            {"Metric": "Test Transactions", "Value": len(test_transactions)},
            {"Metric": "Train Frequent Patterns", "Value": len(train_patterns)},
            {"Metric": "Test Frequent Patterns", "Value": len(test_patterns)},
            {"Metric": "Overlapping Patterns", "Value": len(overlapping_patterns)},
            {
                "Metric": "Pattern Overlap Rate",
                "Value": round(len(overlapping_patterns) / len(train_set), 4)
                if len(train_set) > 0 else 0
            }
        ])

        # Prepare compact comparison table for plotting.
        comparison_df = pd.DataFrame([
            {"Dataset": "Train", "Frequent Pattern Count": len(train_patterns)},
            {"Dataset": "Test", "Frequent Pattern Count": len(test_patterns)},
            {"Dataset": "Overlap", "Frequent Pattern Count": len(overlapping_patterns)}
        ])

        # Export raw training transactions for manual inspection.
        train_df = pd.DataFrame([
            {
                "transaction_id": i + 1,
                "items": ", ".join(sorted(transaction))
            }
            for i, transaction in enumerate(train_transactions)
        ])

        # Export raw testing transactions for manual inspection.
        test_df = pd.DataFrame([
            {
                "transaction_id": i + 1,
                "items": ", ".join(sorted(transaction))
            }
            for i, transaction in enumerate(test_transactions)
        ])

        # Convert training frequent patterns into tabular format.
        train_patterns_df = pd.DataFrame([
            {
                "itemset": ", ".join(itemset),
                "support": support
            }
            for itemset, support in train_patterns.items()
        ])

        # Convert testing frequent patterns into tabular format.
        test_patterns_df = pd.DataFrame([
            {
                "itemset": ", ".join(itemset),
                "support": support
            }
            for itemset, support in test_patterns.items()
        ])

        # Save all train/test validation outputs to Excel.
        excel_output = f"{output_prefix}.xlsx"

        with pd.ExcelWriter(excel_output) as writer:
            summary_df.to_excel(writer, sheet_name="Train Test Summary", index=False)
            comparison_df.to_excel(writer, sheet_name="Pattern Comparison", index=False)
            train_df.to_excel(writer, sheet_name="Training Transactions", index=False)
            test_df.to_excel(writer, sheet_name="Testing Transactions", index=False)
            train_patterns_df.to_excel(writer, sheet_name="Train Patterns", index=False)
            test_patterns_df.to_excel(writer, sheet_name="Test Patterns", index=False)

        # Plot train/test/overlap frequent pattern comparison.
        plt.figure(figsize=(8, 5))
        plt.bar(
            comparison_df["Dataset"],
            comparison_df["Frequent Pattern Count"]
        )
        plt.xlabel("Dataset")
        plt.ylabel("Frequent Pattern Count")
        plt.title("Eclat Train vs Test Pattern Comparison")
        plt.tight_layout()

        plot_output = f"{output_prefix}_comparison.png"
        plt.savefig(plot_output)
        plt.close()

        print(f"Saved train/test validation workbook: {excel_output}")
        print(f"Saved train/test comparison plot: {plot_output}")

        return summary_df, comparison_df, train_df, test_df
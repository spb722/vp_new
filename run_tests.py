import json
import time

from pipeline import run_pipeline_debug

hard_test_cases = [
    {
        "name": "A. MAX + attribute + duration + month window",
        "input": "Maximum data usage among smartphone subscribers who have been active on the network for more than 65 days over the past 3 months.",
        "expected_capability": "MAX seed + attribute_filter + duration_threshold",
        "should_work_now": True
    },
    {
        "name": "B. SUM + count constraint",
        "input": "Total revenue from outgoing international SMS in the last 30 days where count of bundled SMS equals 2",
        "expected_capability": "SUM seed + count_constraint",
        "should_work_now": True
    },
    {
        "name": "C. Average monthly formula",
        "input": "Average monthly revenue from bundled data usage within the local network for smartphone users in the last 2 months.",
        "expected_capability": "FORMULA average_over_period + attribute_filter + MONTHS",
        "should_work_now": "maybe"
    },
    {
        "name": "D. Average weekly formula",
        "input": "To check the average weekly outgoing call revenue of a customer over the past 4 weeks.",
        "expected_capability": "FORMULA average_over_period + WEEKS",
        "should_work_now": "maybe"
    },
    {
        "name": "E. Percentage formula",
        "input": "customers whose calculated 20% of the recharge amount is greater than a specified value",
        "expected_capability": "FORMULA percentage_of_kpi",
        "should_work_now": "partial"
    },
    {
        "name": "F. Completed months bounded window",
        "input": "Total revenue from free data usage for smartphone users in the last 2 completed months.",
        "expected_capability": "SUM + MONTHS + bounded completed-period window",
        "should_work_now": "maybe_or_gap"
    },
    {
        "name": "G. Multiple attribute filters",
        "input": "Revenue from free data usage for Indian iPhone users in the last 2 weeks.",
        "expected_capability": "attribute_filter nationality + handset + SUM/RAW + WEEKS",
        "should_work_now": "maybe"
    },
    {
        "name": "H. Product presence list",
        "input": "select customers who purchased product 123 or product 125 in the last month.",
        "expected_capability": "product attribute/list + COUNT_ALL presence + time window",
        "should_work_now": "partial"
    },
    {
        "name": "I. Parameterized X days",
        "input": "Subscribers who did not receive a promotion in the last X days.",
        "expected_capability": "parameterized seed using X days",
        "should_work_now": "likely_gap"
    },
    {
        "name": "J. Group by product",
        "input": "Find total recharge revenue in the last 30 days grouped by recharge type.",
        "expected_capability": "GROUP BY style seed or grouped aggregation",
        "should_work_now": "likely_gap"
    },
    {
        "name": "K. Group by handset type",
        "input": "Find the number of customers grouped by handset type.",
        "expected_capability": "COUNT_ALL + group by Profile_Cdr_Handset_Type",
        "should_work_now": "likely_gap"
    },
    {
        "name": "L. Presence/absence campaign",
        "input": "Subscribers who did not receive any promotion in the last 7 days.",
        "expected_capability": "campaign absence COUNT_ALL = 0",
        "should_work_now": "likely_gap_in_current_clean_pipeline"
    }
]

rerun_cases = [
    "Average monthly revenue from bundled data usage within the local network for smartphone users in the last 2 months.",
    "To check the average weekly outgoing call revenue of a customer over the past 4 weeks.",
    "customers whose calculated 20% of the recharge amount is greater than a specified value",
    "Revenue from free data usage for Indian nationality  iPhone users in the last 2 weeks.",
    "select customers who purchased product 123 or product 125 in the last month.",
    "Subscribers who did not receive a promotion in the last X days.",
    "Find total recharge revenue in the last 30 days grouped by recharge type.",
    "Find the number of customers grouped by handset type.",
    "Subscribers who did not receive any promotion in the last 7 days."
]


if __name__ == "__main__":
    for case in hard_test_cases:

        print("=" * 120)
        print(case["name"])
        print("INPUT:", case["input"])
        print("EXPECTED CAPABILITY:", case["expected_capability"])
        print("SHOULD WORK NOW:", case["should_work_now"])
        print("-" * 120)

        result = run_pipeline_debug(case["input"], client_name=None)

        print("FEATURES:")
        print(json.dumps(result["features"], indent=2))

        print("\nCANDIDATES:")
        print(json.dumps(result["candidates"], indent=2))

        print("\nDECISION:")
        print(json.dumps(result["decision"], indent=2))

        if result["selected_seed_id"]:
            print("\nSELECTED SEED:", result["selected_seed_id"])

        if result["kpi_mapping"]:
            print("\nKPI MAPPING:")
            print(json.dumps({
                "matched": result["kpi_mapping"]["matched"],
                "input": result["kpi_mapping"]["input"],
                "kpi_col": result["kpi_mapping"]["kpi_col"],
                "table_name": result["kpi_mapping"]["table_name"],
                "datatype": result["kpi_mapping"]["datatype"]
            }, indent=2))

        if result["rendered_seed_condition"]:
            print("\nRENDERED SEED CONDITION:")
            print(result["rendered_seed_condition"])

        if result["final_parent_condition"]:
            print("\nFINAL PARENT CONDITION:")
            print(result["final_parent_condition"])

        if result["error"]:
            print("\nERROR:")
            print(result["error"])
        time.sleep(60)

    for example in rerun_cases:
        print("=" * 120)
        print(example)
        print("-" * 120)

        result = run_pipeline_debug(example, client_name=None)

        print("FEATURES:")
        print(json.dumps(result["features"], indent=2))

        print("\nCANDIDATES:")
        print(json.dumps(result["candidates"], indent=2))

        print("\nDECISION:")
        print(json.dumps(result["decision"], indent=2))

        if result["selected_seed_id"]:
            print("\nSELECTED SEED:", result["selected_seed_id"])

        if result["kpi_mapping"]:
            print("\nKPI MAPPING:")
            print(json.dumps({
                "matched": result["kpi_mapping"]["matched"],
                "input": result["kpi_mapping"]["input"],
                "kpi_col": result["kpi_mapping"]["kpi_col"],
                "table_name": result["kpi_mapping"]["table_name"],
                "datatype": result["kpi_mapping"]["datatype"]
            }, indent=2))

        if result["rendered_seed_condition"]:
            print("\nRENDERED SEED CONDITION:")
            print(result["rendered_seed_condition"])

        if result["final_parent_condition"]:
            print("\nFINAL PARENT CONDITION:")
            print(result["final_parent_condition"])

        if result["error"]:
            print("\nERROR:")
            print(result["error"])

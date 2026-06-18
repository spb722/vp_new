import importlib, graph
from pipeline import reinforce_from_condition
importlib.reload(graph)
from graph import run_vp_graph, explain_result
result = run_vp_graph("customer maximum prepay sms revenue over the last 4 weeks")
explain_result(result)
print(result["features"].get("dynamic_filter_fixed_count"))
print(result["top_candidates"])


# result = reinforce_from_condition(
#     original_input="find the maximum prepay sms revenue of Indian subscribers over the last 4 weeks",
#     parent_condition="COMMON_FCT_DT >= CurrentWeek-4WEEKS AND MAX(COMMON_Prepay_Sms_Revenue) ${operator} ${value}",
#     client_name=None,
# )
#
# print(result)
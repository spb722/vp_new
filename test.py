import importlib, graph
importlib.reload(graph)
from graph import run_vp_graph, explain_result
result = run_vp_graph("Revenue from free data usage for Indian iPhone users in the last 2 weeks.")
explain_result(result)
print(result["features"].get("dynamic_filter_fixed_count"))
print(result["top_candidates"])

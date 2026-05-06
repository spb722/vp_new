from renderer import render_filters


def compose_final_condition(features: dict, rendered_seed_condition: str) -> str:
    filter_conditions = render_filters(features)

    all_conditions = []
    all_conditions.extend(filter_conditions)
    all_conditions.append(rendered_seed_condition)

    return " AND ".join(all_conditions)

import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

TOLERANCE = 0.01


def validate_final_plan(
    hourly_plan: List[Dict[str, Any]],
    hours_data: List[Dict[str, Any]],
    battery_data: Dict[str, Any],
    directives: List[Dict[str, Any]]
) -> None:
    """
    Replays the 24-hour hourly plan to verify all energy balance equations,
    physical battery constraints, and operator directives hold within a 0.01 kWh tolerance.
    Raises ValueError on any failure.
    """
    if len(hourly_plan) != 24:
        raise ValueError(f"Hourly plan must contain exactly 24 entries, got {len(hourly_plan)}")

    seen_hours = set()
    hours_dict = {int(h["hour"]): h for h in hours_data}
    
    capacity = float(battery_data["capacity_kwh"])
    initial_energy = float(battery_data["initial_energy_kwh"])
    base_min_energy = float(battery_data["minimum_energy_kwh"])
    max_charge = float(battery_data["max_charge_kwh_per_hour"])
    max_discharge = float(battery_data["max_discharge_kwh_per_hour"])

    effective_solar = {int(h["hour"]): float(h["solar_kwh"]) for h in hours_data}
    active_minimum = {int(h["hour"]): base_min_energy for h in hours_data}
    max_grid_cap = {int(h["hour"]): None for h in hours_data}
    no_charge_hours = set()
    no_discharge_hours = set()

    for d in directives:
        if not d.get("applies"):
            continue
        dtype = d.get("directive_type")
        adj = d.get("structured_adjustment") or {}
        dhours = adj.get("hours", [])

        if dtype == "solar_reduction":
            factor = float(adj.get("factor", 1.0))
            for h in dhours:
                effective_solar[h] = effective_solar[h] * factor

        elif dtype == "minimum_battery_reserve":
            min_kwh = float(adj.get("minimum_energy_kwh", base_min_energy))
            for h in dhours:
                active_minimum[h] = max(active_minimum[h], min_kwh)

        elif dtype == "no_charge_window":
            for h in dhours:
                no_charge_hours.add(h)

        elif dtype == "no_discharge_window":
            for h in dhours:
                no_discharge_hours.add(h)

        elif dtype == "max_grid_window":
            mg_kwh = float(adj.get("max_grid_kwh", 1e9))
            for h in dhours:
                if max_grid_cap[h] is None:
                    max_grid_cap[h] = mg_kwh
                else:
                    max_grid_cap[h] = min(max_grid_cap[h], mg_kwh)

    prev_energy = initial_energy

    for idx, plan_entry in enumerate(hourly_plan):
        h = plan_entry.get("hour")
        if not isinstance(h, int) or h != idx:
            raise ValueError(f"Hourly plan entry at index {idx} has invalid hour {h}")
        if h in seen_hours:
            raise ValueError(f"Duplicate hour {h} in hourly plan")
        seen_hours.add(h)

        g_kwh = float(plan_entry.get("grid_kwh", 0.0))
        s_kwh = float(plan_entry.get("solar_used_kwh", 0.0))
        action = plan_entry.get("battery_action")
        b_kwh = float(plan_entry.get("battery_kwh", 0.0))
        e_after = float(plan_entry.get("battery_energy_after_kwh", 0.0))

        for val_name, val in [("grid_kwh", g_kwh), ("solar_used_kwh", s_kwh), ("battery_kwh", b_kwh), ("battery_energy_after_kwh", e_after)]:
            if math.isnan(val) or math.isinf(val) or val < -TOLERANCE:
                raise ValueError(f"Hour {h}: {val_name} must be non-negative and finite, got {val}")

        c_kwh = b_kwh if action == "charge" else 0.0
        d_kwh = b_kwh if action == "discharge" else 0.0

        if action == "idle" and b_kwh > TOLERANCE:
            raise ValueError(f"Hour {h}: battery_kwh must be 0 when action is idle, got {b_kwh}")

        demand = float(hours_dict[h]["demand_kwh"])

        # Energy balance check
        supply = g_kwh + s_kwh + d_kwh
        consumption = demand + c_kwh
        if abs(supply - consumption) > TOLERANCE:
            raise ValueError(f"Hour {h}: energy balance violated. Supply ({supply:.4f}) != Consumption ({consumption:.4f})")

        # Solar limit check
        eff_solar = effective_solar[h]
        if s_kwh - eff_solar > TOLERANCE:
            raise ValueError(f"Hour {h}: solar_used_kwh ({s_kwh:.4f}) exceeds effective solar ({eff_solar:.4f})")

        # Rate limits
        if c_kwh - max_charge > TOLERANCE:
            raise ValueError(f"Hour {h}: charge_kwh ({c_kwh:.4f}) exceeds max_charge_rate ({max_charge})")
        if d_kwh - max_discharge > TOLERANCE:
            raise ValueError(f"Hour {h}: discharge_kwh ({d_kwh:.4f}) exceeds max_discharge_rate ({max_discharge})")

        # State transition check
        expected_e_after = prev_energy + c_kwh - d_kwh
        if abs(e_after - expected_e_after) > TOLERANCE:
            raise ValueError(f"Hour {h}: battery transition violated. State after ({e_after:.4f}) != expected ({expected_e_after:.4f})")

        # Battery bounds check
        act_min = active_minimum[h]
        if e_after + TOLERANCE < act_min:
            raise ValueError(f"Hour {h}: battery energy ({e_after:.4f}) below active minimum ({act_min})")
        if e_after - TOLERANCE > capacity:
            raise ValueError(f"Hour {h}: battery energy ({e_after:.4f}) exceeds capacity ({capacity})")

        # Directive checks
        if h in no_charge_hours and c_kwh > TOLERANCE:
            raise ValueError(f"Hour {h}: charging prohibited by no_charge_window directive, but charged {c_kwh:.4f} kWh")
        if h in no_discharge_hours and d_kwh > TOLERANCE:
            raise ValueError(f"Hour {h}: discharging prohibited by no_discharge_window directive, but discharged {d_kwh:.4f} kWh")
        if max_grid_cap[h] is not None and g_kwh - max_grid_cap[h] > TOLERANCE:
            raise ValueError(f"Hour {h}: grid draw ({g_kwh:.4f}) exceeds max_grid_window limit ({max_grid_cap[h]})")

        prev_energy = e_after

    # End-of-day neutrality check
    final_energy = hourly_plan[23]["battery_energy_after_kwh"]
    if abs(final_energy - initial_energy) > TOLERANCE:
        raise ValueError(f"End-of-day neutrality violated. Final energy ({final_energy:.4f}) != Initial energy ({initial_energy:.4f})")


def compute_totals(hourly_plan: List[Dict[str, Any]], hours_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes total grid kWh, total cost in BDT, and peak grid kWh from hourly plan."""
    tariff_map = {int(h["hour"]): float(h["tariff_bdt_per_kwh"]) for h in hours_data}
    
    total_grid_kwh = sum(float(h["grid_kwh"]) for h in hourly_plan)
    total_cost_bdt = sum(float(h["grid_kwh"]) * tariff_map[int(h["hour"])] for h in hourly_plan)
    peak_grid_kwh = max(float(h["grid_kwh"]) for h in hourly_plan)

    return {
        "total_grid_kwh": round(total_grid_kwh, 4),
        "total_cost_bdt": round(total_cost_bdt, 4),
        "peak_grid_kwh": round(peak_grid_kwh, 4)
    }


def generate_plan_summary(
    directives: List[Dict[str, Any]],
    hourly_plan: List[Dict[str, Any]],
    totals: Dict[str, float]
) -> str:
    """Generates a structured human-readable plan summary string."""
    applied_parts = []
    ignored_count = 0

    for d in directives:
        if d.get("applies"):
            dtype = d.get("directive_type")
            explanation = d.get("explanation", "")
            applied_parts.append(f"{dtype} directive ({explanation})")
        else:
            ignored_count += 1

    summary_str = ""
    if applied_parts:
        summary_str += f"Applied {', '.join(applied_parts)}. "
    if ignored_count > 0:
        summary_str += f"Ignored {ignored_count} irrelevant note{'s' if ignored_count > 1 else ''}. "

    has_charge = any(h.get("battery_action") == "charge" for h in hourly_plan)
    has_discharge = any(h.get("battery_action") == "discharge" for h in hourly_plan)

    if has_charge and has_discharge:
        summary_str += "Charged battery during cheap hours, discharged during expensive peak. "
    elif has_charge:
        summary_str += "Charged battery during available windows. "
    elif has_discharge:
        summary_str += "Discharged battery to shave peak demand. "
    else:
        summary_str += "Battery remained idle throughout the day. "

    summary_str += f"Total grid: {totals['total_grid_kwh']} kWh, cost: {totals['total_cost_bdt']} BDT."
    return summary_str

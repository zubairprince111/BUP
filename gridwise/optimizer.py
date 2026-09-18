import os
import logging
from typing import List, Dict, Any, Optional
import pulp



logger = logging.getLogger(__name__)


def optimize_energy_schedule(
    hours_data: List[Dict[str, Any]],
    battery_data: Dict[str, Any],
    directives: List[Dict[str, Any]],
    solver_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Formulates and solves a 24-hour Mixed-Integer Linear Programming (MILP) problem using PuLP and CBC or HiGHS.
    Minimizes total grid electricity purchasing cost subject to energy balance, battery physical limits, rate bounds,
    charge/discharge mutual exclusion (binary variables), end-of-day battery neutrality, and operator directives.
    """
    capacity = float(battery_data["capacity_kwh"])
    initial_energy = float(battery_data["initial_energy_kwh"])
    base_min_energy = float(battery_data["minimum_energy_kwh"])
    max_charge_rate = float(battery_data["max_charge_kwh_per_hour"])
    max_discharge_rate = float(battery_data["max_discharge_kwh_per_hour"])

    effective_solar = {}
    active_minimum = {}
    max_grid_cap = {}
    no_charge_hours = set()
    no_discharge_hours = set()

    for h_entry in hours_data:
        h = int(h_entry["hour"])
        effective_solar[h] = float(h_entry["solar_kwh"])
        active_minimum[h] = base_min_energy
        max_grid_cap[h] = None

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

    # PuLP MILP Problem Setup
    prob = pulp.LpProblem("GridWise_MILP_Energy_Optimization", pulp.LpMinimize)

    grid_kwh = {}
    solar_used_kwh = {}
    charge_kwh = {}
    discharge_kwh = {}
    battery_energy = {}
    is_charge = {}
    is_discharge = {}

    for h_entry in hours_data:
        h = int(h_entry["hour"])
        grid_kwh[h] = pulp.LpVariable(f"grid_kwh_{h}", lowBound=0.0, cat=pulp.LpContinuous)
        solar_used_kwh[h] = pulp.LpVariable(f"solar_used_kwh_{h}", lowBound=0.0, cat=pulp.LpContinuous)
        charge_kwh[h] = pulp.LpVariable(f"charge_kwh_{h}", lowBound=0.0, cat=pulp.LpContinuous)
        discharge_kwh[h] = pulp.LpVariable(f"discharge_kwh_{h}", lowBound=0.0, cat=pulp.LpContinuous)
        battery_energy[h] = pulp.LpVariable(f"battery_energy_{h}", lowBound=active_minimum[h], upBound=capacity, cat=pulp.LpContinuous)
        
        # Binary variables for mutual exclusion
        is_charge[h] = pulp.LpVariable(f"is_charge_{h}", cat=pulp.LpBinary)
        is_discharge[h] = pulp.LpVariable(f"is_discharge_{h}", cat=pulp.LpBinary)

    # Objective Function: Minimize Total Grid Energy Cost (BDT)
    prob += pulp.lpSum([grid_kwh[int(h_entry["hour"])] * float(h_entry["tariff_bdt_per_kwh"]) for h_entry in hours_data])

    # Constraints
    for h_entry in hours_data:
        h = int(h_entry["hour"])
        demand = float(h_entry["demand_kwh"])

        # 1. Energy balance: grid + solar_used + discharge == demand + charge
        prob += (grid_kwh[h] + solar_used_kwh[h] + discharge_kwh[h] == demand + charge_kwh[h], f"EnergyBalance_{h}")

        # 2. Solar limit: solar_used <= effective_solar
        prob += (solar_used_kwh[h] <= effective_solar[h], f"SolarLimit_{h}")

        # 3. Battery state transition: battery_energy[h] == battery_energy[h-1] + charge[h] - discharge[h]
        prev_energy = initial_energy if h == 0 else battery_energy[h - 1]
        prob += (battery_energy[h] == prev_energy + charge_kwh[h] - discharge_kwh[h], f"BatteryTransition_{h}")

        # 4. Charge / discharge rate limits & binary mutual exclusion: is_charge + is_discharge <= 1
        prob += (charge_kwh[h] <= max_charge_rate * is_charge[h], f"MaxCharge_{h}")
        prob += (discharge_kwh[h] <= max_discharge_rate * is_discharge[h], f"MaxDischarge_{h}")
        prob += (is_charge[h] + is_discharge[h] <= 1, f"MutualExclusion_{h}")

        # 5. Directive constraints
        if h in no_charge_hours:
            prob += (charge_kwh[h] == 0.0, f"NoCharge_{h}")

        if h in no_discharge_hours:
            prob += (discharge_kwh[h] == 0.0, f"NoDischarge_{h}")

        if max_grid_cap[h] is not None:
            prob += (grid_kwh[h] <= max_grid_cap[h], f"MaxGrid_{h}")

    # 6. End-of-day neutrality: battery_energy[23] == initial_energy_kwh
    prob += (battery_energy[23] == initial_energy, "EndOfDayNeutrality")

    # Select Solver: HiGHS vs CBC
    if solver_name is None:
        solver_name = os.environ.get("GRIDWISE_SOLVER", "CBC").upper()
    else:
        solver_name = solver_name.upper()

    if solver_name == "HIGHS":
        try:
            solver = pulp.HiGHS(msg=False)
        except Exception as e:
            logger.warning(f"HiGHS solver initialization failed: {e}. Falling back to CBC.")
            solver = pulp.PULP_CBC_CMD(msg=False)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False)

    prob.solve(solver)


    status = pulp.LpStatus[prob.status]
    if status not in ["Optimal", "Feasible"]:
        raise ValueError(f"PuLP MILP solver could not find a feasible energy schedule. Solver status: {status}")

    hourly_plan = []
    for h_entry in hours_data:
        h = int(h_entry["hour"])
        
        g_val = max(0.0, float(grid_kwh[h].varValue or 0.0))
        s_val = max(0.0, float(solar_used_kwh[h].varValue or 0.0))
        c_val = max(0.0, float(charge_kwh[h].varValue or 0.0))
        d_val = max(0.0, float(discharge_kwh[h].varValue or 0.0))
        e_val = max(0.0, float(battery_energy[h].varValue or 0.0))

        if c_val > 0.001:
            action = "charge"
            b_kwh = c_val
        elif d_val > 0.001:
            action = "discharge"
            b_kwh = d_val
        else:
            action = "idle"
            b_kwh = 0.0

        hourly_plan.append({
            "hour": h,
            "grid_kwh": round(g_val, 4),
            "solar_used_kwh": round(s_val, 4),
            "battery_action": action,
            "battery_kwh": round(b_kwh, 4),
            "battery_energy_after_kwh": round(e_val, 4)
        })

    return hourly_plan

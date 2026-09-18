import math
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

SUPPORTED_DIRECTIVE_TYPES = {
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op"
}


def validate_directives(
    directives: List[Dict[str, Any]],
    expected_count: int,
    battery_capacity_kwh: float
) -> List[Dict[str, Any]]:
    """
    Validates LLM directive output deterministically against strict rules.
    If any item fails validation, converts it to no_op (applies=False, structured_adjustment=None)
    and logs a warning. Returns a guaranteed clean list of directive_interpretation objects.
    """
    cleaned_directives = []
    
    if not isinstance(directives, list):
        logger.warning(f"Directives input is not a list ({type(directives)}). Creating fallbacks.")
        directives = []

    seen_indices = set()

    for idx in range(expected_count):
        raw_item = directives[idx] if idx < len(directives) and isinstance(directives[idx], dict) else {}
        
        is_valid, reason = _validate_single_item(raw_item, idx, expected_count, battery_capacity_kwh, seen_indices)
        
        if is_valid:
            seen_indices.add(idx)
            cleaned_directives.append({
                "note_index": idx,
                "applies": bool(raw_item.get("applies")),
                "directive_type": raw_item.get("directive_type"),
                "structured_adjustment": raw_item.get("structured_adjustment"),
                "explanation": str(raw_item.get("explanation", ""))
            })
        else:
            logger.warning(f"Guardrail converted note {idx} to no_op. Reason: {reason}")
            cleaned_directives.append({
                "note_index": idx,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": f"Guardrail fallback to no_op: {reason}"
            })

    return cleaned_directives


def _validate_single_item(
    item: Dict[str, Any],
    expected_idx: int,
    total_count: int,
    battery_capacity_kwh: float,
    seen_indices: set
) -> Tuple[bool, str]:
    """Validates a single directive item."""
    if not item:
        return False, "Item is missing or not a dictionary"

    note_index = item.get("note_index")
    if not isinstance(note_index, int) or isinstance(note_index, bool) or note_index != expected_idx:
        return False, f"note_index must be integer {expected_idx}, got {note_index}"
    if note_index in seen_indices:
        return False, f"Duplicate note_index {note_index}"

    applies = item.get("applies")
    if not isinstance(applies, bool):
        return False, f"applies must be a boolean, got {type(applies).__name__}"

    directive_type = item.get("directive_type")
    if directive_type not in SUPPORTED_DIRECTIVE_TYPES:
        return False, f"Unsupported directive_type: '{directive_type}'"

    structured_adj = item.get("structured_adjustment")

    if directive_type == "no_op":
        if applies is not False:
            return False, "no_op directive must have applies=False"
        if structured_adj is not None:
            return False, "no_op directive must have structured_adjustment=None"
        return True, ""

    # For non-no_op directives
    if applies is not True:
        return False, f"Directive '{directive_type}' must have applies=True"
    if not isinstance(structured_adj, dict):
        return False, f"Directive '{directive_type}' structured_adjustment must be a dictionary"

    # Validate hours array
    hours = structured_adj.get("hours")
    if not isinstance(hours, list):
        return False, "hours must be a list"
    if len(hours) == 0:
        return False, "hours list cannot be empty"
    for h in hours:
        if not isinstance(h, int) or isinstance(h, bool):
            return False, f"All elements in hours must be integers, found {h}"
        if not (0 <= h <= 23):
            return False, f"Hour {h} out of bounds (must be 0-23)"
    if len(hours) != len(set(hours)):
        return False, "hours list contains duplicates"
    if hours != sorted(hours):
        return False, "hours list must be in strictly ascending order"

    # Type-specific validation
    if directive_type == "solar_reduction":
        factor = structured_adj.get("factor")
        if not isinstance(factor, (int, float)) or isinstance(factor, bool):
            return False, "solar_reduction factor must be a number"
        factor = float(factor)
        if math.isnan(factor) or math.isinf(factor) or not (0.0 <= factor <= 1.0):
            return False, f"solar_reduction factor must be float between 0.0 and 1.0 inclusive, got {factor}"
        if set(structured_adj.keys()) != {"hours", "factor"}:
            return False, f"solar_reduction adjustment keys must be exact {{'hours', 'factor'}}, got {set(structured_adj.keys())}"

    elif directive_type == "minimum_battery_reserve":
        min_kwh = structured_adj.get("minimum_energy_kwh")
        if not isinstance(min_kwh, (int, float)) or isinstance(min_kwh, bool):
            return False, "minimum_energy_kwh must be a number"
        min_kwh = float(min_kwh)
        if math.isnan(min_kwh) or math.isinf(min_kwh) or min_kwh < 0 or min_kwh > battery_capacity_kwh:
            return False, f"minimum_energy_kwh must be between 0 and battery capacity ({battery_capacity_kwh}), got {min_kwh}"
        if set(structured_adj.keys()) != {"hours", "minimum_energy_kwh"}:
            return False, f"minimum_battery_reserve adjustment keys must be exact {{'hours', 'minimum_energy_kwh'}}, got {set(structured_adj.keys())}"

    elif directive_type == "no_charge_window":
        if set(structured_adj.keys()) != {"hours"}:
            return False, f"no_charge_window adjustment keys must be exact {{'hours'}}, got {set(structured_adj.keys())}"

    elif directive_type == "no_discharge_window":
        if set(structured_adj.keys()) != {"hours"}:
            return False, f"no_discharge_window adjustment keys must be exact {{'hours'}}, got {set(structured_adj.keys())}"

    elif directive_type == "max_grid_window":
        max_grid = structured_adj.get("max_grid_kwh")
        if not isinstance(max_grid, (int, float)) or isinstance(max_grid, bool):
            return False, "max_grid_kwh must be a number"
        max_grid = float(max_grid)
        if math.isnan(max_grid) or math.isinf(max_grid) or max_grid < 0:
            return False, f"max_grid_kwh must be non-negative finite number, got {max_grid}"
        if set(structured_adj.keys()) != {"hours", "max_grid_kwh"}:
            return False, f"max_grid_window adjustment keys must be exact {{'hours', 'max_grid_kwh'}}, got {set(structured_adj.keys())}"

    return True, ""

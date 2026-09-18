import os
import json
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LLMInterpretationError(Exception):
    """Raised when the LLM service is unavailable, fails retries, or returns invalid output."""
    pass


SYSTEM_PROMPT = """You are an AI assistant for a smart grid energy optimization system.
Your task is to analyze natural language operator notes and interpret them into structured energy schedule directives.

You MUST classify each operator note into EXACTLY ONE of the following 6 supported directive types:

1. solar_reduction: Reductions or limits on rooftop solar output.
   structured_adjustment: {"hours": [int, ...], "factor": float}
   - "hours": unique integers 0-23 sorted ascending representing affected hours.
   - "factor": float between 0.0 and 1.0 representing the REMAINING usable solar fraction (e.g. "80% reduction" -> factor 0.2; "drop to 20%" -> factor 0.2; "25% of forecast" -> factor 0.25).

2. minimum_battery_reserve: Temporary requirement for minimum energy level stored in the battery.
   structured_adjustment: {"hours": [int, ...], "minimum_energy_kwh": float}
   - "hours": unique integers 0-23 sorted ascending.
   - "minimum_energy_kwh": minimum required battery energy in kWh during those hours.

3. no_charge_window: Prohibition against charging the battery during specific hours.
   structured_adjustment: {"hours": [int, ...]}
   - "hours": unique integers 0-23 sorted ascending.

4. no_discharge_window: Prohibition against discharging the battery during specific hours.
   structured_adjustment: {"hours": [int, ...]}
   - "hours": unique integers 0-23 sorted ascending.

5. max_grid_window: Constraint limiting grid draw to a maximum power/energy limit.
   structured_adjustment: {"hours": [int, ...], "max_grid_kwh": float}
   - "hours": unique integers 0-23 sorted ascending.
   - "max_grid_kwh": maximum allowable grid energy draw in kWh per hour.

6. no_op: Irrelevant notes, administrative updates, garbage/nonsense, ambiguous/under-specified notes, or unsupported requests.
   applies: false
   structured_adjustment: null

CRITICAL DIRECTIVE CLASSIFICATION & NO_OP RULES:
- NEVER invent a new or unsupported directive type. You MUST use ONLY one of the 6 listed types above.
- GARBAGE & NONSENSE: Any ungrammatical string, random character sequence (e.g. "asdfghjkl", "xyz 123", "hello hello hello"), or nonsensical phrase ("banana spaceship", "battery pizza moon", "make the grid happy") MUST be classified as no_op (applies: false, structured_adjustment: null).
- IRRELEVANT CAMPUS ACTIVITIES: Any note describing general campus announcements, event schedules, or administrative changes ("cafeteria closes at 8 PM", "football match at 6 PM", "sports office deadline", "library opening hours", "security shift update") MUST be classified as no_op.
- AMBIGUOUS & UNDER-SPECIFIED NOTES: Any note that expresses a vague desire but lacks specific, actionable time windows or required numeric quantities ("Don't use the battery in the afternoon", "Use less power later", "Keep things stable", "Reduce battery usage", "Keep a high battery reserve", "Limit grid usage") MUST NOT have missing values or hours guessed/invented. If time windows or numeric values cannot be derived unambiguously from the text, classify the note as no_op.
- UNSUPPORTED REQUESTS: Any request outside the 5 active directive types ("Turn off the entire campus", "Prioritize Building A", "Run generator at maximum power", "Sell excess electricity") MUST be classified as no_op.

TIME WINDOW RULES:
- Use 0-indexed 24-hour system (0 = 12 AM / midnight to 1 AM, 12 = 12 PM / noon to 1 PM, 23 = 11 PM to 12 AM).
- Time ranges specified as start time to end time are START-INCLUSIVE and END-EXCLUSIVE.
Examples:
  - "noon until 2 PM" -> hours [12, 13]
  - "1 PM to 3 PM" -> hours [13, 14]
  - "2 PM to 4 PM" -> hours [14, 15]
  - "6 PM until 9 PM" -> hours [18, 19, 20]
  - "between 14:00 and 15:00" -> hours [14]
  - "from 22:00 to 00:00" -> hours [22, 23]

RESPONSE FORMAT RULES:
- You MUST return ONLY a JSON object containing a top-level key "directives" which is a JSON array of N objects (where N is the number of notes).
- Schema for each object:
{
  "note_index": int,           // 0-indexed corresponding to the note order
  "applies": boolean,          // true for types 1-5, false for no_op
  "directive_type": string,   // one of: "solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window", "no_op"
  "structured_adjustment": dict | null, // schema matching directive_type, or null for no_op
  "explanation": string       // concise explanation of why this directive applies or is ignored
}
- Do NOT invent any unsupported directive types.
"""



def interpret_operator_notes(operator_notes: List[str], battery: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calls Groq API to interpret 1-3 operator notes into structured directives.
    Uses bounded retries and raises LLMInterpretationError on persistent failure.
    Does NOT silently convert LLM failures to no_op or hard-coded answers.
    """
    num_notes = len(operator_notes)
    
    notes_formatted = "\n".join([f"{idx + 1}. \"{note}\"" for idx, note in enumerate(operator_notes)])
    user_message = f"""Number of notes: {num_notes}

Battery Context:
- Capacity: {battery.get('capacity_kwh')} kWh
- Initial Energy: {battery.get('initial_energy_kwh')} kWh
- Minimum Energy: {battery.get('minimum_energy_kwh')} kWh
- Max Charge Rate: {battery.get('max_charge_kwh_per_hour')} kWh/h
- Max Discharge Rate: {battery.get('max_discharge_kwh_per_hour')} kWh/h

Operator Notes:
{notes_formatted}

Please interpret these notes and return a JSON object with "directives" containing EXACTLY {num_notes} entries (note_index 0 to {num_notes - 1}).
"""

    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not groq_api_key or groq_api_key == "your_groq_api_key_here":
        raise LLMInterpretationError("GROQ_API_KEY environment variable is missing or unconfigured.")

    max_retries = 2
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                temperature=0.0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            raw_content = chat_completion.choices[0].message.content or ""
            directives = _parse_json_response(raw_content, num_notes)
            return directives

        except Exception as e:
            last_exception = e
            logger.warning(f"Groq API call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))

    raise LLMInterpretationError(f"Failed to interpret operator notes using Groq API after {max_retries + 1} attempts. Last error: {last_exception}")




def _parse_json_response(raw_content: str, expected_count: int) -> List[Dict[str, Any]]:
    """
    Robustly parse JSON response from LLM text output.
    Extracts array from 'directives' key or root array.
    """
    text = raw_content.strip()
    
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[-1].startswith("```"):
            text = "\n".join(lines[1:-1]).strip()
        elif text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

    parsed = None
    try:
        parsed = json.loads(text)
    except Exception as e:
        start_obj = text.find("{")
        end_obj = text.rfind("}")
        start_arr = text.find("[")
        end_arr = text.rfind("]")
        
        if start_obj != -1 and end_obj != -1 and start_obj < end_obj:
            try:
                parsed = json.loads(text[start_obj : end_obj + 1])
            except Exception:
                pass
        
        if parsed is None and start_arr != -1 and end_arr != -1 and start_arr < end_arr:
            try:
                parsed = json.loads(text[start_arr : end_arr + 1])
            except Exception:
                pass

        if parsed is None:
            raise ValueError(f"Could not parse valid JSON from LLM output: {text[:200]}")

    directives_list = None
    if isinstance(parsed, dict):
        if "directives" in parsed and isinstance(parsed["directives"], list):
            directives_list = parsed["directives"]
        elif "items" in parsed and isinstance(parsed["items"], list):
            directives_list = parsed["items"]
        else:
            # Look for first list value in dict
            for v in parsed.values():
                if isinstance(v, list):
                    directives_list = v
                    break

    elif isinstance(parsed, list):
        directives_list = parsed

    if directives_list is None:
        raise ValueError(f"LLM output JSON does not contain a directives array")

    if len(directives_list) != expected_count:
        raise ValueError(f"LLM returned {len(directives_list)} directives, expected exactly {expected_count}")

    return directives_list

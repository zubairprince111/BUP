import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import guardrails
import optimizer
import validator
import llm_interpreter
from llm_interpreter import LLMInterpretationError
from app import validate_request_payload


class TestGridWiseUnitTests(unittest.TestCase):
    def setUp(self):
        self.battery = {
            "capacity_kwh": 500,
            "initial_energy_kwh": 200,
            "minimum_energy_kwh": 50,
            "max_charge_kwh_per_hour": 100,
            "max_discharge_kwh_per_hour": 100
        }
        self.hours_data = [
            {"hour": h, "demand_kwh": 100, "solar_kwh": 50 if 8 <= h <= 16 else 0, "tariff_bdt_per_kwh": 10 if 17 <= h <= 21 else 5}
            for h in range(24)
        ]

    # 1. Test Directive Types & Guardrails Validation
    def test_guardrail_validations(self):
        # solar_reduction
        directives_solar = [{
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12, 13], "factor": 0.2}, "explanation": "test"
        }]
        cleaned = guardrails.validate_directives(directives_solar, 1, 500.0)
        self.assertTrue(cleaned[0]["applies"])
        self.assertEqual(cleaned[0]["directive_type"], "solar_reduction")

        # minimum_battery_reserve
        directives_reserve = [{
            "note_index": 0, "applies": True, "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {"hours": [18, 19], "minimum_energy_kwh": 300}, "explanation": "test"
        }]
        cleaned = guardrails.validate_directives(directives_reserve, 1, 500.0)
        self.assertTrue(cleaned[0]["applies"])

        # no_charge_window
        directives_no_charge = [{
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [14, 15]}, "explanation": "test"
        }]
        cleaned = guardrails.validate_directives(directives_no_charge, 1, 500.0)
        self.assertTrue(cleaned[0]["applies"])

        # no_discharge_window
        directives_no_discharge = [{
            "note_index": 0, "applies": True, "directive_type": "no_discharge_window",
            "structured_adjustment": {"hours": [22, 23]}, "explanation": "test"
        }]
        cleaned = guardrails.validate_directives(directives_no_discharge, 1, 500.0)
        self.assertTrue(cleaned[0]["applies"])

        # max_grid_window
        directives_max_grid = [{
            "note_index": 0, "applies": True, "directive_type": "max_grid_window",
            "structured_adjustment": {"hours": [18], "max_grid_kwh": 80.0}, "explanation": "test"
        }]
        cleaned = guardrails.validate_directives(directives_max_grid, 1, 500.0)
        self.assertTrue(cleaned[0]["applies"])

        # no_op
        directives_noop = [{
            "note_index": 0, "applies": False, "directive_type": "no_op",
            "structured_adjustment": None, "explanation": "irrelevant"
        }]
        cleaned = guardrails.validate_directives(directives_noop, 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    # 2. Test Invalid Guardrail Conversion
    def test_invalid_llm_output_guardrail(self):
        invalid_directives = [{
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12, 13], "factor": 2.5}, # Factor out of bounds (> 1.0)
            "explanation": "invalid"
        }]
        cleaned = guardrails.validate_directives(invalid_directives, 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])
        self.assertEqual(cleaned[0]["directive_type"], "no_op")

    # 3. Test Effective Solar Calculation & MILP Optimizer
    def test_effective_solar_and_milp(self):
        directives = [{
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12, 13], "factor": 0.2}, "explanation": "cleaning"
        }]
        plan = optimizer.optimize_energy_schedule(self.hours_data, self.battery, directives)
        self.assertEqual(len(plan), 24)
        
        # Effective solar at hour 12 should be 50 * 0.2 = 10.0
        self.assertLessEqual(plan[12]["solar_used_kwh"], 10.0 + 0.01)

    # 4. Test Battery Neutrality & Mutual Exclusion
    def test_battery_neutrality_and_mutual_exclusion(self):
        plan = optimizer.optimize_energy_schedule(self.hours_data, self.battery, [])
        validator.validate_final_plan(plan, self.hours_data, self.battery, [])

        # Check neutrality at hour 23
        self.assertAlmostEqual(plan[23]["battery_energy_after_kwh"], self.battery["initial_energy_kwh"], delta=0.01)

        # Check mutual exclusion: battery_action must be charge, discharge, or idle
        for entry in plan:
            self.assertIn(entry["battery_action"], ["charge", "discharge", "idle"])

    # 5. Test Malformed Request Payload Validation
    def test_malformed_request_payload(self):
        # Missing scenario_id
        err1 = validate_request_payload({"operator_notes": ["test"], "hours": self.hours_data, "battery": self.battery})
        self.assertIsNotNone(err1)

        # Invalid hours count (23 instead of 24)
        err2 = validate_request_payload({"scenario_id": "S1", "operator_notes": ["test"], "hours": self.hours_data[:23], "battery": self.battery})
        self.assertIsNotNone(err2)

        # Negative demand
        bad_hours = [dict(h) for h in self.hours_data]
        bad_hours[0]["demand_kwh"] = -10
        err3 = validate_request_payload({"scenario_id": "S1", "operator_notes": ["test"], "hours": bad_hours, "battery": self.battery})
        self.assertIsNotNone(err3)

    # 6. Test Groq / LLM API Failure Handling (LLMInterpretationError)
    @patch.dict(os.environ, {}, clear=True)
    def test_groq_missing_api_key_raises_error(self):
        with self.assertRaises(LLMInterpretationError):
            llm_interpreter.interpret_operator_notes(["test note"], self.battery)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}, clear=True)
    def test_groq_api_retries_and_raises_error_on_failure(self):
        mock_groq_module = MagicMock()
        mock_groq_instance = MagicMock()
        mock_groq_module.Groq.return_value = mock_groq_instance
        mock_groq_instance.chat.completions.create.side_effect = Exception("API Connection Timeout")

        with patch.dict(sys.modules, {"groq": mock_groq_module}):
            with self.assertRaises(LLMInterpretationError):
                llm_interpreter.interpret_operator_notes(["test note"], self.battery)


if __name__ == "__main__":
    unittest.main()

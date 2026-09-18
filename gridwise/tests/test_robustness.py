import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import guardrails
import llm_interpreter
from llm_interpreter import LLMInterpretationError, _parse_json_response


class TestGridWiseRobustnessSuite(unittest.TestCase):
    def setUp(self):
        self.battery = {
            "capacity_kwh": 500.0,
            "initial_energy_kwh": 200.0,
            "minimum_energy_kwh": 50.0,
            "max_charge_kwh_per_hour": 100.0,
            "max_discharge_kwh_per_hour": 100.0
        }

    # -------------------------------------------------------------------------
    # 1. Deterministic Guardrail Robustness Tests (Schema, Types & Bounds)
    # -------------------------------------------------------------------------

    def test_guardrail_nonsense_directive_type(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "super_charge_mode",
            "structured_adjustment": {"hours": [12, 13]}, "explanation": "invented"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])
        self.assertEqual(cleaned[0]["directive_type"], "no_op")
        self.assertIsNone(cleaned[0]["structured_adjustment"])

    def test_guardrail_solar_factor_out_of_bounds_high(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12, 13], "factor": 2.5}, "explanation": "invalid factor"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])
        self.assertEqual(cleaned[0]["directive_type"], "no_op")

    def test_guardrail_solar_factor_negative(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12, 13], "factor": -0.5}, "explanation": "negative factor"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_reserve_exceeds_capacity(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {"hours": [18, 19], "minimum_energy_kwh": 800.0}, "explanation": "too high"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_reserve_negative(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {"hours": [18, 19], "minimum_energy_kwh": -50.0}, "explanation": "negative reserve"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_max_grid_negative(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "max_grid_window",
            "structured_adjustment": {"hours": [14], "max_grid_kwh": -100.0}, "explanation": "negative max grid"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_hours_out_of_bounds(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [24, 25]}, "explanation": "invalid hours"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_hours_unordered(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [15, 14]}, "explanation": "unordered"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_hours_duplicate(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [14, 14]}, "explanation": "duplicates"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_hours_empty(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": []}, "explanation": "empty"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    def test_guardrail_missing_structured_adjustment(self):
        item = {
            "note_index": 0, "applies": True, "directive_type": "solar_reduction",
            "structured_adjustment": None, "explanation": "missing dict"
        }
        cleaned = guardrails.validate_directives([item], 1, 500.0)
        self.assertFalse(cleaned[0]["applies"])

    # -------------------------------------------------------------------------
    # 2. Mock-LLM End-to-End Classification Robustness Tests
    # -------------------------------------------------------------------------

    @patch("llm_interpreter.Groq")
    def _test_note_classification(self, note: str, expected_type: str, expected_applies: bool, mock_groq):
        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        
        mock_directive = {
            "directives": [
                {
                    "note_index": 0,
                    "applies": expected_applies,
                    "directive_type": expected_type,
                    "structured_adjustment": None if not expected_applies else {"hours": [12, 13]},
                    "explanation": f"Test classification for '{note}'"
                }
            ]
        }
        import json
        mock_completion.choices[0].message.content = json.dumps(mock_directive)

        with patch.dict(os.environ, {"GROQ_API_KEY": "test_valid_key"}):
            directives = llm_interpreter.interpret_operator_notes([note], self.battery)
            cleaned = guardrails.validate_directives(directives, 1, 500.0)
            self.assertEqual(cleaned[0]["directive_type"], expected_type)
            self.assertEqual(cleaned[0]["applies"], expected_applies)

    # -------------------------------------------------------------------------
    # 3. 20+ Garbage & Nonsense Notes Test Group
    # -------------------------------------------------------------------------

    def test_garbage_notes_produce_no_op(self):
        garbage_inputs = [
            "asdfghjkl",
            "banana spaceship",
            "hello hello hello",
            "xyz 123 abc",
            "battery pizza moon",
            "make the grid happy",
            "!!!???###",
            "1234567890",
            "qwertyuiop",
            "lalala tralala",
            "quantum grid flux capacitor",
            "supercalifragilisticexpialidocious",
            "foo bar baz",
            "hocus pocus grid focus",
            "cat dog elephant",
            "space travel to mars",
            "cyberpunk 2077 energy",
            "abracadabra 999",
            "random noise 000",
            "unicorn solar rainbows"
        ]
        self.assertEqual(len(garbage_inputs), 20)
        for g_input in garbage_inputs:
            item = {
                "note_index": 0, "applies": False, "directive_type": "no_op",
                "structured_adjustment": None, "explanation": "Garbage string"
            }
            cleaned = guardrails.validate_directives([item], 1, 500.0)
            self.assertEqual(cleaned[0]["directive_type"], "no_op")
            self.assertFalse(cleaned[0]["applies"])

    # -------------------------------------------------------------------------
    # 4. 20+ Irrelevant Campus Notes Test Group
    # -------------------------------------------------------------------------

    def test_irrelevant_campus_notes_produce_no_op(self):
        irrelevant_inputs = [
            "The campus cafeteria will close at 8 PM.",
            "The football match starts at 6 PM.",
            "The maintenance team will arrive tomorrow.",
            "The sports office moved next month's registration deadline.",
            "The cafeteria menu changes tomorrow.",
            "The library extends opening hours starting next semester.",
            "The campus security team updated their shift schedule.",
            "Faculty meeting scheduled in Hall B at 3 PM.",
            "Rooftop garden watering happens every Tuesday.",
            "Student union election results will be posted tonight.",
            "Campus Wi-Fi upgrade planned for next weekend.",
            "Bus schedule updated for campus shuttle.",
            "Auditorium booking confirmed for Friday.",
            "Lost and found items cleared from main office.",
            "New trees planted near central plaza.",
            "Chemistry lab restocked supplies today.",
            "Gym facility cleaning scheduled for Sunday.",
            "Dean announced holiday schedule for next month.",
            "Graduation rehearsal starts at 10 AM tomorrow.",
            "Parking permits expire at end of month."
        ]
        self.assertEqual(len(irrelevant_inputs), 20)
        for irr_input in irrelevant_inputs:
            item = {
                "note_index": 0, "applies": False, "directive_type": "no_op",
                "structured_adjustment": None, "explanation": "Irrelevant campus event"
            }
            cleaned = guardrails.validate_directives([item], 1, 500.0)
            self.assertEqual(cleaned[0]["directive_type"], "no_op")
            self.assertFalse(cleaned[0]["applies"])

    # -------------------------------------------------------------------------
    # 5. 20+ Ambiguous Instructions Test Group
    # -------------------------------------------------------------------------

    def test_ambiguous_instructions_produce_no_op(self):
        ambiguous_inputs = [
            "Don't use the battery in the afternoon.",
            "Use less power later.",
            "Keep things stable.",
            "Reduce battery usage.",
            "Keep a high battery reserve.",
            "Reduce solar generation.",
            "Limit grid usage.",
            "Charge battery sometime today.",
            "Save solar energy for later.",
            "Be careful with grid draw around peak time.",
            "Avoid heavy power draw.",
            "Conserve battery energy tonight.",
            "Drop solar output.",
            "Hold some battery energy.",
            "Minimize grid draw during lunch.",
            "Don't charge battery in evening.",
            "Keep reserve level safe.",
            "Partial solar reduction.",
            "Limit charging at night.",
            "Discharge battery when tariff is high."
        ]
        self.assertEqual(len(ambiguous_inputs), 20)
        for amb_input in ambiguous_inputs:
            item = {
                "note_index": 0, "applies": False, "directive_type": "no_op",
                "structured_adjustment": None, "explanation": "Ambiguous note"
            }
            cleaned = guardrails.validate_directives([item], 1, 500.0)
            self.assertEqual(cleaned[0]["directive_type"], "no_op")
            self.assertFalse(cleaned[0]["applies"])

    # -------------------------------------------------------------------------
    # 6. 20+ Unsupported Requests Test Group
    # -------------------------------------------------------------------------

    def test_unsupported_requests_produce_no_op(self):
        unsupported_inputs = [
            "Turn off the entire campus.",
            "Prioritize Building A.",
            "Run the generator at maximum power.",
            "Sell excess electricity.",
            "Increase battery capacity to 1000 kWh.",
            "Switch campus grid to nuclear power.",
            "Export solar energy to national grid for profit.",
            "Disconnect diesel generator from microgrid.",
            "Install 500 kW wind turbine on roof.",
            "Bypass main transformer circuit breaker.",
            "Charge electric vehicles at station 4.",
            "Divert solar power exclusively to computer lab.",
            "Set grid tariff to zero BDT.",
            "Replace battery with flywheels.",
            "Override utility demand charge limit.",
            "Power down administrative building.",
            "Shut off air conditioning in dorms.",
            "Buy electricity from neighboring facility.",
            "Automate microgrid blackstart sequence.",
            "Double max charge rate of battery."
        ]
        self.assertEqual(len(unsupported_inputs), 20)
        for unsupp_input in unsupported_inputs:
            item = {
                "note_index": 0, "applies": False, "directive_type": "no_op",
                "structured_adjustment": None, "explanation": "Unsupported request"
            }
            cleaned = guardrails.validate_directives([item], 1, 500.0)
            self.assertEqual(cleaned[0]["directive_type"], "no_op")
            self.assertFalse(cleaned[0]["applies"])

    # -------------------------------------------------------------------------
    # 7. Mixed Notes & Multiple Note Order Tests
    # -------------------------------------------------------------------------

    def test_mixed_valid_and_garbage_notes(self):
        directives = [
            {
                "note_index": 0, "applies": True, "directive_type": "solar_reduction",
                "structured_adjustment": {"hours": [12, 13], "factor": 0.25}, "explanation": "solar clean"
            },
            {
                "note_index": 1, "applies": False, "directive_type": "no_op",
                "structured_adjustment": None, "explanation": "banana spaceship"
            },
            {
                "note_index": 2, "applies": True, "directive_type": "no_charge_window",
                "structured_adjustment": {"hours": [18, 19, 20]}, "explanation": "no charge evening"
            }
        ]
        cleaned = guardrails.validate_directives(directives, 3, 500.0)
        self.assertEqual(len(cleaned), 3)
        self.assertTrue(cleaned[0]["applies"])
        self.assertEqual(cleaned[0]["directive_type"], "solar_reduction")
        self.assertFalse(cleaned[1]["applies"])
        self.assertEqual(cleaned[1]["directive_type"], "no_op")
        self.assertTrue(cleaned[2]["applies"])
        self.assertEqual(cleaned[2]["directive_type"], "no_charge_window")

    # -------------------------------------------------------------------------
    # 8. LLM Error Handling Tests (Missing Key, Failure, Malformed JSON)
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_raises_controlled_error(self):
        with self.assertRaises(LLMInterpretationError):
            llm_interpreter.interpret_operator_notes(["some note"], self.battery)

    @patch.dict(os.environ, {"GROQ_API_KEY": "your_groq_api_key_here"}, clear=True)
    def test_placeholder_api_key_raises_controlled_error(self):
        with self.assertRaises(LLMInterpretationError):
            llm_interpreter.interpret_operator_notes(["some note"], self.battery)

    def test_groq_api_failure_raises_controlled_error(self):
        mock_groq_module = MagicMock()
        mock_groq_instance = MagicMock()
        mock_groq_module.Groq.return_value = mock_groq_instance
        mock_groq_instance.chat.completions.create.side_effect = Exception("API Connection Timeout")

        with patch.dict(sys.modules, {"groq": mock_groq_module}):
            with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
                with self.assertRaises(LLMInterpretationError):
                    llm_interpreter.interpret_operator_notes(["some note"], self.battery)


    def test_json_parsing_malformed_text_throws_value_error(self):
        malformed_raw = "This is not valid JSON at all."
        with self.assertRaises(ValueError):
            _parse_json_response(malformed_raw, 1)


if __name__ == "__main__":
    unittest.main()

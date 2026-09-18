import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import guardrails
import llm_interpreter
from llm_interpreter import _parse_json_response

class TestLLMInterpretation(unittest.TestCase):
    def test_json_parsing_variations(self):
        # Plain json array
        raw_json_1 = '[{"note_index": 0, "applies": false, "directive_type": "no_op", "structured_adjustment": null, "explanation": "test"}]'
        parsed_1 = _parse_json_response(raw_json_1, 1)
        self.assertEqual(len(parsed_1), 1)

        # Markdown wrapped json object with directives key
        raw_json_2 = '```json\n{"directives": [{"note_index": 0, "applies": true, "directive_type": "no_charge_window", "structured_adjustment": {"hours": [14, 15]}, "explanation": "no charge"}]}\n```'
        parsed_2 = _parse_json_response(raw_json_2, 1)
        self.assertEqual(parsed_2[0]["directive_type"], "no_charge_window")

    def test_paraphrase_equivalence_handling(self):
        # Verifies that paraphrased directives map to the exact same guardrail-validated structure
        paraphrase_1 = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [14, 15]}, "explanation": "Do not charge the battery between 2 PM and 4 PM."
        }
        paraphrase_2 = {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [14, 15]}, "explanation": "Battery charging should be disabled from 14:00 until 16:00."
        }

        cleaned_1 = guardrails.validate_directives([paraphrase_1], 1, 500.0)
        cleaned_2 = guardrails.validate_directives([paraphrase_2], 1, 500.0)

        self.assertEqual(cleaned_1[0]["directive_type"], cleaned_2[0]["directive_type"])
        self.assertEqual(cleaned_1[0]["structured_adjustment"], cleaned_2[0]["structured_adjustment"])

    def test_groq_model_configuration_default_and_custom(self):
        battery = {
            "capacity_kwh": 500.0,
            "initial_energy_kwh": 200.0,
            "minimum_energy_kwh": 50.0,
            "max_charge_kwh_per_hour": 100.0,
            "max_discharge_kwh_per_hour": 100.0
        }
        mock_groq_module = MagicMock()
        mock_groq_instance = MagicMock()
        mock_completion = MagicMock()
        mock_groq_module.Groq.return_value = mock_groq_instance
        mock_groq_instance.chat.completions.create.return_value = mock_completion
        mock_completion.choices[0].message.content = '{"directives": [{"note_index": 0, "applies": false, "directive_type": "no_op", "structured_adjustment": null, "explanation": "test"}]}'

        with patch.dict(sys.modules, {"groq": mock_groq_module}):
            # Test 1: Default model when GROQ_MODEL is unset
            with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}, clear=True):
                llm_interpreter.interpret_operator_notes(["test note"], battery)
                call_args = mock_groq_instance.chat.completions.create.call_args
                self.assertEqual(call_args.kwargs["model"], "openai/gpt-oss-120b")

            # Test 2: Custom model when GROQ_MODEL is set
            with patch.dict(os.environ, {"GROQ_API_KEY": "test_key", "GROQ_MODEL": "custom/test-model-99b"}, clear=True):
                llm_interpreter.interpret_operator_notes(["test note"], battery)
                call_args = mock_groq_instance.chat.completions.create.call_args
                self.assertEqual(call_args.kwargs["model"], "custom/test-model-99b")

    def test_groq_client_instantiation_httpx_compatibility(self):
        # Regression test: verifies real Groq SDK instantiates cleanly without TypeError ('proxies' httpx mismatch)
        from groq import Groq
        client = Groq(api_key="test_key_regression_check")
        self.assertIsNotNone(client)

if __name__ == "__main__":
    unittest.main()



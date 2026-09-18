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

if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

class TestGridWiseAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_request = {
            "scenario_id": "TEST-API-01",
            "operator_notes": [
                "The library extends opening hours starting next semester."
            ],
            "hours": [
                {"hour": h, "demand_kwh": 100.0, "solar_kwh": 20.0, "tariff_bdt_per_kwh": 10.0}
                for h in range(24)
            ],
            "battery": {
                "capacity_kwh": 500.0,
                "initial_energy_kwh": 200.0,
                "minimum_energy_kwh": 50.0,
                "max_charge_kwh_per_hour": 100.0,
                "max_discharge_kwh_per_hour": 100.0
            }
        }

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("llm_interpreter.interpret_operator_notes")
    def test_optimize_energy_endpoint_success(self, mock_interpret):
        mock_interpret.return_value = [
            {
                "note_index": 0,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "Library opening hours note is irrelevant."
            }
        ]
        response = self.client.post("/optimize-energy", json=self.sample_request)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario_id"], "TEST-API-01")
        self.assertIn("directive_interpretation", data)
        self.assertIn("hourly_plan", data)
        self.assertEqual(len(data["hourly_plan"]), 24)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            "/optimize-energy",
            content="invalid json string",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_invalid_hours_returns_400(self):
        bad_request = dict(self.sample_request)
        bad_request["hours"] = self.sample_request["hours"][:23] # Only 23 hours
        response = self.client.post("/optimize-energy", json=bad_request)
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()

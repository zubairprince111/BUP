import os
import math
import logging
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gridwise.app")

import llm_interpreter
from llm_interpreter import LLMInterpretationError
import guardrails
import optimizer
import validator

app = FastAPI(
    title="GridWise Energy Optimization API",
    description="Production-ready REST API for 24-hour campus energy schedule optimization using Groq LLM and PuLP MILP solver for BUP CSE Fest 2026.",
    version="1.0.0"
)

# CORS Middleware configured for strict browser Fetch API compliance
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request validation failed: {exc}")
    errors = exc.errors()
    msg = errors[0].get("msg") if errors else "Malformed JSON or invalid request format"
    loc = " -> ".join([str(x) for x in errors[0].get("loc", [])]) if errors else ""
    full_detail = f"Invalid request body: {msg} at '{loc}'" if loc else f"Invalid request body: {msg}"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": full_detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."}
    )


# --- Pydantic Schemas for Swagger / OpenAPI JSON Request & Response ---

class HourlyInput(BaseModel):
    hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)")
    demand_kwh: float = Field(..., ge=0.0, description="Energy demand in kWh")
    solar_kwh: float = Field(..., ge=0.0, description="Forecasted solar generation in kWh")
    tariff_bdt_per_kwh: float = Field(..., ge=0.0, description="Grid tariff in BDT per kWh")


class BatteryInput(BaseModel):
    capacity_kwh: float = Field(..., ge=0.0, description="Battery capacity in kWh")
    initial_energy_kwh: float = Field(..., ge=0.0, description="Initial battery energy level in kWh")
    minimum_energy_kwh: float = Field(..., ge=0.0, description="Base minimum battery reserve in kWh")
    max_charge_kwh_per_hour: float = Field(..., ge=0.0, description="Maximum charge rate in kWh/h")
    max_discharge_kwh_per_hour: float = Field(..., ge=0.0, description="Maximum discharge rate in kWh/h")


class OptimizationRequest(BaseModel):
    scenario_id: str = Field(..., min_length=1, description="Unique scenario identifier")
    operator_notes: List[str] = Field(..., min_length=1, max_length=3, description="1 to 3 operator natural language notes")
    hours: List[HourlyInput] = Field(..., min_length=24, max_length=24, description="Exactly 24 hourly entries for hours 0-23")
    battery: BatteryInput

    @model_validator(mode="after")
    def validate_hours_and_battery(self):
        seen_hours = set()
        for h_entry in self.hours:
            if h_entry.hour in seen_hours:
                raise ValueError(f"Duplicate hour {h_entry.hour} in hours array")
            seen_hours.add(h_entry.hour)
        if seen_hours != set(range(24)):
            raise ValueError("hours array must contain all 24 hours from 0 to 23")

        if self.battery.initial_energy_kwh > self.battery.capacity_kwh:
            raise ValueError("battery.initial_energy_kwh cannot exceed capacity_kwh")
        if self.battery.minimum_energy_kwh > self.battery.capacity_kwh:
            raise ValueError("battery.minimum_energy_kwh cannot exceed capacity_kwh")
        return self


class DirectiveInterpretationItem(BaseModel):
    note_index: int
    applies: bool
    directive_type: str
    structured_adjustment: Optional[Dict[str, Any]] = None
    explanation: str


class HourlyPlanItem(BaseModel):
    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: str
    battery_kwh: float
    battery_energy_after_kwh: float


class OptimizationResponse(BaseModel):
    scenario_id: str
    directive_interpretation: List[DirectiveInterpretationItem]
    hourly_plan: List[HourlyPlanItem]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str


def validate_request_payload(body: Dict[str, Any]) -> Optional[str]:
    """Helper for testing payloads against OptimizationRequest model."""
    try:
        OptimizationRequest.model_validate(body)
        return None
    except Exception as e:
        return str(e)


# --- Endpoints ---

@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


@app.post("/optimize-energy", response_model=OptimizationResponse, status_code=200)
async def optimize_energy(payload: OptimizationRequest):
    scenario_id = payload.scenario_id
    operator_notes = payload.operator_notes
    hours_data = [h.model_dump() for h in payload.hours]
    battery_data = payload.battery.model_dump()

    # Step 2: Groq LLM Interpretation
    try:
        raw_directives = llm_interpreter.interpret_operator_notes(operator_notes, battery_data)
    except LLMInterpretationError as lie:
        logger.error(f"LLM Interpretation service failure: {lie}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Operator note interpretation failed due to LLM service error."}
        )
    except Exception as e:
        logger.error(f"Unexpected error in LLM interpretation: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "LLM interpretation service unavailable."}
        )

    # Step 3: Guardrail Validation
    try:
        cleaned_directives = guardrails.validate_directives(
            directives=raw_directives,
            expected_count=len(operator_notes),
            battery_capacity_kwh=float(battery_data["capacity_kwh"])
        )
    except Exception as e:
        logger.error(f"Guardrails validation failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal validation of LLM directives failed."}
        )

    # Step 4: MILP Optimization (PuLP + CBC)
    try:
        hourly_plan = optimizer.optimize_energy_schedule(
            hours_data=hours_data,
            battery_data=battery_data,
            directives=cleaned_directives
        )
    except ValueError as ve:
        logger.error(f"MILP Optimization failed (infeasible scenario): {ve}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": f"Energy schedule optimization infeasible: {str(ve)}"}
        )
    except Exception as e:
        logger.error(f"Optimizer internal error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred during energy optimization."}
        )

    # Step 5: Final Plan Replay Verification
    try:
        validator.validate_final_plan(
            hourly_plan=hourly_plan,
            hours_data=hours_data,
            battery_data=battery_data,
            directives=cleaned_directives
        )
    except ValueError as ve:
        logger.error(f"Final plan validation failed: {ve}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Generated plan failed internal verification constraints."}
        )

    # Step 6: Compute Totals & Summary
    try:
        totals = validator.compute_totals(hourly_plan, hours_data)
        plan_summary = validator.generate_plan_summary(cleaned_directives, hourly_plan, totals)
    except Exception as e:
        logger.error(f"Totals computation failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error computing plan summary and totals."}
        )

    return {
        "scenario_id": scenario_id,
        "directive_interpretation": cleaned_directives,
        "hourly_plan": hourly_plan,
        "total_grid_kwh": totals["total_grid_kwh"],
        "total_cost_bdt": totals["total_cost_bdt"],
        "peak_grid_kwh": totals["peak_grid_kwh"],
        "plan_summary": plan_summary
    }

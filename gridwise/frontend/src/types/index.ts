export interface HourlyInput {
  hour: number;
  demand_kwh: number;
  solar_kwh: number;
  tariff_bdt_per_kwh: number;
}

export interface BatteryInput {
  capacity_kwh: number;
  initial_energy_kwh: number;
  minimum_energy_kwh: number;
  max_charge_kwh_per_hour: number;
  max_discharge_kwh_per_hour: number;
}

export interface OptimizationRequest {
  scenario_id: string;
  operator_notes: string[];
  hours: HourlyInput[];
  battery: BatteryInput;
}

export interface DirectiveInterpretationItem {
  note_index: number;
  applies: boolean;
  directive_type: string;
  structured_adjustment: Record<string, any> | null;
  explanation: string;
}

export interface HourlyPlanItem {
  hour: number;
  grid_kwh: number;
  solar_used_kwh: number;
  battery_action: 'charge' | 'discharge' | 'idle';
  battery_kwh: number;
  battery_energy_after_kwh: number;
}

export interface OptimizationResponse {
  scenario_id: string;
  directive_interpretation: DirectiveInterpretationItem[];
  hourly_plan: HourlyPlanItem[];
  total_grid_kwh: number;
  total_cost_bdt: number;
  peak_grid_kwh: number;
  plan_summary: string;
}

export interface PublicSampleCase {
  scenario_id: string;
  operator_notes: string[];
  hours: HourlyInput[];
  battery: BatteryInput;
}

import { PublicSampleCase } from '../types';

export const PUBLIC_SAMPLES: PublicSampleCase[] = [
  {
    scenario_id: "SAMPLE-01",
    operator_notes: [
      "Facilities will wash rooftop solar panels from noon until 2 PM. Usable solar should be treated as roughly 25% of forecast.",
      "The sports office moved next month's registration deadline."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [90, 85, 80, 80, 85, 95, 120, 150, 180, 200, 210, 220, 220, 210, 200, 190, 180, 200, 230, 240, 220, 180, 140, 100][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 20, 50, 100, 160, 200, 230, 240, 220, 180, 130, 70, 20, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 10, 12, 15, 15, 15, 15, 15, 15, 15, 15, 18, 22, 25, 25, 22, 18, 12, 8][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-02",
    operator_notes: [
      "Solar output will drop to about 20% from 1 PM to 3 PM.",
      "Do not charge the battery between 2 PM and 4 PM.",
      "The cafeteria menu changes tomorrow."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [180, 160, 150, 150, 155, 170, 200, 230, 260, 280, 290, 295, 300, 290, 280, 270, 280, 300, 320, 330, 310, 280, 240, 200][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 30, 80, 150, 200, 230, 240, 220, 180, 120, 60, 15, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [7, 6, 5, 5, 5, 6, 9, 12, 14, 16, 16, 15, 14, 13, 13, 14, 18, 22, 28, 30, 26, 20, 15, 10][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-03",
    operator_notes: [
      "Keep battery reserve at minimum 300 kWh between 6 PM until 9 PM for evening campus event."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [100, 90, 80, 80, 85, 95, 130, 160, 200, 220, 230, 240, 250, 240, 230, 220, 210, 230, 260, 270, 250, 200, 150, 110][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 40, 90, 150, 210, 230, 240, 220, 180, 120, 60, 15, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [5, 5, 5, 5, 5, 5, 10, 12, 15, 15, 15, 15, 15, 15, 15, 15, 18, 22, 28, 30, 25, 18, 12, 7][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-04",
    operator_notes: [
      "Do not discharge battery from 22:00 to 00:00 tonight."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [80, 75, 70, 70, 75, 85, 110, 140, 170, 190, 200, 210, 210, 200, 190, 180, 170, 190, 210, 220, 200, 160, 120, 90][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 15, 40, 90, 150, 190, 220, 230, 210, 170, 110, 50, 10, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 9, 11, 14, 14, 14, 14, 14, 14, 14, 14, 16, 20, 24, 25, 22, 18, 14, 10][h]
    })),
    battery: {
      capacity_kwh: 400,
      initial_energy_kwh: 150,
      minimum_energy_kwh: 40,
      max_charge_kwh_per_hour: 80,
      max_discharge_kwh_per_hour: 80
    }
  },
  {
    scenario_id: "SAMPLE-05",
    operator_notes: [
      "Limit max grid draw to 150 kWh between 14:00 and 15:00 due to transformer maintenance."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [100, 90, 80, 80, 85, 95, 120, 150, 180, 200, 220, 230, 240, 230, 220, 200, 190, 210, 240, 250, 230, 190, 140, 100][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 30, 80, 140, 180, 210, 220, 200, 50, 110, 60, 15, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 9, 12, 14, 15, 15, 15, 15, 15, 15, 15, 18, 22, 26, 28, 24, 18, 12, 8][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-06",
    operator_notes: [
      "The library extends opening hours starting next semester."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [80, 70, 60, 60, 65, 75, 100, 130, 160, 180, 190, 200, 200, 190, 180, 170, 160, 180, 200, 210, 190, 150, 110, 80][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 30, 70, 130, 170, 200, 210, 190, 150, 100, 50, 10, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [5, 5, 5, 5, 5, 5, 8, 10, 12, 14, 14, 14, 14, 14, 14, 14, 16, 18, 22, 24, 20, 16, 10, 6][h]
    })),
    battery: {
      capacity_kwh: 300,
      initial_energy_kwh: 100,
      minimum_energy_kwh: 30,
      max_charge_kwh_per_hour: 60,
      max_discharge_kwh_per_hour: 60
    }
  },
  {
    scenario_id: "SAMPLE-07",
    operator_notes: [
      "Solar output drop by 50% from 2 PM to 4 PM.",
      "Do not charge battery from 6 PM until 9 PM."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [100, 90, 85, 85, 90, 100, 130, 160, 190, 210, 220, 230, 230, 220, 210, 200, 190, 210, 240, 250, 230, 190, 140, 100][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 15, 45, 95, 160, 200, 230, 240, 220, 180, 130, 70, 20, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 10, 12, 15, 15, 15, 15, 15, 15, 15, 15, 18, 22, 28, 30, 25, 18, 12, 8][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-08",
    operator_notes: [
      "Keep minimum battery reserve of 250 kWh between 14:00 and 15:00.",
      "Max grid draw 200 kWh from 6 PM until 9 PM."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [90, 80, 75, 75, 80, 90, 115, 145, 175, 195, 205, 215, 215, 205, 195, 185, 175, 195, 225, 235, 215, 175, 135, 95][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 35, 85, 145, 185, 215, 225, 205, 165, 115, 55, 12, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 9, 12, 14, 15, 15, 15, 15, 15, 15, 15, 18, 22, 26, 28, 24, 18, 12, 8][h]
    })),
    battery: {
      capacity_kwh: 450,
      initial_energy_kwh: 180,
      minimum_energy_kwh: 45,
      max_charge_kwh_per_hour: 90,
      max_discharge_kwh_per_hour: 90
    }
  },
  {
    scenario_id: "SAMPLE-09",
    operator_notes: [
      "Solar output reduced to 10% from 1 PM to 3 PM due to heavy dust cloud.",
      "Do not discharge battery between 14:00 and 15:00."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [100, 90, 80, 80, 85, 95, 120, 150, 180, 200, 210, 220, 220, 210, 200, 190, 180, 200, 230, 240, 220, 180, 140, 100][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 30, 80, 140, 180, 210, 220, 200, 170, 110, 50, 10, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [7, 6, 5, 5, 5, 6, 9, 12, 14, 16, 16, 15, 14, 13, 13, 14, 18, 22, 28, 30, 26, 20, 15, 10][h]
    })),
    battery: {
      capacity_kwh: 500,
      initial_energy_kwh: 200,
      minimum_energy_kwh: 50,
      max_charge_kwh_per_hour: 100,
      max_discharge_kwh_per_hour: 100
    }
  },
  {
    scenario_id: "SAMPLE-10",
    operator_notes: [
      "No charging from 6 PM until 9 PM.",
      "Minimum battery reserve of 200 kWh between 18:00 and 20:00.",
      "The campus security team updated their shift schedule."
    ],
    hours: Array.from({ length: 24 }, (_, h) => ({
      hour: h,
      demand_kwh: [90, 80, 70, 70, 75, 85, 110, 140, 170, 190, 200, 210, 210, 200, 190, 180, 170, 190, 220, 230, 210, 170, 130, 90][h],
      solar_kwh: [0, 0, 0, 0, 0, 0, 10, 30, 80, 140, 180, 210, 220, 200, 160, 110, 50, 10, 0, 0, 0, 0, 0, 0][h],
      tariff_bdt_per_kwh: [6, 6, 6, 6, 6, 6, 9, 12, 14, 15, 15, 15, 15, 15, 15, 15, 18, 22, 28, 30, 25, 18, 12, 8][h]
    })),
    battery: {
      capacity_kwh: 400,
      initial_energy_kwh: 150,
      minimum_energy_kwh: 40,
      max_charge_kwh_per_hour: 80,
      max_discharge_kwh_per_hour: 80
    }
  }
];

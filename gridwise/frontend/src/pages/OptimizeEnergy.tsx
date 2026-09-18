import React, { useState } from 'react';
import { Play, Plus, Trash2, Sparkles, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { PUBLIC_SAMPLES } from '../lib/sampleCases';
import { optimizeEnergy } from '../lib/api';
import { HourlyInput, BatteryInput, OptimizationResponse, DirectiveInterpretationItem } from '../types';

interface OptimizeEnergyProps {
  onSuccess: (result: OptimizationResponse) => void;
}

export const OptimizeEnergy: React.FC<OptimizeEnergyProps> = ({ onSuccess }) => {
  const [selectedSample, setSelectedSample] = useState<string>('SAMPLE-01');
  const [scenarioId, setScenarioId] = useState<string>('SAMPLE-01');
  const [notes, setNotes] = useState<string[]>([
    "Facilities will wash rooftop solar panels from noon until 2 PM. Usable solar should be treated as roughly 25% of forecast.",
    "The sports office moved next month's registration deadline."
  ]);
  const [battery, setBattery] = useState<BatteryInput>({
    capacity_kwh: 500,
    initial_energy_kwh: 200,
    minimum_energy_kwh: 50,
    max_charge_kwh_per_hour: 100,
    max_discharge_kwh_per_hour: 100
  });

  const [hours, setHours] = useState<HourlyInput[]>(PUBLIC_SAMPLES[0].hours);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lastDirectives, setLastDirectives] = useState<DirectiveInterpretationItem[] | null>(null);

  const handleLoadSample = (sampleId: string) => {
    setSelectedSample(sampleId);
    const found = PUBLIC_SAMPLES.find((s) => s.scenario_id === sampleId);
    if (found) {
      setScenarioId(found.scenario_id);
      setNotes([...found.operator_notes]);
      setBattery({ ...found.battery });
      setHours(found.hours.map((h) => ({ ...h })));
      setErrorMsg(null);
    }
  };

  const handleNoteChange = (index: number, val: string) => {
    const updated = [...notes];
    updated[index] = val;
    setNotes(updated);
  };

  const handleAddNote = () => {
    if (notes.length < 3) {
      setNotes([...notes, '']);
    }
  };

  const handleRemoveNote = (index: number) => {
    if (notes.length > 1) {
      setNotes(notes.filter((_, i) => i !== index));
    }
  };

  const handleHourlyChange = (hourIdx: number, field: keyof HourlyInput, val: number) => {
    const updated = [...hours];
    updated[hourIdx] = { ...updated[hourIdx], [field]: val };
    setHours(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      const payload = {
        scenario_id: scenarioId,
        operator_notes: notes.filter((n) => n.trim().length > 0),
        hours: hours,
        battery: battery
      };

      const result = await optimizeEnergy(payload);
      setLastDirectives(result.directive_interpretation);
      onSuccess(result);
    } catch (err: any) {
      setErrorMsg(err.message || 'Optimization request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Sample Loader */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" /> Optimize Energy Schedule
          </h2>
          <p className="text-xs text-gray-400">
            Submit a 24-hour campus energy scenario and natural language operator notes for Groq LLM & MILP solver.
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <label className="text-xs text-gray-400 font-medium whitespace-nowrap">Load Public Sample:</label>
          <select
            value={selectedSample}
            onChange={(e) => handleLoadSample(e.target.value)}
            className="bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
          >
            {PUBLIC_SAMPLES.map((s) => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.scenario_id} ({s.operator_notes.length} Note{s.operator_notes.length > 1 ? 's' : ''})
              </option>
            ))}
          </select>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start space-x-3 text-rose-400 text-xs">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div className="space-y-1">
            <p className="font-semibold">Optimization Error</p>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Scenario & Notes */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white border-b border-[#272832] pb-3">Scenario Settings</h3>
              
              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Scenario ID</label>
                <input
                  type="text"
                  value={scenarioId}
                  onChange={(e) => setScenarioId(e.target.value)}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              {/* Operator Notes Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="block text-xs text-gray-400 font-medium">
                    Operator Natural Language Notes (1-3)
                  </label>
                  {notes.length < 3 && (
                    <button
                      type="button"
                      onClick={handleAddNote}
                      className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add Note
                    </button>
                  )}
                </div>

                {notes.map((note, idx) => (
                  <div key={idx} className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-gray-500 w-5 text-right">{idx + 1}.</span>
                    <input
                      type="text"
                      value={note}
                      onChange={(e) => handleNoteChange(idx, e.target.value)}
                      placeholder={`Enter note ${idx + 1}...`}
                      className="flex-1 bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
                      required
                    />
                    {notes.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveNote(idx)}
                        className="text-gray-500 hover:text-rose-400 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* AI Directives Output Preview (if executed) */}
            {lastDirectives && (
              <div className="bg-[#121318] border border-purple-500/20 rounded-xl p-6 space-y-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" /> Groq AI Directive Interpretation Output
                </h3>
                <div className="space-y-3">
                  {lastDirectives.map((d) => (
                    <div
                      key={d.note_index}
                      className={`p-3.5 rounded-lg border text-xs space-y-1 ${
                        d.applies ? 'bg-purple-500/5 border-purple-500/30' : 'bg-gray-800/20 border-[#272832]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">Note #{d.note_index + 1}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                            d.applies ? 'bg-purple-500/20 text-purple-300' : 'bg-gray-700 text-gray-400'
                          }`}
                        >
                          {d.directive_type}
                        </span>
                      </div>
                      <p className="text-gray-300">{d.explanation}</p>
                      {d.structured_adjustment && (
                        <pre className="mt-1 text-[11px] font-mono text-emerald-400 bg-[#0c0d10] p-2 rounded border border-[#272832]">
                          {JSON.stringify(d.structured_adjustment, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Battery Specs */}
          <div className="space-y-6">
            <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white border-b border-[#272832] pb-3">Battery Specifications</h3>
              
              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Capacity (kWh)</label>
                <input
                  type="number"
                  value={battery.capacity_kwh}
                  onChange={(e) => setBattery({ ...battery, capacity_kwh: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Initial Energy (kWh)</label>
                <input
                  type="number"
                  value={battery.initial_energy_kwh}
                  onChange={(e) => setBattery({ ...battery, initial_energy_kwh: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Minimum Energy Reserve (kWh)</label>
                <input
                  type="number"
                  value={battery.minimum_energy_kwh}
                  onChange={(e) => setBattery({ ...battery, minimum_energy_kwh: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Max Charge Rate (kWh/h)</label>
                <input
                  type="number"
                  value={battery.max_charge_kwh_per_hour}
                  onChange={(e) => setBattery({ ...battery, max_charge_kwh_per_hour: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-gray-400 font-medium mb-1">Max Discharge Rate (kWh/h)</label>
                <input
                  type="number"
                  value={battery.max_discharge_kwh_per_hour}
                  onChange={(e) => setBattery({ ...battery, max_discharge_kwh_per_hour: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-semibold text-xs rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span>Running MILP Solver & Groq...</span>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Optimize Energy Schedule</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 24-Hour Data Table */}
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white">24-Hour Input Data Schedule (Editable)</h3>
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-xs text-left text-gray-300">
              <thead className="text-[11px] uppercase bg-[#181920] text-gray-400 sticky top-0">
                <tr>
                  <th className="px-3 py-2">Hour</th>
                  <th className="px-3 py-2">Demand (kWh)</th>
                  <th className="px-3 py-2">Solar (kWh)</th>
                  <th className="px-3 py-2">Tariff (BDT/kWh)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#272832]">
                {hours.map((h, idx) => (
                  <tr key={h.hour} className="hover:bg-white/5">
                    <td className="px-3 py-1.5 font-mono text-gray-400">Hour {h.hour}</td>
                    <td className="px-3 py-1.5">
                      <input
                        type="number"
                        value={h.demand_kwh}
                        onChange={(e) => handleHourlyChange(idx, 'demand_kwh', parseFloat(e.target.value) || 0)}
                        className="w-24 bg-[#181920] border border-[#272832] px-2 py-1 rounded text-white font-mono focus:outline-none focus:border-emerald-500"
                      />
                    </td>
                    <td className="px-3 py-1.5">
                      <input
                        type="number"
                        value={h.solar_kwh}
                        onChange={(e) => handleHourlyChange(idx, 'solar_kwh', parseFloat(e.target.value) || 0)}
                        className="w-24 bg-[#181920] border border-[#272832] px-2 py-1 rounded text-white font-mono focus:outline-none focus:border-emerald-500"
                      />
                    </td>
                    <td className="px-3 py-1.5">
                      <input
                        type="number"
                        value={h.tariff_bdt_per_kwh}
                        onChange={(e) => handleHourlyChange(idx, 'tariff_bdt_per_kwh', parseFloat(e.target.value) || 0)}
                        className="w-24 bg-[#181920] border border-[#272832] px-2 py-1 rounded text-white font-mono focus:outline-none focus:border-emerald-500"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </form>
    </div>
  );
};

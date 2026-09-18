import React from 'react';
import { CheckCircle2, Zap, DollarSign, Activity, Sun, Battery, ArrowUpRight } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import { OptimizationResponse } from '../types';

interface ResultsProps {
  result: OptimizationResponse | null;
  onNavigateToOptimize: () => void;
}

export const Results: React.FC<ResultsProps> = ({ result, onNavigateToOptimize }) => {
  if (!result) {
    return (
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-12 text-center space-y-4">
        <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto text-gray-400">
          <Activity className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-white">No Optimization Results Available</h3>
          <p className="text-xs text-gray-400">Please run an energy optimization scenario to view full results and schedule details.</p>
        </div>
        <button
          onClick={onNavigateToOptimize}
          className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg transition-colors"
        >
          Go to Optimize Energy
        </button>
      </div>
    );
  }

  const chartData = result.hourly_plan.map((h) => ({
    hour: `H${h.hour}`,
    Grid: h.grid_kwh,
    Solar: h.solar_used_kwh,
    BatteryLevel: h.battery_energy_after_kwh,
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner Status */}
      <div className="bg-[#121318] border border-emerald-500/30 rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> Validation Status: VALID
            </span>
            <span className="text-xs font-mono text-gray-400">Scenario: {result.scenario_id}</span>
          </div>
          <p className="text-xs text-gray-300 pt-1 leading-relaxed">{result.plan_summary}</p>
        </div>

        <button
          onClick={onNavigateToOptimize}
          className="px-4 py-2 bg-[#181920] hover:bg-white/5 border border-[#272832] text-white text-xs font-semibold rounded-lg transition-colors whitespace-nowrap"
        >
          Optimize Another
        </button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Grid Energy</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">{result.total_grid_kwh.toLocaleString()} kWh</p>
          <p className="text-xs text-gray-400">24-Hour Cumulative Draw</p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">{result.total_cost_bdt.toLocaleString()} BDT</p>
          <p className="text-xs text-emerald-400">MILP Cost Minimized</p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Peak Grid Power</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">{result.peak_grid_kwh} kWh</p>
          <p className="text-xs text-amber-400">Peak Demand Shaved</p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-1">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Final Battery Level</span>
            <Battery className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">
            {result.hourly_plan[23].battery_energy_after_kwh} kWh
          </p>
          <p className="text-xs text-emerald-400">Equal to Initial Level</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grid vs Solar Chart */}
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white">Grid Draw vs Solar Generation (kWh)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#272832" />
                <XAxis dataKey="hour" stroke="#8b8d9e" fontSize={11} />
                <YAxis stroke="#8b8d9e" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#181920', borderColor: '#272832', color: '#fff', fontSize: '12px' }} />
                <Area type="monotone" dataKey="Grid" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.2} strokeWidth={2} />
                <Area type="monotone" dataKey="Solar" stroke="#eab308" fill="#eab308" fillOpacity={0.2} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Battery Level Chart */}
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white">Battery Energy Level (kWh)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#272832" />
                <XAxis dataKey="hour" stroke="#8b8d9e" fontSize={11} />
                <YAxis stroke="#8b8d9e" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#181920', borderColor: '#272832', color: '#fff', fontSize: '12px' }} />
                <Line type="monotone" dataKey="BatteryLevel" stroke="#a855f7" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Hourly Schedule Table */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white">Validated 24-Hour Dispatch Plan</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-gray-300">
            <thead className="text-[11px] uppercase bg-[#181920] text-gray-400">
              <tr>
                <th className="px-4 py-3">Hour</th>
                <th className="px-4 py-3">Grid (kWh)</th>
                <th className="px-4 py-3">Solar Used (kWh)</th>
                <th className="px-4 py-3">Battery Action</th>
                <th className="px-4 py-3">Battery Power (kWh)</th>
                <th className="px-4 py-3">Battery Energy After (kWh)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#272832]">
              {result.hourly_plan.map((h) => (
                <tr key={h.hour} className="hover:bg-white/5">
                  <td className="px-4 py-2.5 font-mono text-gray-400">Hour {h.hour}</td>
                  <td className="px-4 py-2.5 font-mono text-cyan-400 font-medium">{h.grid_kwh}</td>
                  <td className="px-4 py-2.5 font-mono text-yellow-400">{h.solar_used_kwh}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                        h.battery_action === 'charge'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : h.battery_action === 'discharge'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      {h.battery_action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-white">{h.battery_kwh}</td>
                  <td className="px-4 py-2.5 font-mono text-purple-400">{h.battery_energy_after_kwh}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

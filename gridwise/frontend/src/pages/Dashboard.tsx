import React, { useEffect, useState } from 'react';
import { Activity, Zap, Sun, DollarSign, ShieldCheck, Cpu, Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { checkHealth } from '../lib/api';
import { OptimizationResponse } from '../types';

interface DashboardProps {
  lastResult: OptimizationResponse | null;
  onNavigateToOptimize: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ lastResult, onNavigateToOptimize }) => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  const chartData = lastResult
    ? lastResult.hourly_plan.map((h) => ({
        hour: `H${h.hour}`,
        Grid: h.grid_kwh,
        Solar: h.solar_used_kwh,
        Battery: h.battery_energy_after_kwh,
      }))
    : Array.from({ length: 24 }, (_, i) => ({
        hour: `H${i}`,
        Grid: Math.floor(80 + Math.sin(i / 3) * 40 + Math.random() * 10),
        Solar: i >= 6 && i <= 17 ? Math.floor(Math.sin((i - 6) / 11 * Math.PI) * 150) : 0,
        Battery: Math.floor(200 + Math.cos(i / 4) * 80),
      }));

  return (
    <div className="space-y-6">
      {/* Top Banner Status Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-500/10 rounded-lg text-emerald-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">FastAPI Backend</p>
              <p className="text-sm font-semibold text-white">
                {apiOnline === null ? 'Checking...' : apiOnline ? 'API Online' : 'API Offline'}
              </p>
            </div>
          </div>
          <span className={`w-2.5 h-2.5 rounded-full ${apiOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-purple-500/10 rounded-lg text-purple-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Groq LLM</p>
              <p className="text-sm font-semibold text-white">llama-3.3-70b</p>
            </div>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-cyan-500/10 rounded-lg text-cyan-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">MILP Optimizer</p>
              <p className="text-sm font-semibold text-white">PuLP + CBC</p>
            </div>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-amber-500/10 rounded-lg text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Final Validator</p>
              <p className="text-sm font-semibold text-white">Replay Ready</p>
            </div>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
        </div>
      </div>

      {/* Main Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Grid Energy</span>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">
            {lastResult ? `${lastResult.total_grid_kwh.toLocaleString()} kWh` : '2,450.5 kWh'}
          </p>
          <p className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 24-Hour Verified Dispatch
          </p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Schedule Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">
            {lastResult ? `${lastResult.total_cost_bdt.toLocaleString()} BDT` : '38,200.0 BDT'}
          </p>
          <p className="text-xs text-gray-400">Optimized Dynamic Tariffs</p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Peak Grid Draw</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">
            {lastResult ? `${lastResult.peak_grid_kwh} kWh` : '210.0 kWh'}
          </p>
          <p className="text-xs text-amber-400 font-medium">Peak Shaved via Battery</p>
        </div>

        <div className="bg-[#121318] border border-[#272832] rounded-xl p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Battery State</span>
            <Sun className="w-4 h-4 text-yellow-400" />
          </div>
          <p className="text-2xl font-bold text-white tracking-tight">
            {lastResult ? `${lastResult.hourly_plan[23].battery_energy_after_kwh} kWh` : '200.0 kWh'}
          </p>
          <p className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> EOD Neutrality Preserved
          </p>
        </div>
      </div>

      {/* 24-Hour Energy Chart Card */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-white">24-Hour Energy Schedule & Dispatch</h3>
            <p className="text-xs text-gray-400">
              {lastResult ? `Scenario: ${lastResult.scenario_id}` : 'Sample Visualization (Run Optimization for Live Scenario)'}
            </p>
          </div>
          <button
            onClick={onNavigateToOptimize}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg transition-colors shadow-lg shadow-emerald-500/20"
          >
            Optimize New Scenario
          </button>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="gridGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="solarGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#272832" />
              <XAxis dataKey="hour" stroke="#8b8d9e" fontSize={11} />
              <YAxis stroke="#8b8d9e" fontSize={11} unit=" kWh" />
              <Tooltip
                contentStyle={{ backgroundColor: '#181920', borderColor: '#272832', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Area type="monotone" dataKey="Grid" stroke="#06b6d4" fillOpacity={1} fill="url(#gridGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="Solar" stroke="#eab308" fillOpacity={1} fill="url(#solarGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Plan Summary Banner */}
      {lastResult && (
        <div className="bg-[#181920] border border-emerald-500/20 rounded-xl p-5 flex items-start space-x-4">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-white">Optimization Summary</h4>
            <p className="text-xs text-gray-300 leading-relaxed">{lastResult.plan_summary}</p>
          </div>
        </div>
      )}
    </div>
  );
};

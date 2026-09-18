import React, { useState } from 'react';
import { Terminal, Send, CheckCircle2, XCircle, Clock, Copy } from 'lucide-react';
import { checkHealth, optimizeEnergy } from '../lib/api';
import { PUBLIC_SAMPLES } from '../lib/sampleCases';
import { OptimizationResponse } from '../types';

export const APITest: React.FC = () => {
  const [healthResult, setHealthResult] = useState<{ status: string } | null>(null);
  const [healthStatus, setHealthStatus] = useState<number | null>(null);
  const [healthTime, setHealthTime] = useState<number | null>(null);

  const [optRequestJson, setOptRequestJson] = useState<string>(
    JSON.stringify(PUBLIC_SAMPLES[0], null, 2)
  );
  const [optResponse, setOptResponse] = useState<OptimizationResponse | null>(null);
  const [optStatus, setOptStatus] = useState<number | null>(null);
  const [optTime, setOptTime] = useState<number | null>(null);
  const [optError, setOptError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleTestHealth = async () => {
    const start = performance.now();
    try {
      const res = await checkHealth();
      const end = performance.now();
      setHealthResult(res);
      setHealthStatus(200);
      setHealthTime(Math.round(end - start));
    } catch (err: any) {
      setHealthResult({ status: 'error' });
      setHealthStatus(500);
    }
  };

  const handleLoadSample = (sampleId: string) => {
    const found = PUBLIC_SAMPLES.find((s) => s.scenario_id === sampleId);
    if (found) {
      setOptRequestJson(JSON.stringify(found, null, 2));
    }
  };

  const handleSendOptimize = async () => {
    setLoading(true);
    setOptError(null);
    setOptResponse(null);
    const start = performance.now();

    try {
      const parsed = JSON.parse(optRequestJson);
      const res = await optimizeEnergy(parsed);
      const end = performance.now();
      setOptResponse(res);
      setOptStatus(200);
      setOptTime(Math.round(end - start));
    } catch (err: any) {
      const end = performance.now();
      setOptError(err.message || 'Request failed');
      setOptStatus(err.message.includes('400') ? 400 : err.message.includes('422') ? 422 : 500);
      setOptTime(Math.round(end - start));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-1">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Terminal className="w-5 h-5 text-cyan-400" /> Developer & Judge API Test Console
        </h2>
        <p className="text-xs text-gray-400">
          Directly test REST API endpoints, response latencies, HTTP status codes, and inspect raw JSON payloads.
        </p>
      </div>

      {/* Section 1: Health Test */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded text-xs font-mono font-bold">
              GET
            </span>
            <span className="text-sm font-mono text-white">/health</span>
          </div>
          <button
            onClick={handleTestHealth}
            className="px-4 py-1.5 bg-[#181920] hover:bg-white/5 border border-[#272832] text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Test Health Endpoint
          </button>
        </div>

        {healthStatus !== null && (
          <div className="flex items-center space-x-4 text-xs pt-2 border-t border-[#272832]">
            <span
              className={`px-2 py-0.5 rounded font-mono font-bold ${
                healthStatus === 200 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
              }`}
            >
              HTTP {healthStatus} OK
            </span>
            <span className="text-gray-400 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-gray-500" /> {healthTime} ms
            </span>
            <span className="text-gray-300 font-mono">{JSON.stringify(healthResult)}</span>
          </div>
        )}
      </div>

      {/* Section 2: POST /optimize-energy Test */}
      <div className="bg-[#121318] border border-[#272832] rounded-xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="px-2.5 py-1 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded text-xs font-mono font-bold">
              POST
            </span>
            <span className="text-sm font-mono text-white">/optimize-energy</span>
          </div>

          <div className="flex items-center space-x-3">
            <select
              onChange={(e) => handleLoadSample(e.target.value)}
              className="bg-[#181920] border border-[#272832] text-white text-xs rounded-lg px-3 py-1.5 font-mono focus:outline-none"
            >
              <option value="">Load Sample Scenario...</option>
              {PUBLIC_SAMPLES.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.scenario_id}
                </option>
              ))}
            </select>

            <button
              onClick={handleSendOptimize}
              disabled={loading}
              className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{loading ? 'Sending...' : 'Send Request'}</span>
            </button>
          </div>
        </div>

        {/* Request & Response Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
          {/* JSON Request Input */}
          <div className="space-y-2">
            <label className="text-xs text-gray-400 font-medium">Request Payload (JSON)</label>
            <textarea
              value={optRequestJson}
              onChange={(e) => setOptRequestJson(e.target.value)}
              rows={16}
              className="w-full bg-[#0c0d10] border border-[#272832] text-emerald-400 font-mono text-xs rounded-lg p-3 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* JSON Response Viewer */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-400 font-medium">Response Output</label>
              {optStatus !== null && (
                <div className="flex items-center space-x-3 text-xs">
                  <span
                    className={`px-2 py-0.5 rounded font-mono font-bold ${
                      optStatus === 200 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                    }`}
                  >
                    HTTP {optStatus}
                  </span>
                  <span className="text-gray-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> {optTime} ms
                  </span>
                </div>
              )}
            </div>

            <div className="w-full h-[310px] bg-[#0c0d10] border border-[#272832] rounded-lg p-3 overflow-y-auto font-mono text-xs">
              {optError ? (
                <div className="text-rose-400 space-y-1">
                  <p className="font-semibold">Error Response:</p>
                  <p>{optError}</p>
                </div>
              ) : optResponse ? (
                <pre className="text-purple-300">{JSON.stringify(optResponse, null, 2)}</pre>
              ) : (
                <span className="text-gray-600">Click "Send Request" to execute API call...</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

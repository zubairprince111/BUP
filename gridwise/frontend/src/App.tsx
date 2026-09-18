import React, { useState } from 'react';
import { LayoutDashboard, SlidersHorizontal, BarChart3, Terminal, Shield, Zap, ExternalLink } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { OptimizeEnergy } from './pages/OptimizeEnergy';
import { Results } from './pages/Results';
import { APITest } from './pages/APITest';
import { OptimizationResponse } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'optimize' | 'results' | 'api-test'>('dashboard');
  const [lastResult, setLastResult] = useState<OptimizationResponse | null>(null);

  const handleOptimizationSuccess = (result: OptimizationResponse) => {
    setLastResult(result);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen bg-[#0c0d10] text-gray-200 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-[#272832] bg-[#121318]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white tracking-tight text-base">GridWise</span>
                <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-semibold rounded-full uppercase">
                  BUP Fest 2026
                </span>
              </div>
              <p className="text-[11px] text-gray-400">Smart Energy Schedule Optimization Platform</p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="flex space-x-1 bg-[#181920] p-1 rounded-xl border border-[#272832]">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-[#272832] text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab('optimize')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'optimize'
                  ? 'bg-[#272832] text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Optimize Energy</span>
            </button>

            <button
              onClick={() => setActiveTab('results')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'results'
                  ? 'bg-[#272832] text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Results</span>
            </button>

            <button
              onClick={() => setActiveTab('api-test')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                activeTab === 'api-test'
                  ? 'bg-[#272832] text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span>API Console</span>
            </button>
          </nav>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden lg:flex items-center space-x-1.5 text-xs text-gray-400 hover:text-white transition-colors"
          >
            <span>Swagger Docs</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {activeTab === 'dashboard' && (
          <Dashboard
            lastResult={lastResult}
            onNavigateToOptimize={() => setActiveTab('optimize')}
          />
        )}
        {activeTab === 'optimize' && (
          <OptimizeEnergy onSuccess={handleOptimizationSuccess} />
        )}
        {activeTab === 'results' && (
          <Results
            result={lastResult}
            onNavigateToOptimize={() => setActiveTab('optimize')}
          />
        )}
        {activeTab === 'api-test' && <APITest />}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#272832] bg-[#121318] py-4 text-xs text-gray-500 text-center">
        <p>GridWise Energy Optimization Platform — BUP CSE Fest 2026 Hackathon Official Submission</p>
      </footer>
    </div>
  );
};

export default App;

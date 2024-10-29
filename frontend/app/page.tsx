'use client';

import { useState } from 'react';
import LoadStrategyModal from '@/components/LoadStrategyModal';
import RuleBuilder from '@/components/RuleBuilder';
import BacktestForm from '@/components/BacktestForm';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Toast from '@/components/Toast';

// Define the Rule type
interface Rule {
  type: 'condition' | 'weight';
  indicator?: {
    name: string;
    params: any[];
    symbol: string;
  };
  comparator?: string;
  value?: number;
  if_true: Rule[];
  if_false: Rule[];
}

export default function Home() {
  const [strategyName, setStrategyName] = useState("Untitled Strategy");
  const [isLoadModalOpen, setIsLoadModalOpen] = useState(false);
  const [rules, setRules] = useState<Rule>({
    type: 'condition',
    indicator: {
      name: 'sma_price',
      params: [1],
      symbol: 'SPXL'
    },
    comparator: '>=',
    value: 0,
    if_true: [],
    if_false: []
  });
  const currentUserId = 1; // This should come from your auth system
  const [isJsonExpanded, setIsJsonExpanded] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error';
  } | null>(null);

  const handleSaveStrategy = async () => {
    try {
      const response = await fetch('http://localhost:8000/save_strategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: strategyName,
          rules: {
            rules: rules,
          },
          user_id: 1,
        }),
      });

      if (response.ok) {
        setToast({ message: 'Strategy saved successfully!', type: 'success' });
      } else {
        throw new Error('Failed to save strategy');
      }
    } catch (error) {
      console.error('Error saving strategy:', error);
      setToast({ 
        message: 'Error saving strategy: ' + (error as Error).message, 
        type: 'error' 
      });
    }
  };

  const handleLoadStrategy = async (id: number, requiresCopy: boolean) => {
    try {
      const response = await fetch(`http://localhost:8000/get_strategy?strategy_id=${id}`);
      if (!response.ok) {
        throw new Error('Failed to load strategy');
      }
      
      const strategy = await response.json();
      
      if (requiresCopy) {
        setStrategyName(strategy.name + ' (Copy)');
      } else {
        setStrategyName(strategy.name);
      }
      
      setRules(strategy.rules.rules);
      setIsLoadModalOpen(false);
      setToast({ message: 'Strategy loaded successfully!', type: 'success' });
    } catch (error) {
      console.error('Error loading strategy:', error);
      setToast({ 
        message: 'Error loading strategy: ' + (error as Error).message, 
        type: 'error' 
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
      <main className="container mx-auto px-6 py-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div className="flex-1 w-full md:w-auto">
            <input
              type="text"
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
              className="bg-gray-800/50 text-white text-xl font-semibold px-4 py-3 rounded-xl 
                        border border-gray-700/50 focus:outline-none focus:ring-2 focus:ring-blue-500/50 
                        w-full max-w-md backdrop-blur-sm transition-all duration-200
                        hover:border-gray-600"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <button 
              onClick={handleSaveStrategy}
              className="px-4 py-2.5 bg-green-600/90 hover:bg-green-600 rounded-lg transition-all
                       duration-200 font-medium text-sm flex items-center gap-2 hover:shadow-lg
                       hover:shadow-green-500/20">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
              Save Strategy
            </button>
            <button 
              onClick={() => setIsLoadModalOpen(true)}
              className="px-4 py-2.5 bg-purple-600/90 hover:bg-purple-600 rounded-lg transition-all
                        duration-200 font-medium text-sm flex items-center gap-2 hover:shadow-lg
                        hover:shadow-purple-500/20">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Load Strategy
            </button>
          </div>
        </div>

        {/* Strategy Builder Section */}
        <div className="flex flex-col gap-8">
          {/* Rules Panel */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50
                        shadow-xl shadow-black/20">
            <div className="p-6 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Strategy Rules
              </h2>
            </div>
            <div className="p-6">
              <RuleBuilder 
                rules={rules} 
                onChange={(newRules) => setRules(newRules)} 
              />
            </div>
          </div>

          {/* Preview Panel */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50
                        shadow-xl shadow-black/20">
            <div className="p-6 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Strategy Preview
              </h2>
            </div>
            <div className="p-6">
              <BacktestForm 
                rules={rules} 
                strategyName={strategyName}
              />
            </div>
          </div>

          {/* JSON Preview Panel */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50
                        shadow-xl shadow-black/20">
            <div className="p-6 border-b border-gray-700/50">
              <button 
                onClick={() => setIsJsonExpanded(!isJsonExpanded)}
                className="w-full flex items-center justify-between text-xl font-semibold text-white group"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
                  </svg>
                  Generated Rules JSON
                </div>
                <svg 
                  className={`w-5 h-5 transition-transform duration-200 ${isJsonExpanded ? 'rotate-180' : ''}`}
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            {isJsonExpanded && (
              <div className="p-6">
                <pre className="bg-gray-900/50 rounded-lg p-4 overflow-x-auto text-sm text-gray-300">
                  {JSON.stringify({
                    name: "Untitled Strategy",
                    rules: rules
                  }, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Load Strategy Modal */}
        <LoadStrategyModal 
          isOpen={isLoadModalOpen}
          onClose={() => setIsLoadModalOpen(false)}
          onStrategySelect={handleLoadStrategy}
          currentUserId={currentUserId}
        />

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </main>
    </div>
  );
} 
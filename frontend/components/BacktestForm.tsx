'use client';

import { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface Rule {
  type: 'condition' | 'weight';
  name?: string;
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

interface BacktestFormProps {
  rules: Rule;
  strategyName: string;
}

// Update the interface for the API response
interface BacktestResults {
  daily_values: Array<{
    date: string;
    portfolio_value: number;
    cash: number;
    daily_return: number | null;
  }>;
  spy_values: Array<{
    date: string;
    SPY: number;
  }>;
  stats: {
    'Total Return': number;
    'Annualized Return': number;
    'Max Drawdown': number;
    'Volatility': number;
    'Calmar Ratio': number;
    'Sharpe Ratio': number;
    'Sortino Ratio': number;
    'Ulcer Index': number;
    'UPI': number;
    'Beta': number;
    [key: string]: number;
  };
}

export default function BacktestForm({ rules, strategyName }: BacktestFormProps) {
  // Get current date and date from one year ago
  const today = new Date();
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(today.getFullYear() - 1);

  // Format dates to YYYY-MM-DD
  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState({
    startDate: formatDate(oneYearAgo),
    endDate: formatDate(today),
    startingCapital: 10000,
    monthly: 0,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [backtestResults, setBacktestResults] = useState<BacktestResults | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Add check for strategy name
    if (!strategyName) {
      alert('Please enter a strategy name');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Strategy Name:', strategyName); // Debug log
      const requestBody = {
        name: strategyName,
        rules: {
          type: rules.type,
          indicator: rules.indicator,
          comparator: rules.comparator,
          value: rules.value,
          if_true: rules.if_true,
          if_false: rules.if_false
        },
        start_date: formData.startDate,
        end_date: formData.endDate,
        starting_capital: formData.startingCapital,
        monthly_investment: formData.monthly
      };
      
      console.log('Request Body:', JSON.stringify(requestBody)); // Debug log

      const response = await fetch('http://localhost:8000/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to run backtest');
      }

      const data = await response.json();
      setBacktestResults(data);
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest: ' + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={formData.startDate}
              onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
              className="w-full bg-gray-700/50 text-white px-3 py-2 rounded-lg border border-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={formData.endDate}
              onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
              className="w-full bg-gray-700/50 text-white px-3 py-2 rounded-lg border border-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Starting Capital
            </label>
            <input
              type="number"
              value={formData.startingCapital}
              onChange={(e) => setFormData({ ...formData, startingCapital: Number(e.target.value) })}
              className="w-full bg-gray-700/50 text-white px-3 py-2 rounded-lg border border-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Monthly Investment
            </label>
            <input
              type="number"
              value={formData.monthly}
              onChange={(e) => setFormData({ ...formData, monthly: Number(e.target.value) })}
              className="w-full bg-gray-700/50 text-white px-3 py-2 rounded-lg border border-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium 
                     transition-colors duration-200 flex items-center gap-2 disabled:opacity-50 
                     disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run Backtest
              </>
            )}
          </button>
        </div>
      </form>

      {/* Chart section */}
      <div className="mt-6 p-4 bg-gray-800 rounded-lg">
        {/* Loading state */}
        {isLoading ? (
          <div className="relative" style={{ height: '400px' }}>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
              <div className="mt-4 text-gray-300 text-sm">
                Running backtest...
              </div>
              <div className="mt-2 text-gray-400 text-xs">
                This may take a few moments
              </div>
            </div>
          </div>
        ) : backtestResults && (
          <>
            {backtestResults.daily_values.length === 0 || backtestResults.spy_values.length === 0 ? (
              <div className="relative" style={{ height: '400px' }}>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-red-400 text-lg font-medium mb-2">
                    Unable to display backtest results
                  </div>
                  <div className="text-gray-400 text-sm">
                    Possible causes:
                    <ul className="mt-2 list-disc list-inside">
                      <li>Invalid date range selected</li>
                      <li>Incorrect symbol selection in strategy</li>
                      <li>Invalid strategy configuration</li>
                      <li>No trades were executed during the period</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <Line
                data={{
                  labels: backtestResults.daily_values.map(d => d.date),
                  datasets: [
                    {
                      label: 'Portfolio',
                      data: backtestResults.daily_values.map(d => d.portfolio_value),
                      borderColor: 'rgb(59, 130, 246)',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      tension: 0.1,
                      fill: true,
                    },
                    {
                      label: 'SPY',
                      data: backtestResults.spy_values.map(d => d.SPY),
                      borderColor: 'rgb(234, 179, 8)',
                      backgroundColor: 'rgba(234, 179, 8, 0.1)',
                      tension: 0.1,
                      fill: true,
                    }
                  ],
                }}
                options={{
                  responsive: true,
                  interaction: {
                    mode: 'index' as const,
                    intersect: false,
                  },
                  plugins: {
                    legend: {
                      position: 'top' as const,
                      labels: {
                        color: 'white',
                      },
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          let label = context.dataset.label || '';
                          if (label) {
                            label += ': ';
                          }
                          if (context.parsed.y !== null) {
                            label += new Intl.NumberFormat('en-US', {
                              style: 'currency',
                              currency: 'USD'
                            }).format(context.parsed.y);
                          }
                          return label;
                        }
                      }
                    }
                  },
                  scales: {
                    x: {
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                      },
                      ticks: {
                        color: 'white',
                        maxRotation: 45,
                        minRotation: 45,
                      },
                    },
                    y: {
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                      },
                      ticks: {
                        color: 'white',
                        callback: function(value) {
                          return new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD',
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          }).format(value as number);
                        }
                      },
                    },
                  },
                }}
              />
            )}
          </>
        )}

        {/* Stats display - Always visible */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Total Return</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                `${backtestResults.stats['Total Return'].toFixed(2)}%` : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Annualized Return</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                `${backtestResults.stats['Annualized Return'].toFixed(2)}%` : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Max Drawdown</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                `${backtestResults.stats['Max Drawdown'].toFixed(2)}%` : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Volatility</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                `${backtestResults.stats['Volatility'].toFixed(2)}%` : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Sharpe Ratio</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                backtestResults.stats['Sharpe Ratio'].toFixed(2) : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Sortino Ratio</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                backtestResults.stats['Sortino Ratio'].toFixed(2) : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Beta</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                backtestResults.stats['Beta'].toFixed(2) : 
                '---'}
            </div>
          </div>
          <div className="bg-gray-700/50 p-3 rounded-lg">
            <div className="text-gray-400 text-sm">Calmar Ratio</div>
            <div className="text-white font-semibold">
              {(!isLoading && backtestResults && backtestResults.daily_values.length > 0) ? 
                backtestResults.stats['Calmar Ratio'].toFixed(2) : 
                '---'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 
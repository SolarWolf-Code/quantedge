import { useState, useRef } from 'react';
import RuleTypeMenu from './RuleTypeMenu';

interface Rule {
  type: 'condition' | 'weight';
  indicator?: {
    name: string;
    params: any[];
    symbol: string;
  };
  comparator?: string;
  value?: number;
  if_true?: Rule[];
  if_false?: Rule[];
  weight_type?: 'equal' | 'weighted';
  assets?: { symbol: string; weight?: number }[];
}

interface RuleBuilderProps {
  rules: Rule;
  onChange: (rules: Rule) => void;
}

interface MenuState {
  isOpen: boolean;
  position: { x: number; y: number };
  parentRule: Rule;
  branch: 'if_true' | 'if_false';
}

interface Indicator {
  name: string;
  params: {
    name: string;
    type: 'number' | 'string';
  }[];
}

const INDICATORS: Indicator[] = [
  { name: 'ema', params: [{ name: 'period', type: 'number' }] },
  { 
    name: 'macd', 
    params: [
      { name: 'fast_period', type: 'number' },
      { name: 'slow_period', type: 'number' },
      { name: 'signal_period', type: 'number' }
    ] 
  },
  { name: 'sma_price', params: [{ name: 'period', type: 'number' }] },
  { name: 'fibonacci_retracement', params: [{ name: 'period', type: 'number' }] },
  { name: 'adx', params: [{ name: 'period', type: 'number' }] },
  { name: 'standard_deviation_price', params: [{ name: 'period', type: 'number' }] },
  { name: 'stochastic_oscillator', params: [{ name: 'period', type: 'number' }] },
  { name: 'sma_return', params: [{ name: 'period', type: 'number' }] },
  { name: 'standard_deviation_return', params: [{ name: 'period', type: 'number' }] },
  { name: 'max_drawdown', params: [{ name: 'period', type: 'number' }] },
  { name: 'current_price', params: [] },
  { name: 'cumulative_return', params: [{ name: 'period', type: 'number' }] }
];

export default function RuleBuilder({ rules, onChange }: RuleBuilderProps) {
  const [menu, setMenu] = useState<MenuState | null>(null);
  const assetRefs = useRef<(HTMLInputElement | null)[]>([]);

  const addNode = (parentRule: Rule, branch: 'if_true' | 'if_false', type: 'condition' | 'weight') => {
    const newRule: Rule = type === 'condition' ? {
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
    } : {
      type: 'weight',
      weight_type: 'equal',
      assets: []
    };

    parentRule[branch] = [...(parentRule[branch] || []), newRule];
    onChange({ ...rules });
  };

  const handleAddClick = (e: React.MouseEvent, parentRule: Rule, branch: 'if_true' | 'if_false') => {
    const rect = e.currentTarget.getBoundingClientRect();
    
    setMenu({
      isOpen: true,
      position: { 
        x: rect.left + (rect.width / 2),
        y: rect.bottom + window.scrollY + 5
      },
      parentRule,
      branch
    });
  };

  const deleteNode = (parentRule: Rule, branch: 'if_true' | 'if_false', index: number) => {
    if (parentRule[branch]) {
      parentRule[branch]?.splice(index, 1);
      onChange({ ...rules });
    }
  };

  const addAssetNode = (parentRule: Rule) => {
    if (parentRule.type === 'weight') {
      const newAsset = { symbol: '', weight: parentRule.weight_type === 'equal' ? 100 / (parentRule.assets?.length + 1) : 0 };
      parentRule.assets = [...(parentRule.assets || []), newAsset];
      if (parentRule.weight_type === 'equal') {
        distributeEqualWeights(parentRule.assets);
      }
      onChange({ ...rules });

      // Focus the last added asset input
      setTimeout(() => {
        const lastIndex = parentRule.assets.length - 1;
        assetRefs.current[lastIndex]?.focus();
      }, 0);
    }
  };

  const distributeEqualWeights = (assets: { symbol: string; weight?: number }[]) => {
    const equalWeight = 100 / assets.length;
    assets.forEach(asset => asset.weight = equalWeight);
  };

  const validateWeights = (assets: { symbol: string; weight?: number }[]) => {
    const totalWeight = assets.reduce((sum, asset) => sum + (asset.weight || 0), 0);
    return totalWeight === 100;
  };

  const renderNode = (rule: Rule, depth: number = 0, parentRule?: Rule, branch?: 'if_true' | 'if_false', index?: number) => {
    return (
      <div className="mt-4">
        <div className="flex flex-col">
          {/* Node Content */}
          <div className="flex items-start">
            {/* Tree Line */}
            {depth > 0 && (
              <div className="flex items-center">
                <div className="w-8 h-8 -mt-4 border-l-2 border-b-2 border-gray-600 rounded-bl-lg" />
              </div>
            )}

            {/* Node Box */}
            <div className="flex-grow">
              <div className="bg-blue-500/20 rounded-lg">
                <div className={`${rule.type === 'condition' ? 'bg-blue-600/70' : 'bg-green-600/70'} p-4 rounded-lg`}>
                  <div className="flex items-center justify-between gap-4">
                    {/* Left side content */}
                    <div className="flex-grow">
                      {rule.type === 'condition' ? (
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-blue-400">If</span>
                          <select 
                            className="bg-gray-600 rounded px-2 py-1"
                            value={rule.indicator?.name}
                            onChange={(e) => {
                              rule.indicator = {
                                name: e.target.value,
                                params: INDICATORS.find(i => i.name === e.target.value)?.params.map(() => 0) || [],
                                symbol: rule.indicator?.symbol || 'SPXL'
                              };
                              onChange({ ...rules });
                            }}
                          >
                            {INDICATORS.map(indicator => (
                              <option key={indicator.name} value={indicator.name}>
                                {indicator.name.replace(/_/g, ' ').toUpperCase()}
                              </option>
                            ))}
                          </select>
                          
                          <input
                            type="text"
                            className="bg-gray-600 rounded px-2 py-1 w-24"
                            placeholder="Symbol"
                            value={rule.indicator?.symbol}
                            onChange={(e) => {
                              if (rule.indicator) {
                                rule.indicator.symbol = e.target.value.toUpperCase();
                                onChange({ ...rules });
                              }
                            }}
                          />

                          {rule.indicator && INDICATORS.find(i => i.name === rule.indicator.name)?.params.map((param, idx) => (
                            <input
                              key={param.name}
                              type="number"
                              className="bg-gray-600 rounded px-2 py-1 w-20"
                              placeholder={param.name.replace(/_/g, ' ')}
                              value={rule.indicator.params[idx]}
                              onChange={(e) => {
                                rule.indicator.params[idx] = parseFloat(e.target.value) || 0;
                                onChange({ ...rules });
                              }}
                            />
                          ))}

                          <select 
                            className="bg-gray-600 rounded px-2 py-1"
                            value={rule.comparator}
                            onChange={(e) => {
                              rule.comparator = e.target.value;
                              onChange({ ...rules });
                            }}
                          >
                            <option value=">=">&gt;=</option>
                            <option value="<=">&lt;=</option>
                            <option value=">">&gt;</option>
                            <option value="<">&lt;</option>
                          </select>

                          <input 
                            type="number"
                            className="bg-gray-600 rounded px-2 py-1 w-20"
                            value={rule.value}
                            onChange={(e) => {
                              rule.value = parseFloat(e.target.value) || 0;
                              onChange({ ...rules });
                            }}
                          />
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="text-green-400">Weight</span>
                          <select 
                            className="bg-gray-600 rounded px-2 py-1"
                            value={rule.weight_type}
                            onChange={(e) => {
                              rule.weight_type = e.target.value as 'equal' | 'weighted';
                              if (rule.weight_type === 'equal') {
                                distributeEqualWeights(rule.assets || []);
                              }
                              onChange({ ...rules });
                            }}
                          >
                            <option value="equal">Equal</option>
                            <option value="weighted">Weighted</option>
                          </select>
                        </div>
                      )}
                    </div>

                    {/* Right side delete button */}
                    {parentRule && branch && typeof index === 'number' && (
                      <div className="flex-shrink-0">
                        <button
                          onClick={() => deleteNode(parentRule, branch, index)}
                          className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-sm flex items-center gap-1 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Children Container */}
          <div className="flex">
            {/* Vertical Line for Children */}
            {((rule.type === 'condition' && (rule.if_true?.length || rule.if_false?.length)) || 
              (rule.type === 'weight' && rule.assets?.length)) && (
              <div className="w-8 border-l-2 border-gray-600" />
            )}

            {/* Children Content */}
            <div className="flex-grow">
              {/* Asset Nodes */}
              {rule.type === 'weight' && (
                <div>
                  {rule.assets?.map((asset, idx) => (
                    <div key={idx} className="flex items-start mt-4">
                      <div className="w-8 h-8 border-l-2 border-b-2 border-gray-600 rounded-bl-lg" />
                      <div className="flex-grow ml-2 bg-[#FF8C00]/60 p-2 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex-grow flex items-center gap-2">
                            <input
                              ref={el => assetRefs.current[idx] = el}
                              type="text"
                              className="bg-gray-600 rounded px-2 py-1"
                              placeholder="Ticker"
                              value={asset.symbol}
                              onChange={(e) => {
                                asset.symbol = e.target.value.toUpperCase();
                                onChange({ ...rules });
                              }}
                            />
                            {rule.weight_type === 'weighted' && (
                              <input
                                type="number"
                                className="bg-gray-600 rounded px-2 py-1 w-20"
                                placeholder="Weight"
                                value={asset.weight}
                                onChange={(e) => {
                                  asset.weight = parseFloat(e.target.value);
                                  onChange({ ...rules });
                                }}
                              />
                            )}
                          </div>
                          <div className="flex-shrink-0">
                            <button
                              onClick={() => {
                                if (rule.assets) {
                                  rule.assets.splice(idx, 1);
                                  if (rule.weight_type === 'equal' && rule.assets.length > 0) {
                                    distributeEqualWeights(rule.assets);
                                  }
                                  onChange({ ...rules });
                                }
                              }}
                              className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-sm flex items-center gap-1 transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {/* Add Asset button */}
                  <button
                    onClick={() => addAssetNode(rule)}
                    className="mt-2 ml-8 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add Asset
                  </button>
                  {rule.weight_type === 'weighted' && !validateWeights(rule.assets || []) && (
                    <div className="text-red-500 text-sm mt-2 ml-8">
                      Total weight must equal 100.
                    </div>
                  )}
                </div>
              )}

              {/* Condition branches */}
              {rule.type === 'condition' && (
                <>
                  {/* True branch */}
                  <div>
                    {rule.if_true?.map((childRule, idx) => (
                      <div key={idx}>
                        {renderNode(childRule, depth + 1, rule, 'if_true', idx)}
                      </div>
                    ))}
                    {rule.if_true?.length === 0 && (
                      <button
                        onClick={(e) => handleAddClick(e, rule, 'if_true')}
                        className="mt-2 ml-8 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Add Rule
                      </button>
                    )}
                  </div>

                  {/* Else branch */}
                  <div className="mt-4">
                    <div className="flex items-start">
                      {depth > 0 && (
                        <div className="flex items-center">
                          <div className="w-8 h-8 -mt-4 border-l-2 border-b-2 border-gray-600 rounded-bl-lg" />
                        </div>
                      )}
                      <div className="flex-grow">
                        <div className="bg-blue-500/20 rounded-lg">
                          <div className="bg-blue-600/70 p-4 rounded-lg">
                            <div className="text-blue-400">Else</div>
                          </div>
                        </div>
                        {rule.if_false?.map((childRule, idx) => (
                          <div key={idx}>
                            {renderNode(childRule, depth + 1, rule, 'if_false', idx)}
                          </div>
                        ))}
                        {rule.if_false?.length === 0 && (
                          <button
                            onClick={(e) => handleAddClick(e, rule, 'if_false')}
                            className="mt-2 ml-8 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Add Rule
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="text-white" style={{ position: 'relative', zIndex: 0 }}>
      {renderNode(rules)}
      {menu && (
        <RuleTypeMenu
          position={menu.position}
          onSelect={(type) => {
            addNode(menu.parentRule, menu.branch, type);
            setMenu(null);
          }}
          onClose={() => setMenu(null)}
        />
      )}
    </div>
  );
} 
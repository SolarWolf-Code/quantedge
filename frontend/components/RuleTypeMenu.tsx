import Portal from './Portal';

interface RuleTypeMenuProps {
  onSelect: (type: 'condition' | 'weight') => void;
  onClose: () => void;
  position: { x: number; y: number };
}

export default function RuleTypeMenu({ onSelect, onClose, position }: RuleTypeMenuProps) {
  return (
    <Portal>
      <div 
        className="fixed inset-0 bg-transparent" 
        style={{ zIndex: 9998 }}
        onClick={onClose}
      />
      <div 
        className="fixed bg-gray-800 rounded-lg shadow-xl border border-gray-700 py-1"
        style={{ 
          top: `${position.y}px`,
          left: `${position.x}px`,
          transform: 'translateX(-50%)',
          zIndex: 9999
        }}
      >
        <button
          onClick={() => onSelect('condition')}
          className="w-full px-4 py-2 text-left hover:bg-gray-700 flex items-center gap-2 min-w-[160px] whitespace-nowrap"
        >
          <svg className="w-4 h-4 text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          If Block
        </button>
        <button
          onClick={() => onSelect('weight')}
          className="w-full px-4 py-2 text-left hover:bg-gray-700 flex items-center gap-2 whitespace-nowrap"
        >
          <svg className="w-4 h-4 text-green-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
          Weight Block
        </button>
      </div>
    </Portal>
  );
} 
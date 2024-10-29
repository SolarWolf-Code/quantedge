import { useEffect, useState } from 'react';

interface Strategy {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  user_id: number;
}

interface LoadStrategyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStrategySelect: (id: number, requiresCopy: boolean) => void;
  currentUserId: number;
}

export default function LoadStrategyModal({ isOpen, onClose, onStrategySelect, currentUserId }: LoadStrategyModalProps) {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadStrategies();
    }
  }, [isOpen]);

  const loadStrategies = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/get_all_strategies');
      if (!response.ok) {
        throw new Error('Failed to load strategies');
      }
      const data = await response.json();
      setStrategies(data);
    } catch (error) {
      console.error('Error loading strategies:', error);
      setError((error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the strategy selection
    
    if (!confirm('Are you sure you want to delete this strategy?')) {
      return;
    }

    setDeletingId(id);
    try {
      const response = await fetch(`http://localhost:8000/delete_strategy?strategy_id=${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete strategy');
      }
      
      // Remove the strategy from the local state
      setStrategies(strategies.filter(strategy => strategy.id !== id));
    } catch (error) {
      console.error('Error deleting strategy:', error);
      alert('Error deleting strategy: ' + (error as Error).message);
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-4">Load Strategy</h2>
        
        {loading ? (
          <div className="text-gray-400 text-center py-8">Loading strategies...</div>
        ) : error ? (
          <div className="text-red-400 text-center py-8">{error}</div>
        ) : strategies.length === 0 ? (
          <div className="text-gray-400 text-center py-8">No saved strategies found</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {strategies.map((strategy) => {
              const isOwner = strategy.user_id === currentUserId;
              return (
                <div
                  key={strategy.id}
                  className="flex items-center gap-2 p-3 rounded-lg bg-gray-700 hover:bg-gray-600 
                           transition-colors duration-200"
                >
                  <button
                    onClick={() => onStrategySelect(strategy.id, !isOwner)}
                    className="flex-1 text-left"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">{strategy.name}</span>
                      {!isOwner && (
                        <span className="text-xs px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded-full">
                          Read Only
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-400">
                      Last updated: {new Date(strategy.updated_at).toLocaleDateString()}
                    </div>
                  </button>
                  {isOwner && (
                    <button
                      onClick={(e) => handleDelete(strategy.id, e)}
                      disabled={deletingId === strategy.id}
                      className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700/50 rounded-lg
                               transition-colors duration-200 disabled:opacity-50"
                    >
                      {deletingId === strategy.id ? (
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 
                     transition-colors duration-200"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
} 
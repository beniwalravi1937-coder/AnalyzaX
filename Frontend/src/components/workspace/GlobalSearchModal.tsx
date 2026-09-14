'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from '@tanstack/react-router';
import {
  Search,
  Database,
  LayoutDashboard,
  FileText,
  Code2,
  LineChart,
  Sparkles,
  X,
  ArrowRight,
  Star,
  Brain,
  BarChart3,
  UploadCloud,
  Folder,
  Lightbulb,
  Calculator,
  Terminal,
} from 'lucide-react';
import { workspaceApi } from '../../services/workspaceApi';
import { SearchResult, AssetType } from '../../types/workspace';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  route: string;
  badge?: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'upload-dataset',
    label: 'Upload dataset',
    description: 'Ingest CSV, Parquet, or connect external database',
    icon: UploadCloud,
    route: '/data',
  },
  {
    id: 'ask-ai',
    label: 'Ask AI',
    description: 'Chat with AI Analyst on active dataset context',
    icon: Brain,
    route: '/ai-analyst',
  },
  {
    id: 'create-visualization',
    label: 'Create visualization',
    description: 'Build interactive charts, heatmaps, and plots',
    icon: BarChart3,
    route: '/visualizations',
  },
  {
    id: 'open-sql',
    label: 'Open SQL',
    description: 'Query data directly via high-speed DuckDB engine',
    icon: Terminal,
    route: '/sql',
  },
  {
    id: 'create-dashboard',
    label: 'Create dashboard',
    description: 'Compose executive metric cards and charts',
    icon: LayoutDashboard,
    route: '/',
  },
];

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await workspaceApi.searchAssets({
          q: query.trim(),
          asset_type: selectedType !== 'ALL' ? selectedType : undefined,
          page_size: 20,
        });
        setResults(res.results || []);
        setSelectedIndex(0);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 220);

    return () => clearTimeout(timer);
  }, [query, selectedType]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (query) {
          setSelectedIndex((prev) => (results.length > 0 ? (prev + 1) % results.length : 0));
        } else {
          setSelectedIndex((prev) => (prev + 1) % QUICK_ACTIONS.length);
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (query) {
          setSelectedIndex((prev) => (results.length > 0 ? (prev - 1 + results.length) % results.length : 0));
        } else {
          setSelectedIndex((prev) => (prev - 1 + QUICK_ACTIONS.length) % QUICK_ACTIONS.length);
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (query && results[selectedIndex]) {
          navigateToResult(results[selectedIndex]);
        } else if (!query && QUICK_ACTIONS[selectedIndex]) {
          executeQuickAction(QUICK_ACTIONS[selectedIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, query, results, selectedIndex]);

  const navigateToResult = (item: SearchResult) => {
    onClose();
    navigate({ to: item.navigation_url as any });
  };

  const executeQuickAction = (action: QuickAction) => {
    onClose();
    navigate({ to: action.route as any });
  };

  if (!isOpen) return null;

  const getTypeIcon = (type: AssetType | string) => {
    switch (type) {
      case 'PROJECT':
        return <Folder className="w-4 h-4 text-indigo-400" />;
      case 'DATASET':
      case 'DATASET_VERSION':
        return <Database className="w-4 h-4 text-emerald-400" />;
      case 'DASHBOARD':
        return <LayoutDashboard className="w-4 h-4 text-sky-400" />;
      case 'VISUALIZATION':
        return <BarChart3 className="w-4 h-4 text-violet-400" />;
      case 'QUERY':
        return <Code2 className="w-4 h-4 text-amber-400" />;
      case 'REPORT':
      case 'EXPORT':
        return <FileText className="w-4 h-4 text-rose-400" />;
      case 'INSIGHT':
      case 'STATISTICAL_ANALYSIS':
        return <Lightbulb className="w-4 h-4 text-yellow-400" />;
      case 'METRIC':
        return <Calculator className="w-4 h-4 text-teal-400" />;
      case 'AI_SESSION':
        return <Brain className="w-4 h-4 text-purple-400" />;
      case 'ML_EXPERIMENT':
      case 'ML_RESULT':
      case 'FORECAST_EXPERIMENT':
      case 'FORECAST_RESULT':
        return <LineChart className="w-4 h-4 text-fuchsia-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-slate-400" />;
    }
  };

  const filterTabs = [
    { label: 'All', value: 'ALL' },
    { label: 'Datasets', value: 'DATASET' },
    { label: 'Dashboards', value: 'DASHBOARD' },
    { label: 'Visualizations', value: 'VISUALIZATION' },
    { label: 'Queries', value: 'QUERY' },
    { label: 'Reports', value: 'REPORT' },
    { label: 'Insights', value: 'INSIGHT' },
    { label: 'Metrics', value: 'METRIC' },
    { label: 'AI', value: 'AI_SESSION' },
  ];

  return (
    <div
      className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-start justify-center z-50 pt-16 sm:pt-24 p-4 animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[82vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="relative flex items-center px-4 py-3.5 border-b border-slate-800 bg-slate-950/70">
          <Search className="w-5 h-5 text-slate-400 shrink-0 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search anything...  ⌘K"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="text-slate-400 hover:text-slate-200 p-1 rounded-md"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <div className="ml-2 pl-3 border-l border-slate-800 text-[10px] text-slate-400 flex items-center gap-1 font-mono shrink-0">
            <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">ESC</kbd>
          </div>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 px-4 py-2 bg-slate-950/40 border-b border-slate-800/60 overflow-x-auto text-xs no-scrollbar">
          {filterTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSelectedType(tab.value)}
              className={`px-2.5 py-1 rounded-full font-medium transition-colors shrink-0 text-[11px] ${
                selectedType === tab.value
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Results / Quick Actions View */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoading ? (
            <div className="p-10 text-center text-xs text-slate-400">
              Searching analytical registry...
            </div>
          ) : query && results.length === 0 ? (
            <div className="p-10 text-center space-y-2">
              <Search className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-sm font-semibold text-slate-300">No matching analytical assets</p>
              <p className="text-xs text-slate-500">Try searching with different keywords or check active filters.</p>
            </div>
          ) : !query ? (
            /* Quick Actions when no search query */
            <div className="py-2 px-1">
              <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Quick Actions
              </div>
              <div className="mt-1 space-y-1">
                {QUICK_ACTIONS.map((action, idx) => {
                  const isSelected = idx === selectedIndex;
                  const Icon = action.icon;
                  return (
                    <div
                      key={action.id}
                      onClick={() => executeQuickAction(action)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-indigo-500/15 border border-indigo-500/30 text-white'
                          : 'hover:bg-slate-800/50 border border-transparent text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-800/80 text-indigo-400 shrink-0">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-100">{action.label}</div>
                          <div className="text-xs text-slate-400 leading-tight">{action.description}</div>
                        </div>
                      </div>
                      <ArrowRight className={`w-4 h-4 text-slate-500 transition-transform ${isSelected ? 'translate-x-1 text-indigo-400' : ''}`} />
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            results.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.asset_id}
                  onClick={() => navigateToResult(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-indigo-500/15 border border-indigo-500/30 text-slate-100 shadow-sm'
                      : 'hover:bg-slate-800/40 border border-transparent text-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3 truncate">
                    <div className="p-2 rounded-lg bg-slate-800/80 shrink-0">
                      {getTypeIcon(item.asset_type)}
                    </div>
                    <div className="truncate">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold truncate">{item.name}</span>
                        {item.is_favorite && <Star className="w-3 h-3 text-amber-400 fill-amber-400 shrink-0" />}
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 uppercase font-mono font-medium tracking-wide">
                          {item.asset_type.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5 truncate">
                        {item.project_name && (
                          <span className="text-slate-400 truncate">Project: {item.project_name}</span>
                        )}
                        {item.description && (
                          <>
                            <span>•</span>
                            <span className="truncate">{item.description}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 text-slate-500 ml-4">
                    <ArrowRight className={`w-4 h-4 transition-transform ${isSelected ? 'translate-x-1 text-indigo-400' : ''}`} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-4 py-2.5 bg-slate-950/80 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span>Navigate: <kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-300">↑</kbd> <kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-300">↓</kbd></span>
            <span>Select: <kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-300">↵</kbd></span>
          </div>
          {query && results.length > 0 && <span>{results.length} result(s) found</span>}
          {!query && <span>Press ESC to close</span>}
        </div>
      </div>
    </div>
  );
};

export default GlobalSearchModal;

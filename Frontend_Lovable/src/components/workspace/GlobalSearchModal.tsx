'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Database, LayoutDashboard, FileText, Code2, LineChart, Sparkles, X, ArrowRight, Star } from 'lucide-react';
import { workspaceApi } from '../../services/workspaceApi';
import { SearchResult, AssetType } from '../../types/workspace';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose }) => {
  const router = useRouter();
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
    }, 250);

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
        setSelectedIndex((prev) => (results.length > 0 ? (prev + 1) % results.length : 0));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (results.length > 0 ? (prev - 1 + results.length) % results.length : 0));
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        e.preventDefault();
        navigateToResult(results[selectedIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex]);

  const navigateToResult = (item: SearchResult) => {
    onClose();
    router.push(item.navigation_url);
  };

  if (!isOpen) return null;

  const getTypeIcon = (type: AssetType) => {
    switch (type) {
      case 'DATASET':
      case 'DATASET_VERSION':
        return <Database className="w-4 h-4 text-emerald-400" />;
      case 'DASHBOARD':
        return <LayoutDashboard className="w-4 h-4 text-indigo-400" />;
      case 'REPORT':
      case 'EXPORT':
        return <FileText className="w-4 h-4 text-sky-400" />;
      case 'QUERY':
        return <Code2 className="w-4 h-4 text-amber-400" />;
      case 'ML_EXPERIMENT':
      case 'ML_RESULT':
      case 'FORECAST_EXPERIMENT':
      case 'FORECAST_RESULT':
        return <LineChart className="w-4 h-4 text-fuchsia-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-violet-400" />;
    }
  };

  const filterTabs = [
    { label: 'All', value: 'ALL' },
    { label: 'Datasets', value: 'DATASET' },
    { label: 'Dashboards', value: 'DASHBOARD' },
    { label: 'Reports', value: 'REPORT' },
    { label: 'Queries', value: 'QUERY' },
    { label: 'ML & Forecasts', value: 'ML_EXPERIMENT' },
  ];

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-start justify-center z-50 pt-20 p-4 animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        {/* Search Input Bar */}
        <div className="relative flex items-center px-4 py-3.5 border-b border-slate-800 bg-slate-950/60">
          <Search className="w-5 h-5 text-slate-400 shrink-0 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search datasets, dashboards, reports, SQL queries, ML models..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="text-slate-400 hover:text-slate-200 p-1 rounded-md"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <div className="ml-2 pl-3 border-l border-slate-800 text-[10px] text-slate-500 flex items-center gap-1 font-mono">
            <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">ESC</kbd> to close
          </div>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 px-4 py-2 bg-slate-950/30 border-b border-slate-800/60 overflow-x-auto text-xs">
          {filterTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSelectedType(tab.value)}
              className={`px-2.5 py-1 rounded-full font-medium transition-colors shrink-0 ${
                selectedType === tab.value
                  ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-400">
              Searching analytical registry...
            </div>
          ) : query && results.length === 0 ? (
            <div className="p-10 text-center space-y-2">
              <Search className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-sm font-semibold text-slate-300">No matching analytical assets</p>
              <p className="text-xs text-slate-500">Try searching with different keywords or check active filters.</p>
            </div>
          ) : !query ? (
            <div className="p-8 text-center text-xs text-slate-500">
              Type to instantly search across all projects, datasets, models, queries, and reports.
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
                      ? 'bg-sky-500/15 border border-sky-500/30 text-slate-100 shadow-sm'
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
                    <ArrowRight className={`w-4 h-4 transition-transform ${isSelected ? 'translate-x-1 text-sky-400' : ''}`} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span>Navigate: <kbd className="px-1 py-0.5 bg-slate-800 rounded">↑</kbd> <kbd className="px-1 py-0.5 bg-slate-800 rounded">↓</kbd></span>
            <span>Select: <kbd className="px-1 py-0.5 bg-slate-800 rounded">↵</kbd></span>
          </div>
          {results.length > 0 && <span>{results.length} result(s) found</span>}
        </div>
      </div>
    </div>
  );
};


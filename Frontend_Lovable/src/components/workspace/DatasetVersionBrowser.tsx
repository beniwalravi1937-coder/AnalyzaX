'use client';

import React, { useState, useEffect } from 'react';
import { X, GitCommit, GitCompare, ArrowRight, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { workspaceApi } from '../../services/workspaceApi';
import { DatasetVersionComparisonResult } from '../../types/workspace';

interface VersionItem {
  version_id: string;
  dataset_id: string;
  parent_version_id?: string | null;
  created_at: string;
  row_count: number;
  column_count: number;
  transformation_summary?: string | null;
}

interface DatasetVersionBrowserProps {
  datasetId: string;
  datasetName: string;
  isOpen: boolean;
  onClose: () => void;
}

export const DatasetVersionBrowser: React.FC<DatasetVersionBrowserProps> = ({
  datasetId,
  datasetName,
  isOpen,
  onClose,
}) => {
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedVersionA, setSelectedVersionA] = useState<string>('');
  const [selectedVersionB, setSelectedVersionB] = useState<string>('');
  const [comparison, setComparison] = useState<DatasetVersionComparisonResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load versions
  useEffect(() => {
    if (!isOpen || !datasetId) return;

    const fetchVersions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`http://localhost:8000/api/v1/datasets/${datasetId}/versions`);
        if (!res.ok) throw new Error('Failed to load version history');
        const data = await res.json();
        setVersions(data || []);
        if (data && data.length >= 2) {
          setSelectedVersionA(data[0].version_id);
          setSelectedVersionB(data[1].version_id);
        } else if (data && data.length === 1) {
          setSelectedVersionA(data[0].version_id);
          setSelectedVersionB(data[0].version_id);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchVersions();
  }, [isOpen, datasetId]);

  // Run metadata comparison
  const handleCompare = async () => {
    if (!selectedVersionA || !selectedVersionB) return;
    setIsComparing(true);
    setError(null);
    try {
      const res = await workspaceApi.compareDatasetVersionsMetadata(datasetId, selectedVersionA, selectedVersionB);
      setComparison(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsComparing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Dataset Version Browser</h3>
              <p className="text-xs text-slate-400">
                Inspect historical version snapshots and compare schema/row deltas for <strong>{datasetName}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/30 text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Versions Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Historical Versions ({versions.length})</h4>
            <div className="border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">Version ID</th>
                    <th className="px-4 py-2.5 font-semibold">Parent</th>
                    <th className="px-4 py-2.5 font-semibold">Rows</th>
                    <th className="px-4 py-2.5 font-semibold">Columns</th>
                    <th className="px-4 py-2.5 font-semibold">Created</th>
                    <th className="px-4 py-2.5 font-semibold">Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                        Loading version history...
                      </td>
                    </tr>
                  ) : versions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-6 text-center text-slate-500">
                        No historical versions recorded for this dataset.
                      </td>
                    </tr>
                  ) : (
                    versions.map((v) => (
                      <tr key={v.version_id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-4 py-2.5 font-mono font-bold text-emerald-400">{v.version_id}</td>
                        <td className="px-4 py-2.5 font-mono text-slate-500">{v.parent_version_id || '—'}</td>
                        <td className="px-4 py-2.5 font-medium">{v.row_count?.toLocaleString() ?? '—'}</td>
                        <td className="px-4 py-2.5 font-medium">{v.column_count ?? '—'}</td>
                        <td className="px-4 py-2.5 text-slate-400">
                          {v.created_at ? new Date(v.created_at).toLocaleString() : '—'}
                        </td>
                        <td className="px-4 py-2.5 text-slate-400 truncate max-w-[200px]">
                          {v.transformation_summary || 'Initial snapshot'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Comparison Controls */}
          {versions.length >= 2 && (
            <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GitCompare className="w-4 h-4 text-sky-400" />
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Metadata-Level Version Comparison
                  </h4>
                </div>
                <button
                  onClick={handleCompare}
                  disabled={isComparing || selectedVersionA === selectedVersionB}
                  className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow"
                >
                  {isComparing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
                  Compare Versions
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Baseline Version (A)</label>
                  <select
                    value={selectedVersionA}
                    onChange={(e) => setSelectedVersionA(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    {versions.map((v) => (
                      <option key={v.version_id} value={v.version_id}>
                        {v.version_id} ({v.row_count} rows, {v.column_count} cols)
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Target Version (B)</label>
                  <select
                    value={selectedVersionB}
                    onChange={(e) => setSelectedVersionB(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-sky-500"
                  >
                    {versions.map((v) => (
                      <option key={v.version_id} value={v.version_id}>
                        {v.version_id} ({v.row_count} rows, {v.column_count} cols)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Comparison Result Display */}
              {comparison && (
                <div className="pt-4 border-t border-slate-800/80 space-y-4 animate-in fade-in duration-200">
                  {/* Summary Delta Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <div className="text-[11px] text-slate-400">Row Count Delta</div>
                      <div className="text-base font-bold text-slate-100 flex items-center gap-1.5 mt-0.5">
                        <span>{comparison.row_count_delta >= 0 ? `+${comparison.row_count_delta}` : comparison.row_count_delta}</span>
                        <span className="text-[10px] text-slate-500 font-normal">
                          ({comparison.row_count_a} → {comparison.row_count_b})
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <div className="text-[11px] text-slate-400">Column Count Delta</div>
                      <div className="text-base font-bold text-slate-100 flex items-center gap-1.5 mt-0.5">
                        <span>{comparison.column_count_delta >= 0 ? `+${comparison.column_count_delta}` : comparison.column_count_delta}</span>
                        <span className="text-[10px] text-slate-500 font-normal">
                          ({comparison.column_count_a} → {comparison.column_count_b})
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <div className="text-[11px] text-slate-400">Stored Metadata Status</div>
                      <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1 mt-1">
                        <Check className="w-3.5 h-3.5" />
                        AVAILABLE STORED METADATA
                      </div>
                    </div>
                  </div>

                  {/* Schema Changes Details */}
                  <div className="space-y-2">
                    <div className="text-xs font-bold text-slate-300">Schema Modifications:</div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                      {/* Added */}
                      <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/30">
                        <div className="font-semibold text-emerald-400 mb-1">
                          Added Columns ({comparison.schema_diff.added_columns.length})
                        </div>
                        {comparison.schema_diff.added_columns.length === 0 ? (
                          <div className="text-[11px] text-slate-500 italic">None</div>
                        ) : (
                          comparison.schema_diff.added_columns.map((col, idx) => (
                            <div key={idx} className="text-[11px] text-emerald-200">
                              + {col.name} <span className="text-emerald-400/60 font-mono">({col.type})</span>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Removed */}
                      <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-800/30">
                        <div className="font-semibold text-rose-400 mb-1">
                          Removed Columns ({comparison.schema_diff.removed_columns.length})
                        </div>
                        {comparison.schema_diff.removed_columns.length === 0 ? (
                          <div className="text-[11px] text-slate-500 italic">None</div>
                        ) : (
                          comparison.schema_diff.removed_columns.map((col, idx) => (
                            <div key={idx} className="text-[11px] text-rose-200">
                              - {col.name} <span className="text-rose-400/60 font-mono">({col.type})</span>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Modified Types */}
                      <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-800/30">
                        <div className="font-semibold text-amber-400 mb-1">
                          Modified Types ({comparison.schema_diff.modified_types.length})
                        </div>
                        {comparison.schema_diff.modified_types.length === 0 ? (
                          <div className="text-[11px] text-slate-500 italic">None</div>
                        ) : (
                          comparison.schema_diff.modified_types.map((col, idx) => (
                            <div key={idx} className="text-[11px] text-amber-200">
                              ~ {col.name}: {col.type_a} → {col.type_b}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-950/80 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

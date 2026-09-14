'use client';

import React, { useState } from 'react';
import { ProjectHealth } from '../../types/workspace';
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2, ChevronDown, ChevronUp, Info, Database, Layers, Flame, Archive } from 'lucide-react';

interface ProjectHealthCardProps {
  health: ProjectHealth;
  onRefresh?: () => void;
}

export const ProjectHealthCard: React.FC<ProjectHealthCardProps> = ({ health, onRefresh }) => {
  const [showBrokenRefs, setShowBrokenRefs] = useState(false);

  const getStatusBadge = () => {
    switch (health.status) {
      case 'HEALTHY':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>PROJECT HEALTH: HEALTHY</span>
          </div>
        );
      case 'WARNING':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>PROJECT HEALTH: WARNING</span>
          </div>
        );
      case 'CRITICAL':
        return (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>PROJECT HEALTH: CRITICAL</span>
          </div>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-slate-700/70 bg-slate-900/60 p-5 backdrop-blur-sm shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-slate-800 text-sky-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Project Governance & Asset Health
            </h4>
            <p className="text-xs text-slate-400">
              Evaluates reference integrity, active dataset dependencies, and job outcomes.
            </p>
          </div>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Datasets Ready</span>
            <Database className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-slate-100">{health.datasets_ready}</div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Total Assets</span>
            <Layers className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-lg font-bold text-slate-100">{health.total_assets}</div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Archived Datasets</span>
            <Archive className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-slate-100">{health.archived_datasets}</div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Broken References</span>
            <Flame className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className={`text-lg font-bold ${health.broken_references.length > 0 ? 'text-rose-400' : 'text-slate-100'}`}>
            {health.broken_references.length}
          </div>
        </div>
      </div>

      {/* Broken References Expansion */}
      {health.broken_references.length > 0 && (
        <div className="pt-2 border-t border-slate-800">
          <button
            onClick={() => setShowBrokenRefs(!showBrokenRefs)}
            className="flex items-center justify-between w-full text-xs font-semibold text-rose-400 hover:text-rose-300 py-1"
          >
            <span>Detected Broken References ({health.broken_references.length})</span>
            {showBrokenRefs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showBrokenRefs && (
            <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
              {health.broken_references.map((b, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-800/30 text-xs text-rose-200"
                >
                  <div className="font-semibold">{b.source_asset_name || b.source_asset_id}</div>
                  <div className="text-[11px] text-rose-300/80 mt-0.5">{b.reason}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Governance Note */}
      <div className="flex items-center gap-2 p-2.5 rounded-xl bg-sky-950/20 border border-sky-900/30 text-[11px] text-sky-300/80">
        <Info className="w-3.5 h-3.5 shrink-0 text-sky-400" />
        <span>
          <strong>Note:</strong> Project Health measures architectural and relational integrity across projects and assets. It does not replace dataset-level profiling quality scores.
        </span>
      </div>
    </div>
  );
};

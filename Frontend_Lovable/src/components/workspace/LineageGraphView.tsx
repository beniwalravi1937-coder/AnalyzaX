'use client';

import React, { useState, useEffect } from 'react';
import { LineageGraph, LineageNode } from '../../types/workspace';
import { workspaceApi } from '../../services/workspaceApi';
import { GitBranch, Database, LayoutDashboard, FileText, Code2, LineChart, Sparkles, ArrowRight, ShieldAlert } from 'lucide-react';

interface LineageGraphViewProps {
  assetId: string;
}

export const LineageGraphView: React.FC<LineageGraphViewProps> = ({ assetId }) => {
  const [lineage, setLineage] = useState<LineageGraph | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLineage = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await workspaceApi.getAssetLineage(assetId);
        setLineage(res);
        if (res.nodes.length > 0) {
          const root = res.nodes.find((n) => n.id === res.root_asset_id) || res.nodes[0];
          setSelectedNode(root);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to construct lineage graph');
      } finally {
        setIsLoading(false);
      }
    };

    if (assetId) {
      fetchLineage();
    }
  }, [assetId]);

  const getNodeIcon = (type: string) => {
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
      case 'FORECAST_EXPERIMENT':
        return <LineChart className="w-4 h-4 text-fuchsia-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-violet-400" />;
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
        <GitBranch className="w-4 h-4 animate-spin text-sky-400" />
        Loading asset lineage and relationship graph...
      </div>
    );
  }

  if (error || !lineage) {
    return (
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 text-center">
        {error || 'No lineage relationships recorded for this asset.'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <GitBranch className="w-4 h-4 text-sky-400" />
          <span>Asset Lineage & Dependency DAG ({lineage.nodes.length} nodes, {lineage.edges.length} edges)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Nodes Grid */}
        <div className="lg:col-span-2 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Connected Assets</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {lineage.nodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isRoot = node.id === lineage.root_asset_id;

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-sky-500/15 border-sky-500/50 shadow-md ring-1 ring-sky-500/30'
                      : 'bg-slate-800/40 border-slate-700/40 hover:bg-slate-800/80'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="p-1.5 rounded-lg bg-slate-800 text-slate-300">
                      {getNodeIcon(node.type)}
                    </div>
                    {isRoot && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-400 font-semibold uppercase">
                        Current
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-bold text-slate-100 truncate">{node.label}</div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                    <span className="uppercase font-mono">{node.type.replace('_', ' ')}</span>
                    <span>•</span>
                    <span className={node.status === 'ARCHIVED' ? 'text-amber-400' : 'text-emerald-400'}>
                      {node.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Relationship Edges */}
          {lineage.edges.length > 0 && (
            <div className="pt-3 border-t border-slate-800/80 space-y-1.5">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Relationships</div>
              <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                {lineage.edges.map((edge, idx) => {
                  const srcNode = lineage.nodes.find((n) => n.id === edge.source);
                  const tgtNode = lineage.nodes.find((n) => n.id === edge.target);

                  return (
                    <div
                      key={idx}
                      className="flex items-center gap-2 text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-800/50 text-slate-300"
                    >
                      <span className="font-semibold text-slate-200 truncate">{srcNode?.label || edge.source}</span>
                      <ArrowRight className="w-3 h-3 text-sky-400 shrink-0" />
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-sky-300 shrink-0">
                        {edge.relationship_type}
                      </span>
                      <ArrowRight className="w-3 h-3 text-sky-400 shrink-0" />
                      <span className="font-semibold text-slate-200 truncate">{tgtNode?.label || edge.target}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Selected Node Details Drawer */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Node Details</div>
          {selectedNode ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40 space-y-1">
                <div className="text-slate-400 text-[11px]">Asset Name</div>
                <div className="font-bold text-slate-100">{selectedNode.label}</div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/40">
                  <div className="text-slate-400 text-[10px]">Asset Type</div>
                  <div className="font-mono text-slate-200 font-semibold">{selectedNode.type}</div>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/40">
                  <div className="text-slate-400 text-[10px]">Status</div>
                  <div className="font-semibold text-emerald-400">{selectedNode.status}</div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40 space-y-1 font-mono text-[11px] text-slate-400">
                <div>ID: {selectedNode.id}</div>
              </div>
            </div>
          ) : (
            <div className="text-slate-500 text-xs text-center py-6">Select a node to inspect details</div>
          )}
        </div>
      </div>
    </div>
  );
};

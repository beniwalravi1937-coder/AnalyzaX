'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useWorkspace } from '../../../../context/WorkspaceContext';
import { Project, ProjectHealth, ActivityRecord, Asset, AssetType } from '../../../../types/workspace';
import { workspaceApi } from '../../../../services/workspaceApi';
import { ProjectHealthCard } from '../../../../components/workspace/ProjectHealthCard';
import { LineageGraphView } from '../../../../components/workspace/LineageGraphView';
import { ActivityTimeline } from '../../../../components/activity/ActivityTimeline';
import {
  Folder,
  Database,
  LayoutDashboard,
  FileText,
  Code2,
  LineChart,
  Sparkles,
  Archive,
  RefreshCw,
  Copy,
  Download,
  Trash2,
  Star,
  GitBranch,
  ArrowRight,
  Search,
  CheckCircle2,
  AlertTriangle,
  X,
} from 'lucide-react';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;
  const { activeProject, setActiveProject, refreshProjects } = useWorkspace();

  const [project, setProject] = useState<Project | null>(null);
  const [health, setHealth] = useState<ProjectHealth | null>(null);
  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [totalAssets, setTotalAssets] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [activeTab, setActiveTab] = useState<'ALL' | 'DATASET' | 'DASHBOARD' | 'REPORT' | 'QUERY' | 'EXPORT'>('ALL');
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedLineageAsset, setSelectedLineageAsset] = useState<Asset | null>(null);

  // Safeguard Delete Modal State
  const [deleteWarningAsset, setDeleteWarningAsset] = useState<Asset | null>(null);
  const [deleteWarnings, setDeleteWarnings] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);

  // Manifest Export Modal State
  const [manifestData, setManifestData] = useState<any | null>(null);

  const loadProjectData = useCallback(async () => {
    if (!projectId) return;
    setIsLoading(true);
    try {
      const [projData, healthData, actData, assetData] = await Promise.all([
        workspaceApi.getProject(projectId),
        workspaceApi.getProjectHealth(projectId),
        workspaceApi.getProjectActivity(projectId, 25),
        workspaceApi.getAssets(projectId, {
          asset_type: activeTab !== 'ALL' ? activeTab : undefined,
          page_size: 100,
        }),
      ]);

      setProject(projData);
      setHealth(healthData);
      setActivities(actData || []);
      setAssets(assetData.assets || []);
      setTotalAssets(assetData.total || 0);

      if (activeProject?.project_id !== projData.project_id) {
        setActiveProject(projData);
      }
    } catch (err: any) {
      console.error('Failed to load project details:', err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, activeTab]);

  useEffect(() => {
    loadProjectData();
  }, [loadProjectData]);

  const handleFavoriteToggle = async (asset: Asset) => {
    try {
      if (asset.is_favorite) {
        await workspaceApi.unfavoriteAsset(asset.asset_id);
      } else {
        await workspaceApi.favoriteAsset(asset.asset_id);
      }
      // Update local state
      setAssets((prev) =>
        prev.map((a) => (a.asset_id === asset.asset_id ? { ...a, is_favorite: !a.is_favorite } : a))
      );
    } catch (err: any) {
      alert(`Failed to update favorite: ${err.message}`);
    }
  };

  const handleArchiveAsset = async (assetId: string) => {
    try {
      await workspaceApi.archiveAsset(assetId);
      loadProjectData();
    } catch (err: any) {
      alert(`Failed to archive asset: ${err.message}`);
    }
  };

  const handleRestoreAsset = async (assetId: string) => {
    try {
      await workspaceApi.restoreAsset(assetId);
      loadProjectData();
    } catch (err: any) {
      alert(`Failed to restore asset: ${err.message}`);
    }
  };

  const initiateDeleteAsset = async (asset: Asset) => {
    try {
      const summary = await workspaceApi.getAssetDependencies(asset.asset_id);
      if (!summary.can_safely_delete) {
        setDeleteWarningAsset(asset);
        setDeleteWarnings(summary.warnings);
      } else {
        if (confirm(`Are you sure you want to permanently delete '${asset.name}'?`)) {
          await executeDelete(asset.asset_id, false);
        }
      }
    } catch (err: any) {
      alert(`Failed to evaluate dependencies: ${err.message}`);
    }
  };

  const executeDelete = async (assetId: string, force: boolean) => {
    setIsDeleting(true);
    try {
      await workspaceApi.deleteAsset(assetId, force);
      setDeleteWarningAsset(null);
      setDeleteWarnings([]);
      loadProjectData();
    } catch (err: any) {
      alert(`Failed to delete asset: ${err.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleExportManifest = async () => {
    try {
      const manifest = await workspaceApi.exportProjectManifest(projectId);
      setManifestData(manifest);
    } catch (err: any) {
      alert(`Failed to export manifest: ${err.message}`);
    }
  };

  const handleDuplicateProject = async () => {
    if (!project) return;
    const newName = prompt('Enter name for duplicated project:', `${project.name} (Copy)`);
    if (!newName) return;
    try {
      const dup = await workspaceApi.duplicateProject(projectId, newName);
      await refreshProjects();
      router.push(`/projects/${dup.project_id}`);
    } catch (err: any) {
      alert(`Failed to duplicate project: ${err.message}`);
    }
  };

  const getAssetIcon = (type: AssetType) => {
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

  const filteredAssets = assets.filter((a) =>
    a.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    (a.description && a.description.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  const datasetCount = assets.filter((a) => a.asset_type === 'DATASET').length;
  const dashboardCount = assets.filter((a) => a.asset_type === 'DASHBOARD').length;
  const reportCount = assets.filter((a) => a.asset_type === 'REPORT').length;
  const queryCount = assets.filter((a) => a.asset_type === 'QUERY').length;

  if (isLoading && !project) {
    return (
      <div className="py-24 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
        Loading project environment...
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-8 text-center space-y-3">
        <h2 className="text-lg font-bold text-slate-200">Project Not Found</h2>
        <Link href="/projects" className="text-xs text-sky-400 hover:underline">
          Return to Projects List
        </Link>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-150">
      {/* Project Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center">
              <Folder className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black text-slate-100 tracking-tight">{project.name}</h1>
                <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                  project.status === 'ACTIVE'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {project.status}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {project.description || 'Project environment for analytical pipelines and assets.'}
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExportManifest}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Manifest</span>
          </button>

          <button
            onClick={handleDuplicateProject}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700 shadow-sm"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>Duplicate</span>
          </button>
        </div>
      </div>

      {/* Overview Stat Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Datasets</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{datasetCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Dashboards</span>
            <LayoutDashboard className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{dashboardCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Reports</span>
            <FileText className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{reportCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Saved Queries</span>
            <Code2 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-bold text-slate-100">{queryCount}</div>
        </div>
      </div>

      {/* Project Health Section */}
      {health && <ProjectHealthCard health={health} onRefresh={loadProjectData} />}

      {/* Asset Inventory & Recent Activity Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Asset Inventory Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-slate-100">Project Analytical Assets</h2>
            <div className="relative w-full sm:w-60">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter assets..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-800/80 border border-slate-700/60 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {(['ALL', 'DATASET', 'DASHBOARD', 'REPORT', 'QUERY', 'EXPORT'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-xl font-semibold transition-colors shrink-0 ${
                  activeTab === tab
                    ? 'bg-sky-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {tab === 'ALL' ? 'All Assets' : `${tab.charAt(0) + tab.slice(1).toLowerCase()}s`}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-900/60 backdrop-blur-sm shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 font-semibold">Asset</th>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Updated</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredAssets.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                      No matching assets found in this project.
                    </td>
                  </tr>
                ) : (
                  filteredAssets.map((asset) => (
                    <tr key={asset.asset_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <button
                            onClick={() => handleFavoriteToggle(asset)}
                            title={asset.is_favorite ? 'Unfavorite' : 'Favorite'}
                            className="text-slate-600 hover:text-amber-400 transition-colors"
                          >
                            <Star
                              className={`w-3.5 h-3.5 ${
                                asset.is_favorite ? 'text-amber-400 fill-amber-400' : ''
                              }`}
                            />
                          </button>
                          <div>
                            <div className="font-bold text-slate-100">{asset.name}</div>
                            {asset.description && (
                              <div className="text-[11px] text-slate-400 truncate max-w-xs">{asset.description}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {getAssetIcon(asset.asset_type)}
                          <span className="font-mono text-[11px] uppercase tracking-wide">
                            {asset.asset_type.replace('_', ' ')}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                          asset.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                        }`}>
                          {asset.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px]">
                        {new Date(asset.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setSelectedLineageAsset(asset)}
                            title="View Lineage & Dependencies"
                            className="p-1 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                          >
                            <GitBranch className="w-3.5 h-3.5" />
                          </button>

                          {asset.status === 'ACTIVE' ? (
                            <button
                              onClick={() => handleArchiveAsset(asset.asset_id)}
                              title="Archive Asset"
                              className="p-1 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors"
                            >
                              <Archive className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleRestoreAsset(asset.asset_id)}
                              title="Restore Asset"
                              className="p-1 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                            >
                              <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                          )}

                          <button
                            onClick={() => initiateDeleteAsset(asset)}
                            title="Delete Asset"
                            className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="space-y-4">
          <ActivityTimeline
            projectId={projectId}
            title="Recent Project Activity"
            subtitle="Collaborative milestones, data uploads, and analytical events"
          />
        </div>
      </div>

      {/* Lineage Modal */}
      {selectedLineageAsset && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl p-6 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-sky-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Lineage: {selectedLineageAsset.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedLineageAsset(null)}
                className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-4 overflow-y-auto">
              <LineageGraphView assetId={selectedLineageAsset.asset_id} />
            </div>
          </div>
        </div>
      )}

      {/* Deletion Safeguard Modal */}
      {deleteWarningAsset && (
        <div className="fixed inset-0 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-rose-800/60 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Dependency Safeguard Warning</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Cannot safely delete <strong>{deleteWarningAsset.name}</strong> without affecting dependent assets.
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-900/40 text-xs text-rose-200 space-y-2">
              <div className="font-semibold text-rose-300">Dependent Asset Warnings:</div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-200/90">
                {deleteWarnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>

            <p className="text-[11px] text-slate-400">
              <strong>Recommendation:</strong> Use <em>Archive</em> instead to preserve historical dashboards and reports while deactivating the asset.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setDeleteWarningAsset(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleArchiveAsset(deleteWarningAsset.asset_id)}
                className="px-4 py-2 text-xs font-semibold text-amber-300 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 rounded-lg transition-colors"
              >
                Archive Instead
              </button>
              <button
                onClick={() => executeDelete(deleteWarningAsset.asset_id, true)}
                disabled={isDeleting}
                className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-50 rounded-lg shadow transition-colors"
              >
                {isDeleting ? 'Deleting...' : 'Force Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manifest Modal */}
      {manifestData && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl p-6 shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100">Project Configuration Manifest</h3>
              <button
                onClick={() => setManifestData(null)}
                className="p-1 text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="py-4 flex-1 overflow-y-auto font-mono text-[11px] bg-slate-950/60 p-4 rounded-xl text-slate-300">
              <pre>{JSON.stringify(manifestData, null, 2)}</pre>
            </div>
            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(manifestData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `project-${projectId}-manifest.json`;
                  a.click();
                }}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow"
              >
                Download Manifest JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useWorkspace } from '../../context/WorkspaceContext';
import { Project } from '../../types/workspace';
import { Folder, ChevronDown, Plus, Check, Archive, RefreshCw } from 'lucide-react';

export const ProjectSwitcher: React.FC = () => {
  const { projects, activeProject, setActiveProject, createProject, isLoading } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setIsSubmitting(true);
    try {
      await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      setIsOpen(false);
    } catch (err: any) {
      alert(`Failed to create project: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(filterQuery.toLowerCase()))
  );

  const activeProjects = filteredProjects.filter((p) => p.status === 'ACTIVE');
  const archivedProjects = filteredProjects.filter((p) => p.status === 'ARCHIVED');

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Switcher Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg border border-slate-700/80 bg-slate-900/90 hover:bg-slate-800/90 text-slate-200 text-sm font-medium transition-all shadow-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
      >
        <div className="w-5 h-5 rounded bg-sky-500/20 text-sky-400 flex items-center justify-center">
          <Folder className="w-3.5 h-3.5" />
        </div>
        <span className="max-w-[140px] truncate font-semibold">
          {isLoading ? 'Loading...' : activeProject ? activeProject.name : 'Select Project'}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 rounded-xl bg-slate-900 border border-slate-700/80 shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          <div className="p-2.5 border-b border-slate-800 bg-slate-950/50">
            <input
              type="text"
              placeholder="Find project..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-slate-800/80 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-sky-500"
              autoFocus
            />
          </div>

          <div className="max-h-60 overflow-y-auto p-1.5 space-y-0.5">
            <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Active Projects ({activeProjects.length})
            </div>
            {activeProjects.map((p) => {
              const isSelected = activeProject?.project_id === p.project_id;
              return (
                <button
                  key={p.project_id}
                  onClick={() => {
                    setActiveProject(p);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors ${
                    isSelected
                      ? 'bg-sky-500/15 text-sky-400 font-semibold'
                      : 'text-slate-300 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Folder className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{p.name}</span>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-sky-400 shrink-0" />}
                </button>
              );
            })}

            {archivedProjects.length > 0 && (
              <>
                <div className="pt-2 px-2 py-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <Archive className="w-3 h-3" /> Archived ({archivedProjects.length})
                </div>
                {archivedProjects.map((p) => (
                  <button
                    key={p.project_id}
                    onClick={() => {
                      setActiveProject(p);
                      setIsOpen(false);
                    }}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-slate-500 hover:bg-slate-800/40 transition-colors"
                  >
                    <span className="truncate">{p.name}</span>
                    <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">Archived</span>
                  </button>
                ))}
              </>
            )}
          </div>

          <div className="p-2 border-t border-slate-800 bg-slate-950/50">
            <button
              onClick={() => {
                setShowCreateModal(true);
                setIsOpen(false);
              }}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-medium text-sky-400 hover:bg-sky-500/10 border border-dashed border-sky-500/30 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create New Project</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95 duration-150">
            <h3 className="text-lg font-bold text-slate-100 mb-1">Create New Project</h3>
            <p className="text-xs text-slate-400 mb-5">
              Organize your analytical assets, datasets, dashboards, and ML experiments.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Project Name *</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Q3 Growth & Retention Analysis"
                  className="w-full px-3.5 py-2 text-sm bg-slate-800/80 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Goals, hypothesis, and target metrics..."
                  className="w-full px-3.5 py-2 text-sm bg-slate-800/80 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !newProjectName.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 disabled:opacity-50 rounded-lg shadow transition-colors flex items-center gap-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Creating...
                    </>
                  ) : (
                    'Create Project'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

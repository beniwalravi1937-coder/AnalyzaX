import { createFileRoute } from "@tanstack/react-router";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "../context/WorkspaceContext";
import { Project } from "../types/workspace";
import { workspaceApi } from "../services/workspaceApi";
import {
  Folder,
  Plus,
  Archive,
  RefreshCw,
  Copy,
  ArrowRight,
  Search,
  CheckCircle2,
  Clock,
  Database,
  Layers,
  ShieldCheck,
  Cpu,
  Sparkles,
  ChevronDown,
  Zap,
} from "lucide-react";

export const Route = createFileRoute("/projects/")({
  head: () => ({
    meta: [
      { title: "Projects & Folders — AnalyzaX" },
      {
        name: "description",
        content:
          "Organize your team's analytics projects, datasets, and saved reports in clean, shareable workspaces tailored for your company.",
      },
      { property: "og:title", content: "Projects & Folders — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Organize your team's analytics projects, datasets, and saved reports in clean, shareable workspaces.",
      },
    ],
  }),
  component: ProjectsPage,
});

function ProjectsPage() {
  const router = useRouter();
  const { projects, activeProject, setActiveProject, refreshProjects, createProject, isLoading } = useWorkspace();
  const [filterTab, setFilterTab] = useState<"ACTIVE" | "ARCHIVED">("ACTIVE");
  const [envFilter, setEnvFilter] = useState<"ALL" | "PRODUCTION" | "STAGING">("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"RECENT" | "NAME" | "CREATED">("RECENT");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "n") {
        e.preventDefault();
        setShowCreateModal(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setIsCreating(true);
    try {
      const created = await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      setShowCreateModal(false);
      setNewProjectName("");
      setNewProjectDesc("");
      router.push(`/projects/${created.project_id}`);
    } catch (err: any) {
      alert(`Failed to create project: ${err.message}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDuplicate = async (projectId: string, currentName: string) => {
    const newName = prompt("Enter name for duplicate project:", `${currentName} (Copy)`);
    if (!newName) return;
    try {
      await workspaceApi.duplicateProject(projectId, newName);
      await refreshProjects();
    } catch (err: any) {
      alert(`Failed to duplicate project: ${err.message}`);
    }
  };

  const handleArchive = async (projectId: string) => {
    if (!confirm("Are you sure you want to archive this project? All existing assets and historical references will remain safely preserved.")) return;
    try {
      await workspaceApi.archiveProject(projectId);
      await refreshProjects();
    } catch (err: any) {
      alert(`Failed to archive project: ${err.message}`);
    }
  };

  const handleRestore = async (projectId: string) => {
    try {
      await workspaceApi.restoreProject(projectId);
      await refreshProjects();
    } catch (err: any) {
      alert(`Failed to restore project: ${err.message}`);
    }
  };

  const filteredProjects = projects
    .filter((p) => {
      const matchesTab = p.status === filterTab;
      const matchesSearch =
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesTab && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === "NAME") return a.name.localeCompare(b.name);
      if (sortBy === "CREATED") return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      return new Date(b.last_activity_at || b.updated_at).getTime() - new Date(a.last_activity_at || a.updated_at).getTime();
    });

  const activeCount = projects.filter((p) => p.status === "ACTIVE").length;
  const archivedCount = projects.filter((p) => p.status === "ARCHIVED").length;

  return (
    <div className="min-h-screen p-6 lg:p-10 max-w-[1400px] mx-auto space-y-8 animate-in fade-in duration-200 relative">
      <div
        className="pointer-events-none absolute top-4 left-1/4 w-[500px] h-[220px] rounded-full blur-[90px] -z-10"
        style={{ background: "radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, rgba(11, 15, 23, 0) 70%)" }}
      />

      <section className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-white/[0.08]">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span
              className="text-[11px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded border"
              style={{
                background: "rgba(99, 102, 241, 0.1)",
                borderColor: "rgba(99, 102, 241, 0.25)",
                color: "#a5b4fc",
              }}
            >
              Workspace Hub
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-[11px] font-mono text-slate-400">DuckDB Engine Online</span>
          </div>

          <h1
            className="text-3xl lg:text-4xl font-bold tracking-tight"
            style={{
              background: "linear-gradient(135deg, #ffffff 30%, #c0c1ff 70%, #818cf8 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Projects & Workspaces
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            Manage your analytical lakehouses, vectorized pipelines, and autonomous AI dataset connections.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refreshProjects()}
            title="Refresh projects list"
            className="flex items-center gap-2 px-3.5 py-2.5 rounded-lg border border-white/[0.08] bg-slate-900/60 hover:bg-slate-800/80 hover:border-white/[0.16] text-slate-300 text-xs font-medium transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-indigo-400" : ""}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/35 hover:scale-[1.01] active:scale-[0.99] transition-all cursor-pointer"
            style={{ background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #7c3aed 100%)" }}
          >
            <Plus className="w-4 h-4 font-bold" />
            <span>New Project</span>
            <kbd className="ml-1 text-[10px] font-mono bg-black/25 text-white/90 px-1.5 py-0.5 rounded border border-white/20">
              ⌘N
            </kbd>
          </button>
        </div>
      </section>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/40 border border-white/[0.06] backdrop-blur-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-slate-400">Active Workspaces</div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{activeCount}</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-white/[0.06] backdrop-blur-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-slate-400">Engine Throughput</div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
              14.2M <span className="text-xs font-normal text-slate-500">rows/s</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Zap className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-white/[0.06] backdrop-blur-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-slate-400">DuckDB Core</div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              v1.5.5 <span className="text-xs font-normal text-emerald-400/80">Vector SIMD</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Cpu className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/40 border border-white/[0.06] backdrop-blur-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-slate-400">Schema Drift</div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
              0 <span className="text-xs font-normal text-emerald-400 font-mono">Normal</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
      </section>

      <section className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 p-2 rounded-2xl bg-slate-900/50 border border-white/[0.06] backdrop-blur-md">
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex p-1 rounded-xl bg-slate-950/70 border border-white/[0.06]">
            <button
              onClick={() => setFilterTab("ACTIVE")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 flex items-center gap-2 ${
                filterTab === "ACTIVE"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/50"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Active Projects</span>
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
                  filterTab === "ACTIVE" ? "bg-indigo-700 text-white" : "bg-slate-800 text-slate-400"
                }`}
              >
                {activeCount}
              </span>
            </button>

            <button
              onClick={() => setFilterTab("ARCHIVED")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 flex items-center gap-2 ${
                filterTab === "ARCHIVED"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/50"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Archived</span>
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
                  filterTab === "ARCHIVED" ? "bg-indigo-700 text-white" : "bg-slate-800 text-slate-400"
                }`}
              >
                {archivedCount}
              </span>
            </button>
          </div>

          <div className="hidden sm:block h-6 w-[1px] bg-white/[0.08]" />

          <div className="flex items-center gap-1.5">
            {(["ALL", "PRODUCTION", "STAGING"] as const).map((env) => (
              <button
                key={env}
                onClick={() => setEnvFilter(env)}
                className={`px-3 py-1 rounded-full text-[11px] font-mono transition-colors ${
                  envFilter === env
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                    : "bg-slate-900/40 text-slate-400 hover:text-slate-200 border border-white/[0.04]"
                }`}
              >
                {env === "ALL" ? "All Envs" : env.charAt(0) + env.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-12 py-1.5 bg-slate-950/60 border border-white/[0.08] rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/40 transition-colors"
            />
            <kbd className="absolute right-2.5 top-2 font-mono text-[10px] text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded border border-white/[0.08]">
              ⌘K
            </kbd>
          </div>

          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="appearance-none pl-3 pr-8 py-1.5 bg-slate-950/60 border border-white/[0.08] rounded-xl text-xs text-slate-300 hover:border-white/[0.16] focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
            >
              <option value="RECENT">Recently updated</option>
              <option value="NAME">Alphabetical</option>
              <option value="CREATED">Date created</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        </div>
      </section>

      {isLoading ? (
        <div className="py-24 text-center text-slate-400 text-sm flex items-center justify-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Synchronizing analytical workspaces...</span>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-20 text-center rounded-2xl border border-dashed border-white/[0.08] bg-slate-900/20 space-y-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
            <Folder className="w-6 h-6" />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-base font-semibold text-slate-200">
              {searchQuery ? "No matching projects found" : filterTab === "ARCHIVED" ? "No archived workspaces" : "No workspaces yet"}
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {searchQuery
                ? "Try adjusting your search terms or environment filter."
                : filterTab === "ARCHIVED"
                ? "Archived workspaces and their versioned datasets remain preserved here."
                : "Create your first analytical workspace to start querying, cleaning, and modeling data."}
            </p>
          </div>
          {filterTab === "ACTIVE" && !searchQuery && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-900/30 transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Workspace</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-6">
          {filteredProjects.map((proj) => {
            const isActive = activeProject?.project_id === proj.project_id;
            const updatedDate = new Date(proj.last_activity_at || proj.updated_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <article
                key={proj.project_id}
                className="group relative flex flex-col justify-between rounded-xl transition-all duration-200 overflow-hidden cursor-default"
                style={{
                  background: "#121620",
                  border: isActive ? "1px solid rgba(99, 102, 241, 0.6)" : "1px solid rgba(255, 255, 255, 0.08)",
                  boxShadow: isActive
                    ? "0 0 24px -4px rgba(99, 102, 241, 0.2), 0 8px 16px -6px rgba(0, 0, 0, 0.5)"
                    : "0 4px 16px rgba(0, 0, 0, 0.3)",
                }}
              >
                <div
                  className={`absolute top-0 inset-x-0 h-[2px] transition-opacity duration-200 ${
                    isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                  }`}
                  style={{ background: "linear-gradient(90deg, transparent, #818cf8, transparent)" }}
                />

                <div className="p-6">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div
                        className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors"
                        style={{
                          background: "rgba(99, 102, 241, 0.12)",
                          border: "1px solid rgba(99, 102, 241, 0.25)",
                          color: "#818cf8",
                        }}
                      >
                        <Database className="w-5 h-5" />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setActiveProject(proj);
                              router.push(`/projects/${proj.project_id}`);
                            }}
                            className="text-left font-semibold text-base text-slate-100 hover:text-indigo-300 transition-colors truncate max-w-[220px]"
                          >
                            {proj.name}
                          </button>
                          <span
                            className="text-[10px] font-mono px-2 py-0.5 rounded border flex-shrink-0"
                            style={{
                              background: "rgba(6, 182, 212, 0.1)",
                              borderColor: "rgba(6, 182, 212, 0.25)",
                              color: "#22d3ee",
                            }}
                          >
                            Production
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-500 block truncate mt-0.5">
                          ID: {proj.project_id.slice(0, 16)}...
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {isActive && (
                        <span
                          className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider flex items-center gap-1"
                          style={{ background: "rgba(99, 102, 241, 0.2)", color: "#c7d2fe" }}
                        >
                          <CheckCircle2 className="w-3 h-3 text-indigo-400" />
                          <span>Current</span>
                        </span>
                      )}
                      <div
                        className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-mono text-[11px]"
                        style={
                          proj.status === "ACTIVE"
                            ? {
                                background: "rgba(16, 185, 129, 0.1)",
                                border: "1px solid rgba(16, 185, 129, 0.25)",
                                color: "#34d399",
                              }
                            : {
                                background: "rgba(245, 158, 11, 0.1)",
                                border: "1px solid rgba(245, 158, 11, 0.25)",
                                color: "#fbbf24",
                              }
                        }
                      >
                        <span className="relative flex h-2 w-2">
                          {proj.status === "ACTIVE" && (
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                          )}
                          <span
                            className={`relative inline-flex rounded-full h-2 w-2 ${
                              proj.status === "ACTIVE" ? "bg-emerald-400" : "bg-amber-400"
                            }`}
                          />
                        </span>
                        <span>{proj.status === "ACTIVE" ? "Active" : "Archived"}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-4">
                    {proj.description || "Primary analytical workspace for orchestrating data pipelines and telemetry."}
                  </p>

                  <div className="flex flex-wrap items-center gap-y-1.5 gap-x-3 py-2 px-3 rounded-lg bg-slate-950/60 border border-white/[0.06] mb-4 font-mono text-[11px] text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-slate-200 font-semibold">Active</span> Datasets
                    </div>
                    <span className="text-slate-600">•</span>
                    <div className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-slate-200 font-semibold">DuckDB</span> Pipelines
                    </div>
                  </div>

                  <div className="flex items-center justify-between font-mono text-[11px] text-slate-500 pt-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800/80 text-indigo-300 border border-white/[0.06]">
                        DuckDB Engine
                      </span>
                      <span className="text-emerald-400 flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        Online
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{updatedDate}</span>
                    </div>
                  </div>
                </div>

                <div className="px-6 py-3 bg-slate-950/40 border-t border-white/[0.06] flex items-center justify-between">
                  <button
                    onClick={() => {
                      setActiveProject(proj);
                      router.push(`/projects/${proj.project_id}`);
                    }}
                    className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white transition-all cursor-pointer"
                    style={{
                      background: "linear-gradient(135deg, #6366f1, #4f46e5)",
                      boxShadow: "0 2px 8px rgba(99, 102, 241, 0.25)",
                    }}
                  >
                    <span>Open Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDuplicate(proj.project_id, proj.name)}
                      title="Duplicate Workspace"
                      className="p-1.5 rounded-md text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>

                    {proj.status === "ACTIVE" ? (
                      <button
                        onClick={() => handleArchive(proj.project_id)}
                        title="Archive Workspace"
                        className="p-1.5 rounded-md text-slate-400 hover:text-amber-300 hover:bg-white/[0.06] transition-colors"
                      >
                        <Archive className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRestore(proj.project_id)}
                        title="Restore Workspace"
                        className="p-1.5 rounded-md text-slate-400 hover:text-emerald-300 hover:bg-white/[0.06] transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}

          <div
            onClick={() => setShowCreateModal(true)}
            className="flex flex-col items-center justify-center p-8 rounded-xl border-2 border-dashed border-white/[0.08] hover:border-indigo-500/50 bg-slate-900/10 hover:bg-indigo-500/[0.03] transition-all cursor-pointer min-h-[260px] group text-center space-y-3"
          >
            <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 group-hover:scale-110 group-hover:bg-indigo-500/20 transition-all">
              <Plus className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-200 group-hover:text-indigo-300 text-sm transition-colors">
                Create New Workspace
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Spin up a vectorized DuckDB lakehouse workspace with zero cold-start latency.
              </p>
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-150">
          <div
            className="rounded-2xl w-full max-w-md p-6 shadow-2xl animate-in zoom-in-95 duration-150 relative"
            style={{
              background: "#121620",
              border: "1px solid rgba(255, 255, 255, 0.1)",
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Plus className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-slate-100">Create New Analytical Workspace</h3>
            </div>
            <p className="text-xs text-slate-400 mb-5 ml-9">
              Isolate datasets, feature engineering pipelines, and ML models.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                  Workspace Name *
                </label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Sales Pipeline Analysis"
                  className="w-full px-3.5 py-2 text-sm bg-slate-950/70 border border-white/[0.08] rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Goals, target metrics, data sources..."
                  className="w-full px-3.5 py-2 text-sm bg-slate-950/70 border border-white/[0.08] rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-white/[0.06]">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !newProjectName.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  style={{ background: "linear-gradient(135deg, #6366f1, #4f46e5)" }}
                >
                  {isCreating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Create Workspace"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

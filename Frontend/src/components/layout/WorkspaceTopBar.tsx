import React from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { Menu, Search, User, LogOut, Settings, BookOpen, Sliders, Shield } from "lucide-react";
import { ProjectSelector } from "@/components/ui/ProjectSelector";
import { DatasetSelector } from "@/components/ui/DatasetSelector";
import { NotificationCenter } from "@/components/collaboration/NotificationCenter";
import { useBackendHealth } from "@/hooks/useBackendHealth";
import { useAuth } from "@/context/AuthContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { useDataset } from "@/context/DatasetContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface WorkspaceTopBarProps {
  onToggleMobileSidebar: () => void;
  onOpenSearch: () => void;
  className?: string;
}

export const WorkspaceTopBar: React.FC<WorkspaceTopBarProps> = ({
  onToggleMobileSidebar,
  onOpenSearch,
  className,
}) => {
  const navigate = useNavigate();
  const { user, logout, currentRole } = useAuth();
  const { projects, activeProject, setActiveProject } = useWorkspace();
  const { datasets, activeDataset, selectDataset } = useDataset();
  const { connection, health } = useBackendHealth();

  const userInitials = React.useMemo(() => {
    if (!user) return "U";
    const name = user.display_name || user.email || "";
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase() || "U";
  }, [user]);

  const handleSignOut = async () => {
    await logout();
    navigate({ to: "/login" });
  };

  return (
    <header
      className={cn(
        "h-14 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 flex items-center justify-between gap-3 shrink-0 sticky top-0 z-20 select-none",
        className
      )}
    >
      {/* LEFT SECTION: Sidebar Toggle + Project Selector + Dataset Context */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          onClick={onToggleMobileSidebar}
          className="md:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/60 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Project Selector */}
        <ProjectSelector
          projects={projects.map((p) => ({
            id: p.project_id,
            name: p.name,
            datasetCount: p.metadata?.dataset_count,
            updatedAt: p.updated_at,
            isShared: Boolean(p.metadata?.is_shared),
          }))}
          activeProjectId={activeProject?.project_id}
          onSelectProject={(id) => {
            const match = projects.find((p) => p.project_id === id);
            if (match) setActiveProject(match);
          }}
          onCreateProject={() => navigate({ to: "/projects" })}
          size="sm"
        />

        {/* Compact Dataset Context */}
        <DatasetSelector
          datasets={datasets.map((d) => ({
            id: d.id,
            name: d.name,
            rowCount: d.row_count,
            columnCount: d.column_count,
            format: d.format,
          }))}
          activeDatasetId={activeDataset?.id}
          onSelectDataset={selectDataset}
          onUploadNew={() => navigate({ to: "/data" })}
          size="sm"
        />
      </div>

      {/* CENTER SECTION: Polished Global Search Trigger */}
      <div className="hidden sm:flex flex-1 max-w-sm justify-center mx-2">
        <button
          type="button"
          onClick={onOpenSearch}
          className="flex items-center justify-between w-full px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-700 text-slate-400 hover:text-slate-200 text-xs transition-colors shadow-xs"
          title="Search anything (⌘K or Ctrl+K)"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate">Search anything...</span>
          </div>
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono shrink-0 ml-2">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* RIGHT SECTION: Status + Notifications + User Avatar */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Real System Status */}
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors"
          title={
            connection === "connected"
              ? `DuckDB Engine ${health?.status || "Ready"} · All analytical pipelines nominal`
              : connection === "connecting"
              ? "Connecting to AnalyzaX Engine..."
              : "Backend unavailable"
          }
        >
          {connection === "connected" ? (
            <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-medium">Connected</span>
            </div>
          ) : connection === "connecting" ? (
            <div className="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span>Connecting</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
              <span>Offline</span>
            </div>
          )}
        </div>

        {/* Notifications */}
        <NotificationCenter />

        {/* Compact User Menu */}
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="focus:outline-none rounded-full ring-offset-slate-950 focus:ring-2 focus:ring-indigo-500 transition-shadow"
                aria-label="Open user menu"
              >
                <Avatar className="w-7 h-7 border border-slate-700 bg-indigo-600/20 text-indigo-300 text-xs font-semibold hover:border-indigo-400 transition-colors">
                  <AvatarFallback className="bg-indigo-600/20 text-indigo-300">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              align="end"
              className="w-56 bg-slate-950 border-slate-800 text-white p-1.5 shadow-2xl z-50 text-xs"
            >
              <div className="px-2.5 py-2">
                <div className="font-semibold text-slate-100 truncate text-xs">
                  {user.display_name || user.email}
                </div>
                <div className="text-[11px] text-slate-400 truncate mt-0.5 flex items-center gap-1">
                  <Shield className="w-3 h-3 text-indigo-400 shrink-0" />
                  <span className="capitalize">{currentRole || "Workspace Owner"}</span>
                </div>
              </div>

              <DropdownMenuSeparator className="bg-slate-800 my-1" />

              <DropdownMenuItem
                onClick={() => navigate({ to: "/settings" })}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer hover:bg-slate-800/60 transition-colors"
              >
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Profile</span>
              </DropdownMenuItem>

              <DropdownMenuItem
                onClick={() => navigate({ to: "/settings" })}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer hover:bg-slate-800/60 transition-colors"
              >
                <Sliders className="w-3.5 h-3.5 text-slate-400" />
                <span>Preferences</span>
              </DropdownMenuItem>

              <DropdownMenuItem
                onClick={() => navigate({ to: "/settings" })}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer hover:bg-slate-800/60 transition-colors"
              >
                <Settings className="w-3.5 h-3.5 text-slate-400" />
                <span>Workspace settings</span>
              </DropdownMenuItem>

              <DropdownMenuItem
                asChild
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer hover:bg-slate-800/60 transition-colors"
              >
                <a
                  href="https://github.com/beniwalravi1937-coder/AnalyzaX#readme"
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                  <span>Documentation</span>
                </a>
              </DropdownMenuItem>

              <DropdownMenuSeparator className="bg-slate-800 my-1" />

              <DropdownMenuItem
                onClick={handleSignOut}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Link
            to="/login"
            className="px-3 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
};

export default WorkspaceTopBar;

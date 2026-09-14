import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Folder, ChevronDown, Check, Plus, Clock, Users } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { Button } from "./button";

export interface ProjectItem {
  id: string;
  name: string;
  datasetCount?: number;
  updatedAt?: string;
  isShared?: boolean;
}

export interface ProjectSelectorProps {
  projects: ProjectItem[];
  activeProjectId?: string | null;
  onSelectProject: (id: string) => void;
  onCreateProject?: () => void;
  className?: string;
  size?: "sm" | "md";
}

export function ProjectSelector({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  className,
  size = "md",
}: ProjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const activeProject = projects.find((p) => p.id === activeProjectId);

  // Partition projects into Recent, My, and Shared
  // Recent: sorted by updatedAt descending or first 3
  const recentProjects = [...projects]
    .sort((a, b) => {
      if (a.updatedAt && b.updatedAt) {
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      }
      return 0;
    })
    .slice(0, 3);

  // My Projects: all personal / workspace projects
  const myProjects = projects.filter((p) => !p.isShared);

  // Shared Projects: flagged as shared
  const sharedProjects = projects.filter((p) => p.isShared);

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size={size === "sm" ? "sm" : "default"}
          className={cn(
            "h-8 sm:h-9 px-2.5 sm:px-3 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-800/80 hover:border-white/20 text-slate-200 justify-between gap-2 max-w-[210px] truncate shadow-sm transition-colors",
            className
          )}
        >
          <div className="flex items-center gap-2 truncate">
            <Folder className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="truncate font-medium">
              {activeProject ? activeProject.name : "Default Project"}
            </span>
          </div>

          <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 opacity-70" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        className="w-72 bg-slate-950 border-white/10 text-white p-1.5 shadow-2xl z-50 max-h-[85vh] overflow-y-auto"
      >
        {/* Recent Projects Section */}
        {recentProjects.length > 0 && (
          <>
            <DropdownMenuLabel className="text-[11px] font-semibold text-slate-400 px-2 py-1 flex items-center gap-1.5 uppercase tracking-wider">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>Recent Projects</span>
            </DropdownMenuLabel>
            <div className="space-y-0.5 mb-1">
              {recentProjects.map((proj) => {
                const isSelected = proj.id === activeProjectId;
                return (
                  <DropdownMenuItem
                    key={`recent-${proj.id}`}
                    onClick={() => {
                      onSelectProject(proj.id);
                      setIsOpen(false);
                    }}
                    className={cn(
                      "flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors focus:bg-white/10 focus:text-white",
                      isSelected ? "bg-indigo-600/20 text-indigo-300 font-medium" : "text-slate-300"
                    )}
                  >
                    <div className="truncate font-medium text-white">{proj.name}</div>
                    {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0 ml-2" />}
                  </DropdownMenuItem>
                );
              })}
            </div>
            <DropdownMenuSeparator className="bg-white/5 my-1" />
          </>
        )}

        {/* My Projects Section */}
        <DropdownMenuLabel className="text-[11px] font-semibold text-slate-400 px-2 py-1 flex items-center gap-1.5 uppercase tracking-wider">
          <Folder className="w-3 h-3 text-slate-400" />
          <span>My Projects</span>
        </DropdownMenuLabel>
        <div className="max-h-48 overflow-y-auto space-y-0.5 mb-1">
          {myProjects.length === 0 ? (
            <div className="px-3 py-2 text-xs text-slate-500">No projects yet</div>
          ) : (
            myProjects.map((proj) => {
              const isSelected = proj.id === activeProjectId;
              return (
                <DropdownMenuItem
                  key={`my-${proj.id}`}
                  onClick={() => {
                    onSelectProject(proj.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "flex items-center justify-between px-2.5 py-2 rounded-md text-xs cursor-pointer transition-colors focus:bg-white/10 focus:text-white",
                    isSelected ? "bg-indigo-600/20 text-indigo-300 font-medium" : "text-slate-300"
                  )}
                >
                  <div className="space-y-0.5 min-w-0 pr-2">
                    <div className="font-medium truncate text-white">{proj.name}</div>
                    {proj.datasetCount !== undefined && (
                      <div className="text-[10px] text-slate-400 font-mono">
                        {proj.datasetCount} {proj.datasetCount === 1 ? "dataset" : "datasets"}
                      </div>
                    )}
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
                </DropdownMenuItem>
              );
            })
          )}
        </div>

        <DropdownMenuSeparator className="bg-white/5 my-1" />

        {/* Shared Projects Section */}
        <DropdownMenuLabel className="text-[11px] font-semibold text-slate-400 px-2 py-1 flex items-center gap-1.5 uppercase tracking-wider">
          <Users className="w-3 h-3 text-slate-400" />
          <span>Shared Projects</span>
        </DropdownMenuLabel>
        <div className="space-y-0.5 mb-1">
          {sharedProjects.length === 0 ? (
            <div className="px-3 py-1.5 text-[11px] text-slate-500 italic">
              No shared projects
            </div>
          ) : (
            sharedProjects.map((proj) => {
              const isSelected = proj.id === activeProjectId;
              return (
                <DropdownMenuItem
                  key={`shared-${proj.id}`}
                  onClick={() => {
                    onSelectProject(proj.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-colors focus:bg-white/10 focus:text-white",
                    isSelected ? "bg-indigo-600/20 text-indigo-300 font-medium" : "text-slate-300"
                  )}
                >
                  <div className="font-medium truncate text-white">{proj.name}</div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0 ml-2" />}
                </DropdownMenuItem>
              );
            })
          )}
        </div>

        {/* Create Project Section */}
        {onCreateProject && (
          <>
            <DropdownMenuSeparator className="bg-white/5 my-1" />
            <DropdownMenuItem
              onClick={() => {
                onCreateProject();
                setIsOpen(false);
              }}
              className="flex items-center gap-2 px-2.5 py-2 text-xs font-medium text-indigo-400 hover:text-indigo-300 hover:bg-indigo-600/10 cursor-pointer rounded-md transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Project</span>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default ProjectSelector;

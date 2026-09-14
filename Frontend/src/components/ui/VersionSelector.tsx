import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { GitBranch, ChevronDown, Check, Clock, ShieldCheck } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { Button } from "./button";
import { Badge } from "./badge";

export interface VersionItem {
  id: string;
  version_number?: number;
  name?: string;
  created_at?: string;
  row_count?: number;
  column_count?: number;
  is_current?: boolean;
  change_description?: string;
}

export interface VersionSelectorProps {
  versions: VersionItem[];
  activeVersionId?: string;
  onSelectVersion: (versionId: string) => void;
  className?: string;
  size?: "sm" | "md";
  disabled?: boolean;
}

export function VersionSelector({
  versions,
  activeVersionId,
  onSelectVersion,
  className,
  size = "md",
  disabled = false,
}: VersionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeVersion =
    versions.find((v) => v.id === activeVersionId || `v${v.version_number}` === activeVersionId) ||
    versions[0];

  const versionLabel = activeVersion
    ? activeVersion.name || `V${activeVersion.version_number ?? 1}`
    : "V1 (Original)";

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size={size === "sm" ? "sm" : "default"}
          disabled={disabled || versions.length === 0}
          className={cn(
            "h-9 px-2.5 sm:px-3 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-slate-200 justify-between gap-2 shrink-0 transition-colors shadow-sm",
            className
          )}
        >
          <div className="flex items-center gap-1.5 truncate text-left">
            <GitBranch className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="font-mono text-xs font-semibold text-slate-100">{versionLabel}</span>
            {activeVersion?.is_current && (
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" title="Latest Version" />
            )}
          </div>
          <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 opacity-70" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        className="w-64 bg-slate-950 border-white/10 text-white p-1.5 shadow-2xl z-50 max-h-[85vh] overflow-y-auto"
      >
        <DropdownMenuLabel className="text-[11px] font-semibold text-slate-400 px-2 py-1 flex items-center justify-between uppercase tracking-wider">
          <span>Immutable Lineage Versions</span>
          <Badge variant="outline" className="text-[10px] text-indigo-400 border-indigo-500/20 font-normal">
            {versions.length} version{versions.length !== 1 ? "s" : ""}
          </Badge>
        </DropdownMenuLabel>

        <DropdownMenuSeparator className="bg-white/5 my-1" />

        <div className="max-h-60 overflow-y-auto space-y-0.5 py-0.5">
          {versions.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-slate-400">
              No previous versions recorded.
            </div>
          ) : (
            versions.map((ver) => {
              const isSelected =
                ver.id === activeVersionId || `v${ver.version_number}` === activeVersionId;
              const displayName = ver.name || `Version ${ver.version_number ?? 1}`;

              return (
                <DropdownMenuItem
                  key={ver.id}
                  onClick={() => onSelectVersion(ver.id)}
                  className={cn(
                    "flex flex-col items-start gap-1 p-2 rounded-md cursor-pointer transition-colors text-xs",
                    isSelected
                      ? "bg-indigo-600/20 border border-indigo-500/30 text-white"
                      : "hover:bg-white/5 text-slate-300"
                  )}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-1.5 font-medium">
                      <GitBranch className={cn("w-3.5 h-3.5", isSelected ? "text-indigo-400" : "text-slate-500")} />
                      <span className="font-mono font-bold text-slate-100">{displayName}</span>
                      {ver.is_current && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Current
                        </span>
                      )}
                    </div>
                    {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                  </div>

                  {ver.change_description && (
                    <div className="text-[11px] text-slate-400 line-clamp-1 pl-5">
                      {ver.change_description}
                    </div>
                  )}

                  <div className="flex items-center gap-3 pl-5 text-[10px] text-slate-400">
                    {ver.row_count !== undefined && (
                      <span>{ver.row_count.toLocaleString()} rows</span>
                    )}
                    {ver.created_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {new Date(ver.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </DropdownMenuItem>
              );
            })
          )}
        </div>

        <DropdownMenuSeparator className="bg-white/5 my-1" />
        <div className="px-2 py-1 flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
          <ShieldCheck className="w-3 h-3 text-emerald-400 shrink-0" />
          <span>Read-only DAG lineage snapshot</span>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

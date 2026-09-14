import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Database, ChevronDown, Check, UploadCloud } from "lucide-react";
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

export interface DatasetItem {
  id: string;
  name: string;
  rowCount?: number;
  columnCount?: number;
  versionName?: string;
  updatedAt?: string;
  format?: string;
}

export interface DatasetSelectorProps {
  datasets: DatasetItem[];
  activeDatasetId?: string | null;
  onSelectDataset: (id: string) => void;
  onUploadNew?: () => void;
  className?: string;
  size?: "sm" | "md";
}

function formatRowCount(count?: number): string {
  if (count === undefined || count === null) return "0 rows";
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1).replace(/\.0$/, "")}M rows`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1).replace(/\.0$/, "")}K rows`;
  return `${count.toLocaleString()} rows`;
}

export function DatasetSelector({
  datasets,
  activeDatasetId,
  onSelectDataset,
  onUploadNew,
  className,
  size = "md",
}: DatasetSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const activeDataset = datasets.find((d) => d.id === activeDatasetId);

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size={size === "sm" ? "sm" : "default"}
          className={cn(
            "h-9 px-2.5 sm:px-3 text-xs border-white/10 bg-slate-900/60 hover:bg-slate-850 hover:border-white/20 text-slate-200 justify-between gap-2 max-w-[240px] truncate shadow-sm transition-colors",
            activeDataset && "h-10 py-1",
            className
          )}
        >
          {activeDataset ? (
            <div className="flex items-center gap-2 truncate text-left">
              <Database className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <div className="flex flex-col truncate leading-tight">
                <span className="truncate font-medium text-slate-100">{activeDataset.name}</span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {activeDataset.versionName || "V1"} · {formatRowCount(activeDataset.rowCount)}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 truncate">
              <Database className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="truncate font-medium text-slate-300">Select Dataset</span>
            </div>
          )}

          <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 opacity-70" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        className="w-72 bg-slate-950 border-white/10 text-white p-1.5 shadow-2xl z-50 max-h-[85vh] overflow-y-auto"
      >
        <DropdownMenuLabel className="text-[11px] font-semibold text-slate-400 px-2 py-1 flex items-center justify-between uppercase tracking-wider">
          <span>Active Datasets</span>
          <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/20 font-normal">
            {datasets.length} available
          </Badge>
        </DropdownMenuLabel>

        <DropdownMenuSeparator className="bg-white/5 my-1" />

        <div className="max-h-60 overflow-y-auto space-y-0.5 py-0.5">
          {datasets.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-slate-400">
              No datasets connected yet
            </div>
          ) : (
            datasets.map((ds) => {
              const isSelected = ds.id === activeDatasetId;
              return (
                <DropdownMenuItem
                  key={ds.id}
                  onClick={() => {
                    onSelectDataset(ds.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "flex items-center justify-between px-2.5 py-2 rounded-md text-xs cursor-pointer transition-colors focus:bg-white/10 focus:text-white",
                    isSelected ? "bg-indigo-600/20 text-indigo-300 font-medium" : "text-slate-300"
                  )}
                >
                  <div className="space-y-0.5 min-w-0 pr-2">
                    <div className="font-medium truncate text-white">{ds.name}</div>
                    <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                      <span>{ds.versionName || "V1"}</span>
                      <span>·</span>
                      <span>{formatRowCount(ds.rowCount)}</span>
                      {ds.format && (
                        <span className="uppercase text-[9px] px-1 rounded bg-white/5 text-slate-400 ml-1">
                          {ds.format}
                        </span>
                      )}
                    </div>
                  </div>

                  {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0 ml-2" />}
                </DropdownMenuItem>
              );
            })
          )}
        </div>

        {onUploadNew && (
          <>
            <DropdownMenuSeparator className="bg-white/5 my-1" />
            <DropdownMenuItem
              onClick={() => {
                onUploadNew();
                setIsOpen(false);
              }}
              className="flex items-center gap-2 px-2.5 py-2 text-xs font-medium text-indigo-400 hover:text-indigo-300 hover:bg-indigo-600/10 cursor-pointer rounded-md transition-colors"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Connect / Upload Dataset</span>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default DatasetSelector;

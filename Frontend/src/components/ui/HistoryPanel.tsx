import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Clock, Play, RotateCcw, Search, Trash2, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";
import { Badge } from "./badge";
import { EmptyState } from "./EmptyState";

export interface HistoryEntry {
  id: string;
  title: string;
  timestamp: string | Date;
  status: "success" | "error" | "running";
  durationMs?: number;
  parameters?: Record<string, any>;
  summary?: string;
  queryOrCommand?: string;
}

export interface HistoryPanelProps {
  entries: HistoryEntry[];
  onSelectEntry?: (entry: HistoryEntry) => void;
  onRerunEntry?: (entry: HistoryEntry) => void;
  onClearHistory?: () => void;
  selectedId?: string;
  className?: string;
  title?: string;
  emptyMessage?: string;
}

export function HistoryPanel({
  entries,
  onSelectEntry,
  onRerunEntry,
  onClearHistory,
  selectedId,
  className,
  title = "Analysis Run History",
  emptyMessage = "No analysis runs recorded in this session.",
}: HistoryPanelProps) {
  const [filterQuery, setFilterQuery] = useState("");

  const filteredEntries = entries.filter((e) => {
    if (!filterQuery.trim()) return true;
    const q = filterQuery.toLowerCase();
    return (
      e.title.toLowerCase().includes(q) ||
      (e.summary && e.summary.toLowerCase().includes(q)) ||
      (e.queryOrCommand && e.queryOrCommand.toLowerCase().includes(q))
    );
  });

  const formatDate = (d: string | Date) => {
    const date = typeof d === "string" ? new Date(d) : d;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  return (
    <div className={cn("flex flex-col h-full bg-slate-900/40 rounded-xl border border-white/10 overflow-hidden", className)}>
      <div className="p-3.5 border-b border-white/[0.08] flex items-center justify-between gap-2 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-white">{title}</span>
          <Badge variant="outline" className="text-[10px] text-slate-400 border-white/10">
            {entries.length}
          </Badge>
        </div>

        {onClearHistory && entries.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearHistory}
            className="h-7 px-2 text-[11px] text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 gap-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </Button>
        )}
      </div>

      {entries.length > 3 && (
        <div className="p-2 border-b border-white/[0.06] bg-slate-950/40">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <Input
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Search previous runs..."
              className="h-8 pl-8 text-xs bg-slate-900/80 border-white/10 text-white placeholder:text-slate-400"
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5 max-h-[480px]">
        {filteredEntries.length === 0 ? (
          <div className="py-8">
            <EmptyState
              icon={<Clock className="w-8 h-8 text-slate-500" />}
              title="No history yet"
              description={emptyMessage}
            />
          </div>
        ) : (
          filteredEntries.map((entry) => {
            const isSelected = entry.id === selectedId;
            return (
              <div
                key={entry.id}
                onClick={() => onSelectEntry?.(entry)}
                className={cn(
                  "group p-3 rounded-lg border text-xs cursor-pointer transition-all duration-150 flex flex-col gap-1.5",
                  isSelected
                    ? "bg-indigo-600/15 border-indigo-500/40 text-white shadow-sm"
                    : "bg-slate-900/60 border-white/5 hover:border-white/15 hover:bg-slate-850 text-slate-300"
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {entry.status === "success" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    ) : entry.status === "error" ? (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    ) : (
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 animate-pulse" />
                    )}
                    <span className="font-medium text-slate-100 truncate">{entry.title}</span>
                  </div>

                  <span className="text-[10px] text-slate-400 font-mono shrink-0">
                    {formatDate(entry.timestamp)}
                  </span>
                </div>

                {entry.summary && (
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {entry.summary}
                  </p>
                )}

                {entry.queryOrCommand && (
                  <div className="p-1.5 rounded bg-slate-950/80 font-mono text-[10px] text-slate-300 truncate border border-white/5">
                    {entry.queryOrCommand}
                  </div>
                )}

                <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                  <div className="flex items-center gap-2">
                    {entry.durationMs !== undefined && (
                      <span className="font-mono">{Math.round(entry.durationMs)}ms</span>
                    )}
                  </div>

                  {onRerunEntry && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRerunEntry(entry);
                      }}
                      className="h-6 px-2 text-[10px] text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 gap-1 opacity-80 group-hover:opacity-100"
                    >
                      <RotateCcw className="w-2.5 h-2.5" />
                      <span>Restore</span>
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

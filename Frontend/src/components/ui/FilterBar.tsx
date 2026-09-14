import React from "react";
import { cn } from "@/lib/utils";
import { X, Filter, RotateCcw } from "lucide-react";
import { Button } from "./button";

export interface FilterItem {
  id: string;
  field: string;
  operator?: string;
  value: string | number;
}

export interface FilterChipProps {
  field: string;
  operator?: string;
  value: string | number;
  onRemove?: () => void;
  className?: string;
}

export function FilterChip({
  field,
  operator = "equals",
  value,
  onRemove,
  className,
}: FilterChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs bg-slate-900 border border-white/10 text-slate-200 shadow-sm transition-all hover:border-white/20 select-none",
        className
      )}
    >
      <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">
        {field}
      </span>
      {operator !== "equals" && (
        <span className="text-[11px] text-slate-500">{operator}</span>
      )}
      <span className="font-mono text-indigo-300 font-medium">{String(value)}</span>

      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 p-0.5 text-slate-400 hover:text-rose-400 rounded transition-colors"
          aria-label={`Remove filter for ${field}`}
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </span>
  );
}

export interface FilterBarProps extends React.HTMLAttributes<HTMLDivElement> {
  filters: FilterItem[];
  onRemoveFilter: (id: string) => void;
  onClearAll?: () => void;
  actions?: React.ReactNode;
}

export function FilterBar({
  filters,
  onRemoveFilter,
  onClearAll,
  actions,
  className,
  ...props
}: FilterBarProps) {
  if (filters.length === 0 && !actions) return null;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-950/50 border border-white/10 backdrop-blur-sm flex-wrap",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-2 flex-wrap min-w-0">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium pl-1 shrink-0">
          <Filter className="w-3.5 h-3.5 text-indigo-400" />
          <span>Filters ({filters.length})</span>
        </div>

        <div className="h-4 w-px bg-white/10 mx-1 hidden sm:block shrink-0" />

        {filters.map((f) => (
          <FilterChip
            key={f.id}
            field={f.field}
            operator={f.operator}
            value={f.value}
            onRemove={() => onRemoveFilter(f.id)}
          />
        ))}

        {filters.length > 0 && onClearAll && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="h-7 text-xs text-slate-400 hover:text-slate-200 gap-1 px-2"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </Button>
        )}
      </div>

      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

export default FilterBar;

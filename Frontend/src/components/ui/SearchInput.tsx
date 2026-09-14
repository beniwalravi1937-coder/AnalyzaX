import React from "react";
import { cn } from "@/lib/utils";
import { Search, X } from "lucide-react";

export interface SearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  onClear?: () => void;
  showShortcut?: boolean;
  shortcutLabel?: string;
  size?: "sm" | "md" | "lg";
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  (
    {
      className,
      value,
      onChange,
      onClear,
      placeholder = "Search...",
      showShortcut = false,
      shortcutLabel = "Ctrl+K",
      size = "md",
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: "h-8 text-xs pl-8 pr-7",
      md: "h-9 text-xs sm:text-sm pl-9 pr-8",
      lg: "h-11 text-sm sm:text-base pl-10 pr-9",
    };

    const iconSizes = {
      sm: "w-3.5 h-3.5 left-2.5",
      md: "w-4 h-4 left-3",
      lg: "w-5 h-5 left-3.5",
    };

    const hasValue = value !== undefined && value !== null && String(value).length > 0;

    return (
      <div className="relative flex items-center w-full">
        <Search
          className={cn(
            "absolute text-slate-400 pointer-events-none transition-colors",
            iconSizes[size]
          )}
        />

        <input
          ref={ref}
          type="text"
          value={value}
          onChange={onChange}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            "w-full rounded-lg border border-white/10 bg-slate-900/60 text-white placeholder:text-slate-500 transition-all duration-150 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50",
            sizeClasses[size],
            className
          )}
          {...props}
        />

        <div className="absolute right-2.5 flex items-center gap-1.5">
          {hasValue && onClear && !disabled && (
            <button
              type="button"
              onClick={onClear}
              className="p-1 text-slate-400 hover:text-white rounded-md transition-colors"
              aria-label="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}

          {showShortcut && !hasValue && (
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-[10px] font-mono text-slate-400 select-none">
              {shortcutLabel}
            </kbd>
          )}
        </div>
      </div>
    );
  }
);

SearchInput.displayName = "SearchInput";

export default SearchInput;

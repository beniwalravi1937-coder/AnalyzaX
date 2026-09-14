import React from "react";
import { cn } from "@/lib/utils";

export interface SegmentedControlOption<T extends string | number> {
  value: T;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface SegmentedControlProps<T extends string | number> {
  value: T;
  onChange: (value: T) => void;
  options: SegmentedControlOption<T>[];
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function SegmentedControl<T extends string | number>({
  value,
  onChange,
  options,
  size = "md",
  className,
}: SegmentedControlProps<T>) {
  const sizeClasses = {
    sm: "p-0.5 text-xs",
    md: "p-1 text-xs sm:text-sm",
    lg: "p-1.5 text-sm sm:text-base",
  };

  const itemSizeClasses = {
    sm: "px-2.5 py-1 text-xs gap-1.5",
    md: "px-3 py-1.5 text-xs sm:text-sm gap-2",
    lg: "px-4 py-2 text-sm gap-2",
  };

  return (
    <div
      role="radiogroup"
      className={cn(
        "inline-flex items-center rounded-lg border border-white/10 bg-slate-950/70 backdrop-blur-sm select-none",
        sizeClasses[size],
        className
      )}
    >
      {options.map((option) => {
        const isSelected = option.value === value;
        return (
          <button
            key={String(option.value)}
            type="button"
            role="radio"
            aria-checked={isSelected}
            disabled={option.disabled}
            onClick={() => !option.disabled && onChange(option.value)}
            className={cn(
              "inline-flex items-center justify-center font-medium rounded-md transition-all duration-150 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40",
              itemSizeClasses[size],
              isSelected
                ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30 font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            )}
          >
            {option.icon && (
              <span className={cn("shrink-0", isSelected ? "text-white" : "text-slate-400")}>
                {option.icon}
              </span>
            )}
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default SegmentedControl;

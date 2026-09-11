"use client";

import React from "react";
import { StructuredFilter } from "@/types";
import { PlusIcon, TrashIcon, FilterIcon } from "@/components/icons";

interface VisualizationFiltersProps {
  filters: StructuredFilter[];
  onChange: (filters: StructuredFilter[]) => void;
  availableColumns: { name: string; type?: string }[];
}

const OPERATOR_LABELS: Record<string, string> = {
  eq: "equals (=)",
  neq: "not equals (≠)",
  gt: "greater than (>)",
  gte: "greater or equal (≥)",
  lt: "less than (<)",
  lte: "less or equal (≤)",
  in: "in list",
  not_in: "not in list",
  is_null: "is null",
  is_not_null: "is not null",
  like: "contains (LIKE)",
};

export function VisualizationFilters({
  filters,
  onChange,
  availableColumns,
}: VisualizationFiltersProps) {
  const handleAddFilter = () => {
    if (availableColumns.length === 0) return;
    const newFilter: StructuredFilter = {
      column: availableColumns[0].name,
      operator: "eq",
      value: "",
    };
    onChange([...filters, newFilter]);
  };

  const handleUpdateFilter = (index: number, updated: Partial<StructuredFilter>) => {
    const next = [...filters];
    next[index] = { ...next[index], ...updated };
    onChange(next);
  };

  const handleRemoveFilter = (index: number) => {
    onChange(filters.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div
      style={{
        backgroundColor: "rgba(15, 23, 42, 0.3)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "0.75rem",
        marginBottom: "1rem",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", fontWeight: 600 }}>
          <FilterIcon size={14} />
          <span>Active Filters ({filters.length})</span>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {filters.length > 0 && (
            <button
              onClick={handleClearAll}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
            >
              Clear All
            </button>
          )}
          <button
            onClick={handleAddFilter}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.2rem 0.6rem", display: "flex", alignItems: "center", gap: "0.3rem" }}
          >
            <PlusIcon size={12} />
            Add Filter
          </button>
        </div>
      </div>

      {filters.length === 0 ? (
        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
          No filters applied. Results reflect the entire dataset version.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {filters.map((filter, index) => {
            const isNullOp = filter.operator === "is_null" || filter.operator === "is_not_null";
            return (
              <div
                key={index}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.5fr 1.5fr 2fr auto",
                  gap: "0.5rem",
                  alignItems: "center",
                }}
              >
                {/* Column */}
                <select
                  value={filter.column}
                  onChange={(e) => handleUpdateFilter(index, { column: e.target.value })}
                  className="input input-sm"
                  style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
                >
                  {availableColumns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name} {col.type ? `(${col.type})` : ""}
                    </option>
                  ))}
                </select>

                {/* Operator */}
                <select
                  value={filter.operator}
                  onChange={(e) =>
                    handleUpdateFilter(index, {
                      operator: e.target.value as StructuredFilter["operator"],
                    })
                  }
                  className="input input-sm"
                  style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
                >
                  {Object.entries(OPERATOR_LABELS).map(([op, label]) => (
                    <option key={op} value={op}>
                      {label}
                    </option>
                  ))}
                </select>

                {/* Value */}
                {isNullOp ? (
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--text-secondary)",
                      padding: "0.25rem 0.5rem",
                      fontStyle: "italic",
                    }}
                  >
                    (no value needed)
                  </div>
                ) : (
                  <input
                    type="text"
                    value={
                      Array.isArray(filter.value)
                        ? filter.value.join(", ")
                        : (filter.value as string) || ""
                    }
                    onChange={(e) => {
                      const val = e.target.value;
                      if (filter.operator === "in" || filter.operator === "not_in") {
                        handleUpdateFilter(index, {
                          value: val.split(",").map((s) => s.trim()),
                        });
                      } else {
                        handleUpdateFilter(index, { value: val });
                      }
                    }}
                    placeholder={
                      filter.operator === "in" || filter.operator === "not_in"
                        ? "val1, val2, val3"
                        : "Filter value..."
                    }
                    className="input input-sm"
                    style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
                  />
                )}

                {/* Remove button */}
                <button
                  onClick={() => handleRemoveFilter(index)}
                  className="btn btn-ghost btn-sm"
                  style={{ padding: "0.25rem", color: "var(--status-danger, #ef4444)" }}
                  title="Remove filter"
                >
                  <TrashIcon size={14} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

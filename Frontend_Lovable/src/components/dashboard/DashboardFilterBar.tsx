"use client";

import React, { useState } from "react";
import { DashboardFilter, FilterOperator } from "@/types/dashboard";

interface DashboardFilterBarProps {
  filters: DashboardFilter[];
  onAddFilter: (filter: DashboardFilter) => void;
  onRemoveFilter: (filterId: string) => void;
  onClearFilters: () => void;
}

export function DashboardFilterBar({
  filters,
  onAddFilter,
  onRemoveFilter,
  onClearFilters,
}: DashboardFilterBarProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [fieldName, setFieldName] = useState("");
  const [operator, setOperator] = useState<FilterOperator>("equals");
  const [filterValue, setFilterValue] = useState("");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fieldName.trim() || !filterValue.trim()) return;

    onAddFilter({
      filter_id: `flt_${Math.random().toString(36).slice(2, 9)}`,
      field: fieldName.trim(),
      operator,
      value: filterValue.trim(),
      data_type: "categorical",
      scope: "GLOBAL",
    });

    setFieldName("");
    setFilterValue("");
    setIsAdding(false);
  };

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        border: "1px solid rgba(51, 65, 85, 0.6)",
        borderRadius: "8px",
        padding: "0.6rem 1rem",
        marginBottom: "1.25rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "0.75rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "#94a3b8" }}>
          Filters ({filters.length}):
        </span>

        {filters.map((f) => (
          <span
            key={f.filter_id}
            style={{
              background: "rgba(99, 102, 241, 0.2)",
              border: "1px solid rgba(99, 102, 241, 0.4)",
              color: "#c7d2fe",
              fontSize: "0.75rem",
              padding: "0.2rem 0.6rem",
              borderRadius: "16px",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <strong>{f.field}</strong> {f.operator} <em>"{String(f.value)}"</em>
            <button
              onClick={() => onRemoveFilter(f.filter_id)}
              style={{
                background: "transparent",
                border: "none",
                color: "#a5b4fc",
                cursor: "pointer",
                padding: "0 0.2rem",
                fontSize: "0.8rem",
              }}
              aria-label="Remove filter"
            >
              ✕
            </button>
          </span>
        ))}

        {filters.length === 0 && !isAdding && (
          <span style={{ fontSize: "0.8rem", color: "#64748b", fontStyle: "italic" }}>
            No active filters. Analytical components show full population.
          </span>
        )}

        {/* Add filter inline form */}
        {isAdding && (
          <form onSubmit={handleCreate} style={{ display: "inline-flex", gap: "0.35rem", alignItems: "center" }}>
            <input
              type="text"
              placeholder="Field name"
              value={fieldName}
              onChange={(e) => setFieldName(e.target.value)}
              className="input"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem", width: "110px" }}
              autoFocus
            />
            <select
              value={operator}
              onChange={(e) => setOperator(e.target.value as FilterOperator)}
              className="input"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
            >
              <option value="equals">=</option>
              <option value="not_equals">!=</option>
              <option value="greater_than">&gt;</option>
              <option value="less_than">&lt;</option>
              <option value="contains">contains</option>
            </select>
            <input
              type="text"
              placeholder="Value"
              value={filterValue}
              onChange={(e) => setFilterValue(e.target.value)}
              className="input"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem", width: "100px" }}
            />
            <button type="submit" className="btn btn-primary btn-sm" style={{ padding: "0.2rem 0.6rem", fontSize: "0.75rem" }}>
              Apply
            </button>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="btn btn-secondary btn-sm"
              style={{ padding: "0.2rem 0.6rem", fontSize: "0.75rem" }}
            >
              Cancel
            </button>
          </form>
        )}
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
          >
            + Add Filter
          </button>
        )}

        {filters.length > 0 && (
          <button
            onClick={onClearFilters}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", color: "#f87171" }}
          >
            Clear All
          </button>
        )}
      </div>
    </div>
  );
}

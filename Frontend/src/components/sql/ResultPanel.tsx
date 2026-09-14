"use client";

import React, { useState, useMemo } from "react";
import { SQLQueryResponse } from "@/types";
import {
  DownloadIcon,
  SearchIcon,
  CopyIcon,
  CheckIcon,
  AlertTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "@/components/icons";

interface ResultPanelProps {
  result: SQLQueryResponse | null;
  loading?: boolean;
}

export function ResultPanel({ result, loading = false }: ResultPanelProps) {
  const [filterText, setFilterText] = useState("");
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const columns = result?.columns || [];
  const rows = result?.rows || [];

  // In-table search filter
  const filteredRows = useMemo(() => {
    if (!filterText.trim()) return rows;
    const lower = filterText.toLowerCase();
    return rows.filter((r) =>
      Object.values(r).some((val) =>
        String(val ?? "").toLowerCase().includes(lower)
      )
    );
  }, [rows, filterText]);

  // In-table column sorting
  const sortedRows = useMemo(() => {
    if (!sortCol) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const valA = a[sortCol];
      const valB = b[sortCol];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;
      if (typeof valA === "number" && typeof valB === "number") {
        return sortAsc ? valA - valB : valB - valA;
      }
      return sortAsc
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRows, sortCol, sortAsc]);

  // Pagination slice
  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, currentPage, pageSize]);

  const handleSort = (colName: string) => {
    if (sortCol === colName) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(colName);
      setSortAsc(true);
    }
    setCurrentPage(1);
  };

  const handleCopyCell = (val: any) => {
    const text = val === null || val === undefined ? "NULL" : String(val);
    navigator.clipboard.writeText(text);
    setCopiedCell(text);
    setTimeout(() => setCopiedCell(null), 1500);
  };

  const handleExportCSV = () => {
    if (!rows.length || !columns.length) return;
    const header = columns.map((c) => `"${c.name.replace(/"/g, '""')}"`).join(",");
    const csvLines = rows.map((r) =>
      columns
        .map((c) => {
          const v = r[c.name];
          if (v === null || v === undefined) return "";
          return `"${String(v).replace(/"/g, '""')}"`;
        })
        .join(",")
    );
    const blob = new Blob([[header, ...csvLines].join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `query_result_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    if (!rows.length) return;
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `query_result_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <div className="spinner-border" style={{ marginBottom: "1rem" }} />
        <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>Executing query in DuckDB OLAP engine...</div>
        <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>Running vectorized scan and in-memory aggregation</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        <div style={{ fontSize: "0.875rem", fontWeight: 500 }}>No query executed yet.</div>
        <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
          Write a query above and press <kbd style={{ padding: "0.1rem 0.35rem", backgroundColor: "var(--bg-card)", borderRadius: "3px" }}>Ctrl+Enter</kbd> to run.
        </div>
      </div>
    );
  }

  // Error State
  if (result.status === "FAILED" || result.status === "TIMEOUT" || result.status === "CANCELLED") {
    return (
      <div style={{ padding: "1.5rem" }}>
        <div
          className="card"
          style={{
            borderColor: "var(--color-danger)",
            backgroundColor: "rgba(239, 68, 68, 0.05)",
            padding: "1rem 1.25rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--color-danger)", fontWeight: 600 }}>
            <AlertTriangleIcon size={18} />
            <span>Query {result.status}: Execution Halted</span>
          </div>
          <div
            style={{
              marginTop: "0.75rem",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "0.8125rem",
              color: "var(--text-primary)",
              whiteSpace: "pre-wrap",
              backgroundColor: "var(--bg-input)",
              padding: "0.75rem",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            {result.error_message || "An unexpected error occurred during execution."}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Elapsed execution time: {result.execution_time_ms} ms
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Metrics Bar & Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        {/* Left metrics */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span className="badge badge-emerald" style={{ fontSize: "0.6875rem" }}>
            {result.status}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            <strong>{result.row_count.toLocaleString()}</strong> rows
            {result.is_truncated && (
              <span className="badge badge-amber" style={{ marginLeft: "0.4rem", fontSize: "0.625rem" }}>
                Truncated (max limit)
              </span>
            )}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>•</span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {result.execution_time_ms} ms
          </span>
          {result.cached && (
            <span className="badge badge-indigo" style={{ fontSize: "0.625rem" }}>
              ⚡ Cached Result
            </span>
          )}
        </div>

        {/* Right actions: search & exports */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ position: "relative" }}>
            <SearchIcon
              size={13}
              style={{
                position: "absolute",
                left: "0.5rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            />
            <input
              type="text"
              placeholder="Search in results..."
              value={filterText}
              onChange={(e) => {
                setFilterText(e.target.value);
                setCurrentPage(1);
              }}
              className="input input-sm"
              style={{
                paddingLeft: "1.75rem",
                fontSize: "0.75rem",
                width: "150px",
                height: "26px",
                backgroundColor: "var(--bg-input)",
              }}
            />
          </div>

          <button
            type="button"
            onClick={handleExportCSV}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.6875rem", padding: "0.2rem 0.5rem", height: "26px" }}
            title="Export full result set as CSV"
          >
            <DownloadIcon size={12} />
            CSV
          </button>

          <button
            type="button"
            onClick={handleExportJSON}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.6875rem", padding: "0.2rem 0.5rem", height: "26px" }}
            title="Export full result set as JSON"
          >
            <DownloadIcon size={12} />
            JSON
          </button>
        </div>
      </div>

      {/* Interactive Data Grid */}
      <div style={{ flex: 1, overflow: "auto", position: "relative" }}>
        <table className="table table-hover table-sm" style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
          <thead
            style={{
              position: "sticky",
              top: 0,
              backgroundColor: "var(--bg-surface)",
              zIndex: 2,
              borderBottom: "2px solid var(--border-subtle)",
            }}
          >
            <tr>
              <th style={{ width: "40px", textAlign: "center", color: "var(--text-muted)", fontWeight: 600 }}>#</th>
              {columns.map((col) => {
                const isSorted = sortCol === col.name;
                return (
                  <th
                    key={col.name}
                    onClick={() => handleSort(col.name)}
                    style={{
                      cursor: "pointer",
                      userSelect: "none",
                      padding: "0.5rem 0.75rem",
                      textAlign: col.semantic_type === "numeric" ? "right" : "left",
                      whiteSpace: "nowrap",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.3rem",
                        justifyContent: col.semantic_type === "numeric" ? "flex-end" : "flex-start",
                      }}
                    >
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{col.name}</span>
                      <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", fontWeight: 400 }}>
                        {col.physical_type}
                      </span>
                      {isSorted && (sortAsc ? <ChevronUpIcon size={12} /> : <ChevronDownIcon size={12} />)}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
                  {filterText ? "No matching records found." : "Result set is empty (0 rows returned)."}
                </td>
              </tr>
            ) : (
              paginatedRows.map((row, rowIdx) => {
                const globalIdx = (currentPage - 1) * pageSize + rowIdx + 1;
                return (
                  <tr key={rowIdx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.6875rem" }}>
                      {globalIdx}
                    </td>
                    {columns.map((col) => {
                      const val = row[col.name];
                      const isNumeric = col.semantic_type === "numeric";
                      return (
                        <td
                          key={col.name}
                          onClick={() => handleCopyCell(val)}
                          style={{
                            padding: "0.4rem 0.75rem",
                            textAlign: isNumeric ? "right" : "left",
                            cursor: "pointer",
                            fontFamily: isNumeric ? "var(--font-mono)" : "inherit",
                          }}
                          title="Click to copy value"
                        >
                          {val === null || val === undefined ? (
                            <span className="badge badge-amber" style={{ fontSize: "0.625rem", padding: "0.05rem 0.3rem" }}>
                              NULL
                            </span>
                          ) : val === "" ? (
                            <span style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.6875rem" }}>
                              [empty]
                            </span>
                          ) : typeof val === "boolean" ? (
                            <span className={val ? "badge badge-emerald" : "badge badge-neutral"} style={{ fontSize: "0.625rem" }}>
                              {val ? "TRUE" : "FALSE"}
                            </span>
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.4rem 0.75rem",
          borderTop: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          fontSize: "0.75rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <span style={{ color: "var(--text-muted)" }}>Page size:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="input input-sm"
            style={{ width: "65px", height: "26px", padding: "0.1rem 0.4rem", fontSize: "0.75rem" }}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          {copiedCell && (
            <span style={{ color: "var(--color-success)", marginLeft: "0.5rem", fontSize: "0.6875rem" }}>
              ✓ Copied: "{copiedCell}"
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ color: "var(--text-muted)" }}>
            Page {currentPage} of {totalPages} ({sortedRows.length.toLocaleString()} items)
          </span>
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => p - 1)}
            className="btn btn-secondary btn-sm"
            style={{ padding: "0.15rem 0.45rem", height: "24px", fontSize: "0.6875rem" }}
          >
            Prev
          </button>
          <button
            type="button"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
            className="btn btn-secondary btn-sm"
            style={{ padding: "0.15rem 0.45rem", height: "24px", fontSize: "0.6875rem" }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useMemo } from "react";
import { TableColumn } from "@/types";
import { SearchIcon } from "@/components/icons";
import { TableSkeleton } from "@/components/ui/LoadingState";

interface DataTableProps {
  columns: TableColumn[];
  rows: Record<string, unknown>[];
  totalRows?: number;
  pageSize?: number;
  isLoading?: boolean;
  emptyMessage?: string;
  searchable?: boolean;
}

export function DataTable({
  columns,
  rows,
  totalRows,
  pageSize: initialPageSize = 10,
  isLoading = false,
  emptyMessage = "No records found in this dataset.",
  searchable = true,
}: DataTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Filtering
  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return rows;
    const term = searchTerm.toLowerCase();
    return rows.filter((row) =>
      Object.values(row).some(
        (val) => val !== null && val !== undefined && String(val).toLowerCase().includes(term)
      )
    );
  }, [rows, searchTerm]);

  // Sorting
  const sortedRows = useMemo(() => {
    if (!sortColumn) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const valA = a[sortColumn];
      const valB = b[sortColumn];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === "number" && typeof valB === "number") {
        return sortDirection === "asc" ? valA - valB : valB - valA;
      }
      return sortDirection === "asc"
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });
  }, [filteredRows, sortColumn, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(sortedRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, currentPage, pageSize]);

  const handleSort = (colName: string) => {
    if (sortColumn === colName) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(colName);
      setSortDirection("asc");
    }
  };

  if (isLoading) {
    return <TableSkeleton rows={pageSize} />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Search & Meta Bar */}
      {searchable && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{
              position: "relative",
              maxWidth: "280px",
              width: "100%",
            }}
          >
            <span
              style={{
                position: "absolute",
                left: "0.75rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
                display: "flex",
              }}
            >
              <SearchIcon size={14} />
            </span>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search table rows…"
              aria-label="Filter table rows"
              style={{
                width: "100%",
                backgroundColor: "var(--bg-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "0.4rem 0.75rem 0.4rem 2.2rem",
                fontSize: "0.8125rem",
                color: "var(--text-primary)",
                outline: "none",
              }}
            />
          </div>

          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Showing {paginatedRows.length} of {totalRows ?? sortedRows.length} rows
          </span>
        </div>
      )}

      {/* Table Surface */}
      <div className="table-wrapper">
        <table className="analyzax-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const isSorted = sortColumn === col.name;
                return (
                  <th
                    key={col.name}
                    onClick={() => handleSort(col.name)}
                    style={{ cursor: "pointer" }}
                    title="Click to sort"
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.4rem",
                      }}
                    >
                      <span>{col.name}</span>
                      {col.type && (
                        <span
                          style={{
                            fontSize: "0.6875rem",
                            color: "var(--text-muted)",
                            fontWeight: 400,
                          }}
                        >
                          ({col.type})
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: "0.75rem",
                          color: isSorted ? "var(--accent-primary)" : "var(--text-faint)",
                        }}
                      >
                        {isSorted ? (sortDirection === "asc" ? "▲" : "▼") : "↕"}
                      </span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length > 0 ? (
              paginatedRows.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {columns.map((col) => {
                    const val = row[col.name];
                    const isNum = typeof val === "number";
                    return (
                      <td
                        key={col.name}
                        style={{
                          fontFamily: isNum ? "var(--font-mono)" : "inherit",
                          color:
                            val === null || val === undefined
                              ? "var(--text-faint)"
                              : "inherit",
                        }}
                      >
                        {val === null || val === undefined
                          ? "null"
                          : typeof val === "boolean"
                          ? val ? "true" : "false"
                          : String(val)}
                      </td>
                    );
                  })}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length || 1}
                  style={{
                    textAlign: "center",
                    padding: "2.5rem 1rem",
                    color: "var(--text-muted)",
                  }}
                >
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.35rem 0",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Page {currentPage} of {totalPages} ({totalRows ?? sortedRows.length} items)
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-faint)" }}>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                backgroundColor: "var(--bg-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                color: "var(--text-secondary)",
                fontSize: "0.75rem",
                padding: "0.15rem 0.35rem",
                outline: "none",
              }}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>

        {totalPages > 1 && (
          <div style={{ display: "flex", gap: "0.35rem" }}>
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

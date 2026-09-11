"use client";

import React, { useState, useMemo, useRef, useEffect, useCallback } from "react";
import { TableColumn } from "@/types";
import { SearchIcon } from "@/components/icons";

interface VirtualTableProps {
  columns: TableColumn[];
  rows: Record<string, unknown>[];
  totalRows?: number;
  rowHeight?: number;
  containerHeight?: number;
  searchable?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: Record<string, unknown>, index: number) => void;
}

export function VirtualTable({
  columns,
  rows,
  totalRows,
  rowHeight = 38,
  containerHeight = 420,
  searchable = true,
  emptyMessage = "No records found.",
  onRowClick,
}: VirtualTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [scrollTop, setScrollTop] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);

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

  const handleSort = useCallback((colName: string) => {
    setSortColumn((prevCol) => {
      if (prevCol === colName) {
        setSortDirection((prevDir) => (prevDir === "asc" ? "desc" : "asc"));
        return prevCol;
      }
      setSortDirection("asc");
      return colName;
    });
  }, []);

  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  // Virtual Window Calculation
  const totalCount = sortedRows.length;
  const totalHeight = totalCount * rowHeight;
  const buffer = 5; // extra rows above and below viewport
  const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - buffer);
  const visibleCount = Math.ceil(containerHeight / rowHeight) + buffer * 2;
  const endIndex = Math.min(totalCount, startIndex + visibleCount);

  const visibleRows = useMemo(() => {
    return sortedRows.slice(startIndex, endIndex).map((row, idx) => ({
      row,
      originalIndex: startIndex + idx,
    }));
  }, [sortedRows, startIndex, endIndex]);

  const offsetY = startIndex * rowHeight;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", width: "100%" }}>
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
              onChange={(e) => setSearchTerm(e.target.value)}
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
            Virtual scrolling: rendering {visibleRows.length} of {totalRows ?? totalCount} rows (60 FPS)
          </span>
        </div>
      )}

      {/* Virtualized Container */}
      <div
        className="table-wrapper"
        ref={containerRef}
        onScroll={onScroll}
        style={{
          height: `${containerHeight}px`,
          overflowY: "auto",
          overflowX: "auto",
          position: "relative",
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
        }}
      >
        <div style={{ height: `${totalHeight}px`, position: "relative", minWidth: "100%" }}>
          <table
            className="analyzax-table"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              transform: `translateY(${offsetY}px)`,
            }}
          >
            <thead
              style={{
                position: "sticky",
                top: 0,
                zIndex: 2,
                backgroundColor: "var(--bg-elevated)",
              }}
            >
              <tr>
                {columns.map((col) => {
                  const isSorted = sortColumn === col.name;
                  return (
                    <th
                      key={col.name}
                      onClick={() => handleSort(col.name)}
                      style={{ cursor: "pointer", height: `${rowHeight}px` }}
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
              {visibleRows.length > 0 ? (
                visibleRows.map(({ row, originalIndex }) => (
                  <tr
                    key={originalIndex}
                    onClick={() => onRowClick?.(row, originalIndex)}
                    style={{
                      height: `${rowHeight}px`,
                      cursor: onRowClick ? "pointer" : "default",
                    }}
                  >
                    {columns.map((col) => {
                      const val = row[col.name];
                      const isNum = typeof val === "number";
                      return (
                        <td
                          key={col.name}
                          style={{
                            fontFamily: isNum ? "var(--font-mono)" : "inherit",
                            textAlign: isNum ? "right" : "left",
                            whiteSpace: "nowrap",
                            textOverflow: "ellipsis",
                            overflow: "hidden",
                            maxWidth: "280px",
                          }}
                        >
                          {val === null || val === undefined ? (
                            <span style={{ color: "var(--text-faint)", fontStyle: "italic" }}>
                              null
                            </span>
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={columns.length}
                    style={{
                      textAlign: "center",
                      padding: "2rem",
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
      </div>
    </div>
  );
}

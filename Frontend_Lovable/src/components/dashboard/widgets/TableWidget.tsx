"use client";

import React, { useState } from "react";
import { ComponentDataResponse } from "@/types/dashboard";

interface TableWidgetProps {
  dataResp?: ComponentDataResponse;
  configuration: Record<string, any>;
}

export function TableWidget({ dataResp, configuration }: TableWidgetProps) {
  const tableData = dataResp?.data || configuration.table_data || { columns: [], rows: [], total_rows: 0 };
  const columns: string[] = tableData.columns || [];
  const rows: Record<string, any>[] = tableData.rows || [];
  const totalRows = tableData.total_rows || rows.length;

  const [searchTerm, setSearchTerm] = useState("");

  const filteredRows = React.useMemo(() => {
    if (!searchTerm.trim()) return rows;
    const term = searchTerm.toLowerCase();
    return rows.filter((r) =>
      columns.some((c) => String(r[c] ?? "").toLowerCase().includes(term))
    );
  }, [rows, columns, searchTerm]);

  if (columns.length === 0) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b" }}>
        No table data available
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Table toolbar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem", gap: "0.5rem" }}>
        <input
          type="text"
          placeholder="Filter rows..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(51, 65, 85, 0.6)",
            borderRadius: "4px",
            color: "#e2e8f0",
            fontSize: "0.75rem",
            padding: "0.25rem 0.5rem",
            width: "160px",
          }}
        />
        <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
          Showing {filteredRows.length} of {totalRows} rows
        </span>
      </div>

      {/* Scrollable table */}
      <div style={{ flex: 1, overflow: "auto", border: "1px solid rgba(51, 65, 85, 0.5)", borderRadius: "6px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(30, 41, 59, 0.8)", position: "sticky", top: 0 }}>
              {columns.map((col) => (
                <th
                  key={col}
                  style={{
                    padding: "0.5rem 0.75rem",
                    borderBottom: "1px solid rgba(51, 65, 85, 0.8)",
                    color: "#cbd5e1",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: "1px solid rgba(51, 65, 85, 0.3)",
                  background: idx % 2 === 0 ? "transparent" : "rgba(30, 41, 59, 0.2)",
                }}
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    style={{
                      padding: "0.4rem 0.75rem",
                      color: "#94a3b8",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

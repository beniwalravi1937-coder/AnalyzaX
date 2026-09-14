"use client";

import React, { useState } from "react";
import {
  SchemaTableInfo,
  SchemaColumnInfo,
  SQLTemplate,
} from "@/types";
import {
  DatabaseIcon,
  SearchIcon,
  SparklesIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CopyIcon,
  CheckIcon,
} from "@/components/icons";

interface SchemaExplorerProps {
  schema: SchemaTableInfo | null;
  templates: SQLTemplate[];
  loading?: boolean;
  onInsertText: (text: string) => void;
  onSelectTemplate: (sql: string) => void;
}

export function SchemaExplorer({
  schema,
  templates,
  loading = false,
  onInsertText,
  onSelectTemplate,
}: SchemaExplorerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedColumn, setSelectedColumn] = useState<SchemaColumnInfo | null>(null);
  const [copiedCol, setCopiedCol] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(true);
  const [showColumns, setShowColumns] = useState(true);

  const filteredColumns = schema?.columns.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.physical_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.semantic_type.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const handleCopy = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedCol(text);
    setTimeout(() => setCopiedCol(null), 1500);
  };

  const getSemanticBadge = (semType: string) => {
    switch (semType) {
      case "numeric":
        return <span className="badge badge-blue" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}># num</span>;
      case "categorical":
        return <span className="badge badge-purple" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>Aa cat</span>;
      case "datetime":
        return <span className="badge badge-emerald" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>📅 date</span>;
      case "boolean":
        return <span className="badge badge-amber" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>0/1 bool</span>;
      default:
        return <span className="badge badge-neutral" style={{ fontSize: "0.625rem", padding: "0.1rem 0.35rem" }}>txt</span>;
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "var(--bg-surface)",
        borderRight: "1px solid var(--border-subtle)",
        overflow: "hidden",
      }}
    >
      {/* Search Header */}
      <div style={{ padding: "0.75rem", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ position: "relative" }}>
          <SearchIcon
            size={14}
            style={{
              position: "absolute",
              left: "0.6rem",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-muted)",
            }}
          />
          <input
            type="text"
            placeholder="Search columns & types..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input input-sm"
            style={{
              paddingLeft: "1.9rem",
              fontSize: "0.75rem",
              width: "100%",
              backgroundColor: "var(--bg-input)",
            }}
          />
        </div>
      </div>

      {/* Content Area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.75rem" }}>
        {loading ? (
          <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
            <div className="spinner-border spinner-border-sm" style={{ marginBottom: "0.5rem" }} />
            <div>Introspecting schema...</div>
          </div>
        ) : !schema ? (
          <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
            Select a dataset to browse schema.
          </div>
        ) : (
          <>
            {/* Table Card */}
            <div
              className="card"
              style={{
                padding: "0.625rem 0.75rem",
                marginBottom: "0.75rem",
                backgroundColor: "var(--bg-card)",
                cursor: "pointer",
              }}
              onClick={() => onInsertText(schema.table_alias)}
              title="Click to insert table name into editor"
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <DatabaseIcon size={16} color="var(--primary-light)" />
                  <span style={{ fontWeight: 600, fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                    {schema.table_alias}
                  </span>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-xs"
                  onClick={(e) => handleCopy(e, schema.table_alias)}
                  style={{ padding: "0.15rem 0.35rem" }}
                  title="Copy table alias"
                >
                  {copiedCol === schema.table_alias ? <CheckIcon size={12} color="var(--color-success)" /> : <CopyIcon size={12} />}
                </button>
              </div>
              <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {schema.row_count.toLocaleString()} rows • {schema.column_count} columns • {schema.version_id}
              </div>
            </div>

            {/* Columns Section */}
            <div style={{ marginBottom: "1rem" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  cursor: "pointer",
                  padding: "0.25rem 0",
                  userSelect: "none",
                }}
                onClick={() => setShowColumns(!showColumns)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                  {showColumns ? <ChevronDownIcon size={14} /> : <ChevronRightIcon size={14} />}
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
                    Columns ({filteredColumns.length})
                  </span>
                </div>
              </div>

              {showColumns && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem", marginTop: "0.35rem" }}>
                  {filteredColumns.map((col) => {
                    const isSelected = selectedColumn?.name === col.name;
                    return (
                      <div
                        key={col.name}
                        style={{
                          padding: "0.4rem 0.5rem",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: isSelected ? "var(--bg-active)" : "transparent",
                          border: isSelected ? "1px solid var(--border-focus)" : "1px solid transparent",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) (e.currentTarget.style.backgroundColor = "var(--bg-hover)");
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) (e.currentTarget.style.backgroundColor = "transparent");
                        }}
                        onClick={() => setSelectedColumn(isSelected ? null : col)}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                          <div
                            style={{ display: "flex", alignItems: "center", gap: "0.4rem", flex: 1, minWidth: 0 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              onInsertText(col.name);
                            }}
                            title="Click to insert column into editor"
                          >
                            <span style={{ fontSize: "0.75rem", fontWeight: 500, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {col.name}
                            </span>
                          </div>

                          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                            {getSemanticBadge(col.semantic_type)}
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs"
                              onClick={(e) => handleCopy(e, col.name)}
                              style={{ padding: "0.1rem 0.25rem" }}
                              title="Copy column name"
                            >
                              {copiedCol === col.name ? <CheckIcon size={10} color="var(--color-success)" /> : <CopyIcon size={10} />}
                            </button>
                          </div>
                        </div>

                        {/* Expandable column details & samples */}
                        {isSelected && (
                          <div
                            style={{
                              marginTop: "0.4rem",
                              paddingTop: "0.4rem",
                              borderTop: "1px dashed var(--border-subtle)",
                              fontSize: "0.6875rem",
                              color: "var(--text-secondary)",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.2rem" }}>
                              <span>Type: <code>{col.physical_type}</code></span>
                              <span>Distinct: <strong>{col.cardinality ?? "N/A"}</strong></span>
                            </div>
                            {col.sample_values && col.sample_values.length > 0 && (
                              <div style={{ marginTop: "0.3rem" }}>
                                <span style={{ color: "var(--text-muted)", fontSize: "0.625rem" }}>Top samples:</span>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.2rem", marginTop: "0.15rem" }}>
                                  {col.sample_values.map((val, idx) => (
                                    <span
                                      key={idx}
                                      style={{
                                        padding: "0.1rem 0.35rem",
                                        backgroundColor: "var(--bg-input)",
                                        borderRadius: "3px",
                                        fontSize: "0.625rem",
                                        fontFamily: "var(--font-mono)",
                                      }}
                                    >
                                      {val === null ? <em style={{ color: "var(--color-warning)" }}>null</em> : String(val)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Dynamic Templates Section */}
            {templates && templates.length > 0 && (
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    cursor: "pointer",
                    padding: "0.25rem 0",
                    userSelect: "none",
                  }}
                  onClick={() => setShowTemplates(!showTemplates)}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                    {showTemplates ? <ChevronDownIcon size={14} /> : <ChevronRightIcon size={14} />}
                    <SparklesIcon size={14} color="var(--primary-light)" />
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)" }}>
                      Quick Templates ({templates.length})
                    </span>
                  </div>
                </div>

                {showTemplates && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", marginTop: "0.4rem" }}>
                    {templates.map((tmpl) => (
                      <button
                        key={tmpl.id}
                        type="button"
                        onClick={() => onSelectTemplate(tmpl.sql)}
                        className="btn btn-secondary btn-sm"
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "flex-start",
                          padding: "0.4rem 0.6rem",
                          textAlign: "left",
                          width: "100%",
                        }}
                      >
                        <span style={{ fontSize: "0.75rem", fontWeight: 600 }}>{tmpl.title}</span>
                        <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", marginTop: "0.1rem" }}>
                          {tmpl.description}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

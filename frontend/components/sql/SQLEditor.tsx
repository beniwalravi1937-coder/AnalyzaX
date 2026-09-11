"use client";

import React, { useMemo, useCallback } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql, StandardSQL } from "@codemirror/lang-sql";
import { oneDark } from "@codemirror/theme-one-dark";
import {
  PlayIcon,
  RefreshIcon,
  SparklesIcon,
  SaveIcon,
  EyeIcon,
  CloseIcon,
  AlertTriangleIcon,
} from "@/components/icons";
import { SQLValidationResult, SchemaTableInfo } from "@/types";

interface QueryTab {
  id: string;
  title: string;
  sql: string;
}

interface SQLEditorProps {
  tabs: QueryTab[];
  activeTabId: string;
  onSelectTab: (tabId: string) => void;
  onAddTab: () => void;
  onCloseTab: (tabId: string) => void;
  onChangeQuery: (sql: string) => void;
  onRunQuery: () => void;
  onCancelQuery?: () => void;
  onValidateQuery?: () => void;
  onExplainQuery?: () => void;
  onSaveQuery?: () => void;
  onFormatQuery?: () => void;
  isRunning?: boolean;
  validationResult?: SQLValidationResult | null;
  schema?: SchemaTableInfo | null;
}

export function SQLEditor({
  tabs,
  activeTabId,
  onSelectTab,
  onAddTab,
  onCloseTab,
  onChangeQuery,
  onRunQuery,
  onCancelQuery,
  onValidateQuery,
  onExplainQuery,
  onSaveQuery,
  onFormatQuery,
  isRunning = false,
  validationResult,
  schema,
}: SQLEditorProps) {
  const currentTab = tabs.find((t) => t.id === activeTabId) || tabs[0];
  const queryText = currentTab ? currentTab.sql : "";

  // Schema-aware SQL completions
  const sqlExtension = useMemo(() => {
    const tableSchema: Record<string, string[]> = {};
    if (schema) {
      const colNames = schema.columns.map((c) => c.name);
      tableSchema[schema.table_alias] = colNames;
      tableSchema["dataset"] = colNames;
      tableSchema["current_dataset"] = colNames;
    }

    return sql({
      dialect: StandardSQL,
      schema: tableSchema,
      upperCaseKeywords: true,
    });
  }, [schema]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        if (!isRunning && queryText.trim()) {
          onRunQuery();
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        onSaveQuery?.();
      }
    },
    [isRunning, queryText, onRunQuery, onSaveQuery]
  );

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
      }}
      onKeyDown={handleKeyDown}
    >
      {/* Tabs & Top Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "var(--bg-surface)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "0.25rem 0.5rem 0 0.5rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        {/* Tab Headers */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", overflowX: "auto" }}>
          {tabs.map((tab) => {
            const isActive = tab.id === activeTabId;
            return (
              <div
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  padding: "0.35rem 0.65rem",
                  fontSize: "0.75rem",
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? "var(--primary-light)" : "var(--text-muted)",
                  backgroundColor: isActive ? "var(--bg-card)" : "transparent",
                  borderTopLeftRadius: "var(--radius-sm)",
                  borderTopRightRadius: "var(--radius-sm)",
                  border: isActive ? "1px solid var(--border-subtle)" : "1px solid transparent",
                  borderBottom: isActive ? "1px solid var(--bg-card)" : "1px solid transparent",
                  cursor: "pointer",
                  marginBottom: "-1px",
                }}
              >
                <span>{tab.title}</span>
                {tabs.length > 1 && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onCloseTab(tab.id);
                    }}
                    className="btn btn-ghost btn-xs"
                    style={{ padding: 0, width: "14px", height: "14px" }}
                  >
                    <CloseIcon size={10} />
                  </button>
                )}
              </div>
            );
          })}
          <button
            type="button"
            onClick={onAddTab}
            className="btn btn-ghost btn-xs"
            style={{ fontSize: "0.75rem", padding: "0.2rem 0.4rem", color: "var(--text-muted)" }}
            title="New Query Tab"
          >
            + Tab
          </button>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", paddingBottom: "0.25rem" }}>
          {onFormatQuery && (
            <button
              type="button"
              onClick={onFormatQuery}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
              title="Format SQL query"
            >
              <SparklesIcon size={13} />
              Format
            </button>
          )}

          {onValidateQuery && (
            <button
              type="button"
              onClick={onValidateQuery}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
              title="Validate SQL without executing"
            >
              Validate
            </button>
          )}

          {onExplainQuery && (
            <button
              type="button"
              onClick={onExplainQuery}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
              title="View query execution plan"
            >
              <EyeIcon size={13} />
              Explain
            </button>
          )}

          {onSaveQuery && (
            <button
              type="button"
              onClick={onSaveQuery}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
              title="Save Query (Ctrl+S)"
            >
              <SaveIcon size={13} />
              Save
            </button>
          )}

          {isRunning ? (
            <button
              type="button"
              onClick={onCancelQuery}
              className="btn btn-sm btn-danger"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.8rem" }}
            >
              <RefreshIcon size={13} className="spin" />
              Cancel
            </button>
          ) : (
            <button
              type="button"
              onClick={onRunQuery}
              disabled={!queryText.trim()}
              className="btn btn-primary btn-sm"
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.85rem", fontWeight: 600 }}
              title="Run Query (Ctrl+Enter)"
            >
              <PlayIcon size={13} />
              Run Query
            </button>
          )}
        </div>
      </div>

      {/* CodeMirror Editor Area */}
      <div style={{ position: "relative", minHeight: "180px", maxHeight: "350px", overflow: "auto" }}>
        <CodeMirror
          value={queryText}
          height="220px"
          theme={oneDark}
          extensions={[sqlExtension]}
          onChange={(val) => onChangeQuery(val)}
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            highlightSpecialChars: true,
            history: true,
            foldGutter: true,
            drawSelection: true,
            dropCursor: true,
            allowMultipleSelections: true,
            indentOnInput: true,
            bracketMatching: true,
            closeBrackets: true,
            autocompletion: true,
            rectangularSelection: true,
            crosshairCursor: true,
            highlightActiveLine: true,
            highlightSelectionMatches: true,
            closeBracketsKeymap: true,
            searchKeymap: true,
            foldKeymap: true,
            completionKeymap: true,
            lintKeymap: true,
          }}
          style={{ fontSize: "0.8125rem", fontFamily: "var(--font-mono, monospace)" }}
        />
      </div>

      {/* Validation Feedback Banner */}
      {validationResult && (
        <div style={{ borderTop: "1px solid var(--border-subtle)", padding: "0.5rem 0.75rem", fontSize: "0.75rem" }}>
          {!validationResult.is_valid && validationResult.errors.length > 0 ? (
            <div style={{ color: "var(--color-danger)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <AlertTriangleIcon size={14} />
              <span>{validationResult.errors.map((e) => e.message).join("; ")}</span>
            </div>
          ) : validationResult.warnings.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {validationResult.warnings.map((w, idx) => (
                <div key={idx} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", color: "var(--color-warning)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <AlertTriangleIcon size={13} />
                    <span>{w.message}</span>
                  </div>
                  {w.suggestion && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-xs"
                      onClick={() => {
                        if (w.warning_code === "COLUMN_TYPO" && w.suggestion) {
                          // Replace typo with suggestion
                          const words = queryText.split(/\b/);
                          const typoWord = w.message.match(/'([^']+)'/)?.[1];
                          if (typoWord) {
                            onChangeQuery(queryText.replace(new RegExp(`\\b${typoWord}\\b`), w.suggestion));
                          }
                        }
                      }}
                      style={{ fontSize: "0.6875rem", textDecoration: "underline", color: "var(--primary-light)" }}
                    >
                      Apply: {w.suggestion}
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "var(--color-success)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span>✓ Query is valid and secure.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

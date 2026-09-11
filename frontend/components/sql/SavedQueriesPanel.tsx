"use client";

import React, { useState } from "react";
import { SavedQuery } from "@/types";
import {
  SaveIcon,
  PlayIcon,
  TrashIcon,
  EditIcon,
  TagIcon,
  SearchIcon,
  CloseIcon,
} from "@/components/icons";

interface SavedQueriesPanelProps {
  queries: SavedQuery[];
  onLoadQuery: (sql: string) => void;
  onSaveQuery: (data: {
    name: string;
    description?: string;
    sql: string;
    tags?: string[];
  }) => void;
  onUpdateQuery: (id: string, data: Partial<SavedQuery>) => void;
  onDeleteQuery: (id: string) => void;
  currentSql?: string;
  loading?: boolean;
}

export function SavedQueriesPanel({
  queries,
  onLoadQuery,
  onSaveQuery,
  onUpdateQuery,
  onDeleteQuery,
  currentSql = "",
  loading = false,
}: SavedQueriesPanelProps) {
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingQuery, setEditingQuery] = useState<SavedQuery | null>(null);

  // Modal form state
  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formTags, setFormTags] = useState("");
  const [formSql, setFormSql] = useState("");

  // Collect all unique tags
  const allTags = Array.from(new Set(queries.flatMap((q) => q.tags || [])));

  const filtered = queries.filter((q) => {
    const matchesSearch =
      q.name.toLowerCase().includes(search.toLowerCase()) ||
      (q.description && q.description.toLowerCase().includes(search.toLowerCase())) ||
      q.sql.toLowerCase().includes(search.toLowerCase());
    const matchesTag = !selectedTag || (q.tags && q.tags.includes(selectedTag));
    return matchesSearch && matchesTag;
  });

  const handleOpenCreateModal = () => {
    setEditingQuery(null);
    setFormName("");
    setFormDesc("");
    setFormTags("");
    setFormSql(currentSql);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (q: SavedQuery) => {
    setEditingQuery(q);
    setFormName(q.name);
    setFormDesc(q.description || "");
    setFormTags((q.tags || []).join(", "));
    setFormSql(q.sql);
    setIsModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formSql.trim()) return;

    const tagsList = formTags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    if (editingQuery) {
      onUpdateQuery(editingQuery.id, {
        name: formName.trim(),
        description: formDesc.trim(),
        sql: formSql.trim(),
        tags: tagsList,
      });
    } else {
      onSaveQuery({
        name: formName.trim(),
        description: formDesc.trim(),
        sql: formSql.trim(),
        tags: tagsList,
      });
    }
    setIsModalOpen(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Top Header & Search */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          gap: "0.5rem",
        }}
      >
        <div style={{ position: "relative", flex: 1 }}>
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
            placeholder="Search saved queries..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input input-sm"
            style={{
              paddingLeft: "1.75rem",
              fontSize: "0.75rem",
              width: "100%",
              backgroundColor: "var(--bg-input)",
            }}
          />
        </div>

        <button
          type="button"
          onClick={handleOpenCreateModal}
          className="btn btn-primary btn-sm"
          style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem", whiteSpace: "nowrap" }}
        >
          <SaveIcon size={12} />
          Save Active
        </button>
      </div>

      {/* Tag Filter Pills */}
      {allTags.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
            padding: "0.4rem 0.75rem",
            borderBottom: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            overflowX: "auto",
          }}
        >
          <button
            type="button"
            onClick={() => setSelectedTag(null)}
            className={`btn btn-xs ${selectedTag === null ? "btn-primary" : "btn-ghost"}`}
            style={{ fontSize: "0.6875rem", padding: "0.1rem 0.4rem" }}
          >
            All
          </button>
          {allTags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
              className={`btn btn-xs ${selectedTag === tag ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.6875rem", padding: "0.1rem 0.4rem" }}
            >
              #{tag}
            </button>
          ))}
        </div>
      )}

      {/* Saved Queries List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.5rem" }}>
        {loading ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
            <div className="spinner-border spinner-border-sm" style={{ marginBottom: "0.5rem" }} />
            <div style={{ fontSize: "0.8125rem" }}>Loading saved queries...</div>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
            <SaveIcon size={28} style={{ marginBottom: "0.5rem", opacity: 0.5 }} />
            <div style={{ fontWeight: 500, fontSize: "0.875rem" }}>
              {search ? "No matching queries found." : "No saved queries yet."}
            </div>
            <div style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
              Save queries to build a library of reusable analytical formulas and KPI reports.
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {filtered.map((q) => (
              <div
                key={q.id}
                className="card"
                style={{
                  padding: "0.6rem 0.75rem",
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-sm)",
                  cursor: "pointer",
                }}
                onClick={() => onLoadQuery(q.sql)}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                  <span style={{ fontWeight: 600, fontSize: "0.8125rem", color: "var(--text-primary)" }}>
                    {q.name}
                  </span>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenEditModal(q);
                      }}
                      className="btn btn-ghost btn-xs"
                      style={{ padding: "0.15rem 0.35rem" }}
                      title="Edit Saved Query"
                    >
                      <EditIcon size={12} />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteQuery(q.id);
                      }}
                      className="btn btn-ghost btn-xs"
                      style={{ padding: "0.15rem 0.35rem", color: "var(--color-danger)" }}
                      title="Delete Saved Query"
                    >
                      <TrashIcon size={12} />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onLoadQuery(q.sql);
                      }}
                      className="btn btn-secondary btn-xs"
                      style={{ padding: "0.15rem 0.4rem", fontSize: "0.6875rem" }}
                      title="Load into Editor"
                    >
                      <PlayIcon size={10} />
                      Load
                    </button>
                  </div>
                </div>

                {q.description && (
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                    {q.description}
                  </div>
                )}

                <div
                  style={{
                    fontFamily: "var(--font-mono, monospace)",
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    backgroundColor: "var(--bg-input)",
                    padding: "0.25rem 0.5rem",
                    borderRadius: "3px",
                  }}
                >
                  {q.sql}
                </div>

                {q.tags && q.tags.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem", marginTop: "0.35rem" }}>
                    {q.tags.map((tag) => (
                      <span key={tag} className="badge badge-neutral" style={{ fontSize: "0.625rem" }}>
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Save / Edit Modal Dialog */}
      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.6)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "1rem",
          }}
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: "500px",
              backgroundColor: "var(--bg-surface)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
              padding: "1.25rem",
              boxShadow: "var(--shadow-lg)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
              <div style={{ fontWeight: 600, fontSize: "0.9375rem" }}>
                {editingQuery ? "Edit Saved Query" : "Save Analytical Query"}
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="btn btn-ghost btn-xs"
              >
                <CloseIcon size={14} />
              </button>
            </div>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  Query Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Monthly Revenue by Region"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="input input-sm"
                  style={{ width: "100%", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Optional context or business purpose"
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="input input-sm"
                  style={{ width: "100%", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="finance, reporting, kpi"
                  value={formTags}
                  onChange={(e) => setFormTags(e.target.value)}
                  className="input input-sm"
                  style={{ width: "100%", fontSize: "0.8125rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  SQL Query *
                </label>
                <textarea
                  rows={4}
                  required
                  value={formSql}
                  onChange={(e) => setFormSql(e.target.value)}
                  className="input"
                  style={{
                    width: "100%",
                    fontFamily: "var(--font-mono, monospace)",
                    fontSize: "0.75rem",
                    padding: "0.5rem",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="btn btn-secondary btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  {editingQuery ? "Update Query" : "Save Query"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

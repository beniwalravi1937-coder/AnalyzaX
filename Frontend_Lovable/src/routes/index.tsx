import { createFileRoute } from "@tanstack/react-router";
import React, { useEffect, useState } from "react";
import { Dashboard } from "@/types/dashboard";
import { createDashboard, deleteDashboard, duplicateDashboard, listDashboards } from "@/services/dashboardApi";
import { useDataset } from "@/context/DatasetContext";
import { useAuth } from "@/context/AuthContext";
import { PageHeader } from "@/components/layout/PageHeader";
import { DashboardWorkspace } from "@/components/dashboard/DashboardWorkspace";
import { STARTER_TEMPLATES } from "@/components/dashboard/templates";
import { LandingPage } from "@/components/landing/LandingPage";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AnalyzaX — Turn Raw Data Into Executive Insights in Seconds" },
      {
        name: "description",
        content:
          "Upload your data and get instant cleaning, charts, and AI-generated insights — no SQL required. Built for modern teams.",
      },
      { property: "og:title", content: "AnalyzaX — Turn Raw Data Into Executive Insights in Seconds" },
      {
        property: "og:description",
        content:
          "Upload your data and get instant cleaning, charts, and AI-generated insights — no SQL required.",
      },
    ],
  }),
  component: IndexRouteComponent,
});

function IndexRouteComponent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (!isLoading && !isAuthenticated) {
    return <LandingPage />;
  }

  return <DashboardPage />;
}

function DashboardPage() {
  const { activeDataset } = useDataset();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [selectedDashboardId, setSelectedDashboardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreatingModal, setIsCreatingModal] = useState(false);

  // New dashboard form state
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string>("executive_overview");

  useEffect(() => {
    loadDashboards();
  }, [activeDataset]);

  const loadDashboards = async () => {
    setIsLoading(true);
    try {
      const list = await listDashboards(activeDataset?.id);
      setDashboards(list);
    } catch (err) {
      console.error("Failed to load dashboards:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDashboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !activeDataset) return;

    try {
      const created = await createDashboard({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
        dataset_id: activeDataset.id,
        dataset_version_id: activeDataset.active_version_id || "v1",
        template_id: selectedTemplate === "blank" ? undefined : selectedTemplate,
      });

      setIsCreatingModal(false);
      setNewName("");
      setNewDesc("");
      setSelectedDashboardId(created.dashboard_id);
    } catch (err: any) {
      alert(`Failed to create dashboard: ${err.message}`);
    }
  };

  const handleDelete = async (dashboardId: string, name: string) => {
    if (!confirm(`Delete dashboard '${name}'?`)) return;
    try {
      await deleteDashboard(dashboardId);
      await loadDashboards();
    } catch (err: any) {
      alert(`Failed to delete: ${err.message}`);
    }
  };

  const handleDuplicate = async (dashboardId: string) => {
    try {
      await duplicateDashboard(dashboardId);
      await loadDashboards();
    } catch (err: any) {
      alert(`Failed to duplicate: ${err.message}`);
    }
  };

  if (selectedDashboardId) {
    return (
      <DashboardWorkspace
        dashboardId={selectedDashboardId}
        onBackToList={() => {
          setSelectedDashboardId(null);
          loadDashboards();
        }}
      />
    );
  }

  const filteredDashboards = dashboards.filter((d) =>
    searchTerm ? d.name.toLowerCase().includes(searchTerm.toLowerCase()) : true
  );

  return (
    <div className="ax-stack">
      <PageHeader
        title="Dashboards & Insight Workspaces"
        description="Transform analytical findings, KPI metrics, charts, statistics, and forecasts into persistent interactive dashboards."
        badge={{ text: "Phase 14 — Active", variant: "indigo" }}
        actions={
          <button
            onClick={() => {
              if (!activeDataset) {
                alert("Please select or upload a dataset first.");
                return;
              }
              setIsCreatingModal(true);
            }}
            className="btn btn-primary btn-sm"
          >
            + Create Dashboard
          </button>
        }
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <input
            type="text"
            placeholder="Search dashboards..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input"
            style={{ width: "260px", fontSize: "0.85rem" }}
          />
          {activeDataset && (
            <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
              Active dataset: <strong>{activeDataset.original_filename}</strong>
            </span>
          )}
        </div>

        <span style={{ fontSize: "0.85rem", color: "#64748b" }}>
          {filteredDashboards.length} dashboard{filteredDashboards.length !== 1 ? "s" : ""}
        </span>
      </div>

      {isLoading ? (
        <div style={{ textAlign: "center", color: "#94a3b8", padding: "4rem" }}>
          Loading saved dashboards...
        </div>
      ) : filteredDashboards.length === 0 ? (
        <div
          style={{
            border: "2px dashed rgba(51, 65, 85, 0.6)",
            borderRadius: "12px",
            padding: "4rem 2rem",
            textAlign: "center",
            background: "rgba(15, 23, 42, 0.4)",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>📈</div>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ffffff", marginBottom: "0.5rem" }}>
            No Dashboards Found
          </h3>
          <p style={{ color: "#94a3b8", maxWidth: "480px", margin: "0 auto 1.5rem auto", fontSize: "0.9rem" }}>
            {activeDataset
              ? "Create your first dashboard to assemble KPIs, ChartSpec visualizations, and analytical cards."
              : "Upload or select a dataset from the sidebar to begin building interactive dashboards."}
          </p>
          {activeDataset && (
            <button onClick={() => setIsCreatingModal(true)} className="btn btn-primary">
              + Create Dashboard
            </button>
          )}
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "1.25rem",
          }}
        >
          {filteredDashboards.map((d) => (
            <div
              key={d.dashboard_id}
              style={{
                background: "#1e293b",
                border: "1px solid rgba(51, 65, 85, 0.6)",
                borderRadius: "10px",
                padding: "1.25rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2)",
                transition: "all 0.15s ease",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                  <h3
                    onClick={() => setSelectedDashboardId(d.dashboard_id)}
                    style={{
                      margin: 0,
                      fontSize: "1.1rem",
                      fontWeight: 700,
                      color: "#ffffff",
                      cursor: "pointer",
                    }}
                  >
                    {d.name}
                  </h3>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      background: "rgba(99, 102, 241, 0.2)",
                      color: "#a5b4fc",
                      padding: "0.15rem 0.45rem",
                      borderRadius: "4px",
                      fontWeight: 600,
                    }}
                  >
                    v{d.version}
                  </span>
                </div>

                <p style={{ margin: "0 0 1rem 0", fontSize: "0.85rem", color: "#94a3b8", lineHeight: 1.4 }}>
                  {d.description || "No description provided."}
                </p>

                <div style={{ display: "flex", gap: "0.75rem", fontSize: "0.75rem", color: "#cbd5e1", marginBottom: "1rem" }}>
                  <span>📊 {d.components?.length || 0} widgets</span>
                  <span>🔍 {d.filters?.length || 0} filters</span>
                  <span>🏷️ {d.dataset_version_id}</span>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  borderTop: "1px solid rgba(51, 65, 85, 0.5)",
                  paddingTop: "0.75rem",
                }}
              >
                <button
                  onClick={() => setSelectedDashboardId(d.dashboard_id)}
                  className="btn btn-primary btn-sm"
                >
                  Open Studio →
                </button>

                <div style={{ display: "flex", gap: "0.4rem" }}>
                  <button
                    onClick={() => handleDuplicate(d.dashboard_id)}
                    className="btn btn-secondary btn-sm"
                    title="Duplicate"
                  >
                    Duplicate
                  </button>
                  <button
                    onClick={() => handleDelete(d.dashboard_id, d.name)}
                    className="btn btn-secondary btn-sm"
                    style={{ color: "#f87171" }}
                    title="Delete"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dashboard Modal */}
      {isCreatingModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.8)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setIsCreatingModal(false)}
        >
          <div
            style={{
              background: "#1e293b",
              border: "1px solid rgba(99, 102, 241, 0.4)",
              borderRadius: "12px",
              padding: "1.75rem",
              maxWidth: "540px",
              width: "90%",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.6)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
              Create New Dashboard
            </h3>

            <form onSubmit={handleCreateDashboard} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
                  Dashboard Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Q3 Sales & Performance Overview"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="input"
                  style={{ width: "100%", fontSize: "0.85rem" }}
                  autoFocus
                  required
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.35rem" }}>
                  Description (Optional)
                </label>
                <textarea
                  placeholder="Summary of analytical goals and audience..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={2}
                  className="input"
                  style={{ width: "100%", fontSize: "0.85rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "0.5rem" }}>
                  Starter Template
                </label>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      fontSize: "0.85rem",
                      color: "#e2e8f0",
                      cursor: "pointer",
                      padding: "0.5rem",
                      borderRadius: "6px",
                      background: selectedTemplate === "blank" ? "rgba(99, 102, 241, 0.2)" : "rgba(15, 23, 42, 0.5)",
                    }}
                  >
                    <input
                      type="radio"
                      name="template"
                      value="blank"
                      checked={selectedTemplate === "blank"}
                      onChange={(e) => setSelectedTemplate(e.target.value)}
                    />
                    <div>
                      <strong>Blank Canvas</strong> — Start from scratch with an empty 12-column responsive grid.
                    </div>
                  </label>

                  {STARTER_TEMPLATES.map((tmpl) => (
                    <label
                      key={tmpl.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "0.85rem",
                        color: "#e2e8f0",
                        cursor: "pointer",
                        padding: "0.5rem",
                        borderRadius: "6px",
                        background: selectedTemplate === tmpl.id ? "rgba(99, 102, 241, 0.2)" : "rgba(15, 23, 42, 0.5)",
                      }}
                    >
                      <input
                        type="radio"
                        name="template"
                        value={tmpl.id}
                        checked={selectedTemplate === tmpl.id}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                      />
                      <div>
                        <strong>{tmpl.name}</strong> — {tmpl.description}
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.5rem" }}>
                <button
                  type="button"
                  onClick={() => setIsCreatingModal(false)}
                  className="btn btn-secondary btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Create & Open
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

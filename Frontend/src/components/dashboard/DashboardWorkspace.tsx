"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  ComponentCreateRequest,
  ComponentDataResponse,
  ComponentType,
  Dashboard,
  DashboardComponent,
  DashboardFilter,
} from "@/types/dashboard";
import {
  addComponent,
  deleteComponent,
  deleteDashboard,
  duplicateComponent,
  duplicateDashboard,
  exportDashboard,
  getDashboard,
  getDashboardData,
  updateComponent,
  updateDashboard,
} from "@/services/dashboardApi";
import { DashboardHeader } from "./DashboardHeader";
import { DashboardFilterBar } from "./DashboardFilterBar";
import { DashboardGrid } from "./DashboardGrid";
import { ComponentPaletteModal } from "./ComponentPaletteModal";
import { ComponentConfigDrawer } from "./ComponentConfigDrawer";
import { ProvenanceModal } from "./ProvenanceModal";
import { DashboardHistoryDrawer } from "./DashboardHistoryDrawer";

interface DashboardWorkspaceProps {
  dashboardId: string;
  onBackToList: () => void;
}

export function DashboardWorkspace({ dashboardId, onBackToList }: DashboardWorkspaceProps) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [componentData, setComponentData] = useState<Record<string, ComponentDataResponse>>({});
  const [isEditMode, setIsEditMode] = useState(true);
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved" | "error">("saved");
  const [isLoading, setIsLoading] = useState(true);

  // Modals and Drawers
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [selectedComponentForEdit, setSelectedComponentForEdit] = useState<DashboardComponent | null>(null);
  const [selectedComponentForProv, setSelectedComponentForProv] = useState<DashboardComponent | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Load dashboard and hydrated data
  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    try {
      const [dash, dataResp] = await Promise.all([
        getDashboard(dashboardId),
        getDashboardData(dashboardId).catch(() => ({ components: {} } as any)),
      ]);
      setDashboard(dash);
      setComponentData(dataResp.components || {});
      setSaveStatus("saved");
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setIsLoading(false);
    }
  }, [dashboardId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Persist dashboard state with debounced autosave
  const persistChanges = async (updated: Dashboard) => {
    setSaveStatus("saving");
    try {
      const saved = await updateDashboard(dashboardId, {
        name: updated.name,
        description: updated.description,
        components: updated.components,
        filters: updated.filters,
        layout: updated.layout,
        theme: updated.theme,
      });
      setDashboard(saved);
      setSaveStatus("saved");

      // Refresh component data to reflect new filters/components
      const dataResp = await getDashboardData(dashboardId);
      setComponentData(dataResp.components || {});
    } catch (err) {
      console.error("Failed to save dashboard:", err);
      setSaveStatus("error");
    }
  };

  const scheduleSave = (updated: Dashboard) => {
    setDashboard(updated);
    setSaveStatus("unsaved");
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      persistChanges(updated);
    }, 1200);
  };

  // Rename
  const handleRename = (newName: string) => {
    if (!dashboard) return;
    const updated = { ...dashboard, name: newName };
    scheduleSave(updated);
  };

  // Add filter
  const handleAddFilter = (newFilter: DashboardFilter) => {
    if (!dashboard) return;
    const updated = { ...dashboard, filters: [...dashboard.filters, newFilter] };
    scheduleSave(updated);
  };

  // Remove filter
  const handleRemoveFilter = (filterId: string) => {
    if (!dashboard) return;
    const updated = { ...dashboard, filters: dashboard.filters.filter((f) => f.filter_id !== filterId) };
    scheduleSave(updated);
  };

  // Clear all filters
  const handleClearFilters = () => {
    if (!dashboard) return;
    const updated = { ...dashboard, filters: [] };
    scheduleSave(updated);
  };

  // Cross-filtering trigger
  const handleCrossFilter = (field: string, value: any) => {
    if (!dashboard) return;
    const existing = dashboard.filters.find((f) => f.field === field);
    let updatedFilters: DashboardFilter[];
    if (existing) {
      updatedFilters = dashboard.filters.map((f) => (f.field === field ? { ...f, value } : f));
    } else {
      updatedFilters = [
        ...dashboard.filters,
        {
          filter_id: `flt_${Math.random().toString(36).slice(2, 9)}`,
          field,
          operator: "equals",
          value,
          data_type: "categorical",
          scope: "GLOBAL",
        },
      ];
    }
    const updated = { ...dashboard, filters: updatedFilters };
    scheduleSave(updated);
  };

  // Select component from Palette
  const handleSelectPaletteType = async (type: ComponentType) => {
    if (!dashboard) return;
    try {
      const newComp = await addComponent(dashboardId, {
        type,
        title: `New ${type.replace("_", " ")}`,
        size: { width: type === "TEXT" || type === "TABLE" ? 12 : 6, height: 4 },
        configuration:
          type === "KPI"
            ? { metric: "count", value: 120, formatting: "compact" }
            : type === "TEXT"
            ? { content: "### Section Heading\nEnter notes or strategic context here." }
            : {},
        source: {
          source_type: "MANUAL",
          dataset_id: dashboard.dataset_id,
          dataset_version_id: dashboard.dataset_version_id,
          engine: "core",
        },
      });

      await loadDashboard();
    } catch (err: any) {
      alert(`Failed to add component: ${err.message}`);
    }
  };

  // Resize width
  const handleResizeWidth = (componentId: string, newWidth: number) => {
    if (!dashboard) return;
    const updatedComponents = dashboard.components.map((c) =>
      c.component_id === componentId ? { ...c, size: { ...c.size, width: newWidth } } : c
    );
    const updated = { ...dashboard, components: updatedComponents };
    scheduleSave(updated);
  };

  // Duplicate component
  const handleDuplicateComponent = async (componentId: string) => {
    try {
      await duplicateComponent(dashboardId, componentId);
      await loadDashboard();
    } catch (err: any) {
      alert(`Failed to duplicate component: ${err.message}`);
    }
  };

  // Delete component
  const handleDeleteComponent = async (componentId: string) => {
    try {
      await deleteComponent(dashboardId, componentId);
      await loadDashboard();
    } catch (err: any) {
      alert(`Failed to delete component: ${err.message}`);
    }
  };

  // Duplicate dashboard
  const handleDuplicateDashboard = async () => {
    if (!dashboard) return;
    try {
      await duplicateDashboard(dashboardId);
      alert("Dashboard duplicated successfully!");
      onBackToList();
    } catch (err: any) {
      alert(`Failed to duplicate dashboard: ${err.message}`);
    }
  };

  // Export
  const handleExport = async () => {
    try {
      const data = await exportDashboard(dashboardId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${dashboard?.name || "dashboard"}_config.json`;
      a.click();
    } catch (err: any) {
      alert(`Failed to export dashboard: ${err.message}`);
    }
  };

  // Delete dashboard
  const handleDeleteDashboard = async () => {
    if (!confirm(`Are you sure you want to delete '${dashboard?.name}'? This cannot be undone.`)) {
      return;
    }
    try {
      await deleteDashboard(dashboardId);
      onBackToList();
    } catch (err: any) {
      alert(`Failed to delete dashboard: ${err.message}`);
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: "4rem", textAlign: "center", color: "#94a3b8" }}>
        Loading dashboard workspace...
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div style={{ padding: "4rem", textAlign: "center", color: "#f87171" }}>
        Dashboard not found.
        <button onClick={onBackToList} className="btn btn-secondary btn-sm" style={{ display: "block", margin: "1rem auto" }}>
          Back to Dashboards
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Workspace Header */}
      <div style={{ marginBottom: "0.5rem" }}>
        <button
          onClick={onBackToList}
          style={{
            background: "transparent",
            border: "none",
            color: "#818cf8",
            cursor: "pointer",
            fontSize: "0.85rem",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            padding: 0,
            marginBottom: "0.5rem",
          }}
        >
          ← Back to Dashboards
        </button>
      </div>

      <DashboardHeader
        dashboard={dashboard}
        isEditMode={isEditMode}
        saveStatus={saveStatus}
        onToggleEditMode={() => setIsEditMode(!isEditMode)}
        onRename={handleRename}
        onSave={() => persistChanges(dashboard)}
        onOpenPalette={() => setIsPaletteOpen(true)}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onDuplicate={handleDuplicateDashboard}
        onExport={handleExport}
        onDelete={handleDeleteDashboard}
      />

      {/* Global Filter Bar */}
      <DashboardFilterBar
        filters={dashboard.filters}
        onAddFilter={handleAddFilter}
        onRemoveFilter={handleRemoveFilter}
        onClearFilters={handleClearFilters}
      />

      {/* 12-Column Responsive Grid */}
      <DashboardGrid
        components={dashboard.components}
        componentData={componentData}
        isEditMode={isEditMode}
        onEditComponent={(cmp) => setSelectedComponentForEdit(cmp)}
        onDuplicateComponent={handleDuplicateComponent}
        onDeleteComponent={handleDeleteComponent}
        onResizeWidth={handleResizeWidth}
        onInspectProvenance={(cmp) => setSelectedComponentForProv(cmp)}
        onCrossFilter={handleCrossFilter}
        onOpenPalette={() => setIsPaletteOpen(true)}
      />

      {/* Component Palette Modal */}
      <ComponentPaletteModal
        isOpen={isPaletteOpen}
        onClose={() => setIsPaletteOpen(false)}
        onSelectType={handleSelectPaletteType}
      />

      {/* Component Configuration Drawer */}
      <ComponentConfigDrawer
        component={selectedComponentForEdit}
        isOpen={!!selectedComponentForEdit}
        onClose={() => setSelectedComponentForEdit(null)}
        onSave={async (updatedFields) => {
          if (!selectedComponentForEdit) return;
          await updateComponent(dashboardId, selectedComponentForEdit.component_id, updatedFields);
          await loadDashboard();
        }}
        onDelete={handleDeleteComponent}
      />

      {/* Provenance & Source Modal */}
      <ProvenanceModal
        component={selectedComponentForProv}
        dataResp={selectedComponentForProv ? componentData[selectedComponentForProv.component_id] : undefined}
        onClose={() => setSelectedComponentForProv(null)}
      />

      {/* Version History Drawer */}
      <DashboardHistoryDrawer
        dashboardId={dashboardId}
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onVersionRestored={loadDashboard}
      />
    </div>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import React, { useState, useEffect, useCallback } from "react";
import { useDataset } from "@/context/DatasetContext";
import { apiClient, ApiError } from "@/services/api";
import {
  CleaningRecommendation,
  DatasetVersion,
  TransformationStep,
  TransformationPreview,
  QualityComparison,
} from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { GuidedOnboarding } from "@/components/ui/GuidedOnboarding";
import { CleanIcon, UploadIcon, AlertCircleIcon } from "@/components/icons";
import {
  CleaningRecommendations,
  TransformationPlanBuilder,
  DataPreviewTable,
  ApplyPlanDialog,
  BeforeAfterComparisonModal,
  DatasetVersionSelector,
} from "@/components/cleaning";

export const Route = createFileRoute("/cleaning")({
  head: () => ({
    meta: [
      { title: "Data Cleaning Studio — AnalyzaX" },
      {
        name: "description",
        content:
          "Fix messy rows, remove duplicates, and fill missing values with one click. Track every version safely without losing your original data.",
      },
      { property: "og:title", content: "Data Cleaning Studio — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Fix messy rows, remove duplicates, and fill missing values with one click. Track every version safely.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-cleaning.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-cleaning.png" },
    ],
  }),
  component: CleaningPage,
});

function CleaningPage() {
  const { activeDataset, isLoading: isDatasetLoading, refreshDatasets } = useDataset();

  // State
  const [recommendations, setRecommendations] = useState<CleaningRecommendation[]>([]);
  const [planSteps, setPlanSteps] = useState<TransformationStep[]>([]);
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [activeVersionId, setActiveVersionId] = useState<string>("v1");
  const [preview, setPreview] = useState<TransformationPreview | null>(null);

  // Modals
  const [isApplyDialogOpen, setIsApplyDialogOpen] = useState<boolean>(false);
  const [comparisonModalData, setComparisonModalData] = useState<{
    comparison: QualityComparison;
    newVersion: DatasetVersion;
  } | null>(null);

  // Loadings
  const [isLoadingRecs, setIsLoadingRecs] = useState<boolean>(false);
  const [isLoadingPlan, setIsLoadingPlan] = useState<boolean>(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState<boolean>(false);
  const [isApplyLoading, setIsApplyLoading] = useState<boolean>(false);
  const [isVersionLoading, setIsVersionLoading] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // 1. Fetch versions
  const fetchVersions = useCallback(async (datasetId: string) => {
    setIsVersionLoading(true);
    try {
      const vers = await apiClient.getDatasetVersions(datasetId);
      setVersions(vers);
      const active = await apiClient.getActiveDatasetVersion(datasetId);
      setActiveVersionId(active.version_id);
    } catch (err) {
      console.error("Failed to load versions:", err);
    } finally {
      setIsVersionLoading(false);
    }
  }, []);

  // 2. Fetch recommendations
  const fetchRecommendations = useCallback(async (datasetId: string, force = false) => {
    setIsLoadingRecs(true);
    setError(null);
    try {
      const recs = await apiClient.getCleaningRecommendations(datasetId, force);
      setRecommendations(recs);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to generate cleaning recommendations.");
      }
    } finally {
      setIsLoadingRecs(false);
    }
  }, []);

  // 3. Fetch plan
  const fetchPlan = useCallback(async (datasetId: string) => {
    setIsLoadingPlan(true);
    try {
      const plan = await apiClient.getTransformationPlan(datasetId);
      setPlanSteps(plan.steps || []);
    } catch (err) {
      console.error("Failed to load plan:", err);
    } finally {
      setIsLoadingPlan(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    if (activeDataset) {
      fetchVersions(activeDataset.id);
      fetchRecommendations(activeDataset.id);
      fetchPlan(activeDataset.id);
      setPreview(null);
      setError(null);
      setSuccessBanner(null);
    } else {
      setRecommendations([]);
      setPlanSteps([]);
      setVersions([]);
      setPreview(null);
    }
  }, [activeDataset, fetchVersions, fetchRecommendations, fetchPlan]);

  // Handle adding step from recommendation
  const handleAddStep = (step: TransformationStep) => {
    const updated = [...planSteps, step];
    setPlanSteps(updated);
    if (activeDataset) {
      apiClient.updateTransformationPlan(activeDataset.id, updated, activeVersionId).catch(console.error);
    }
  };

  // Handle plan update
  const handleUpdateSteps = (newSteps: TransformationStep[]) => {
    setPlanSteps(newSteps);
    if (activeDataset) {
      apiClient.updateTransformationPlan(activeDataset.id, newSteps, activeVersionId).catch(console.error);
    }
  };

  // Handle Preview
  const handlePreviewPlan = async () => {
    if (!activeDataset || planSteps.length === 0) return;
    setIsPreviewLoading(true);
    setError(null);
    try {
      const prev = await apiClient.previewTransformationPlan(
        activeDataset.id,
        planSteps,
        activeVersionId,
        10
      );
      setPreview(prev);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to generate plan preview.");
      }
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Handle Confirm Apply
  const handleConfirmApply = async (versionLabel: string) => {
    if (!activeDataset || planSteps.length === 0) return;
    setIsApplyLoading(true);
    setError(null);
    try {
      const res = await apiClient.applyTransformationPlan(
        activeDataset.id,
        planSteps,
        versionLabel,
        activeVersionId
      );

      // Open comparison modal
      setComparisonModalData({
        comparison: res.comparison,
        newVersion: res.new_version,
      });

      // Clear plan and refresh versions
      setPlanSteps([]);
      setPreview(null);
      setIsApplyDialogOpen(false);
      await fetchVersions(activeDataset.id);
      await fetchRecommendations(activeDataset.id, true);
      await refreshDatasets();

      setSuccessBanner(
        `Version ${res.new_version.version_id} created successfully! Quality score: ${res.comparison.after_score.toFixed(1)} (+${res.comparison.score_delta.toFixed(1)}%)`
      );
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to apply transformation plan.");
      }
    } finally {
      setIsApplyLoading(false);
    }
  };

  // Handle Version Switching
  const handleSelectVersion = async (versionId: string) => {
    if (!activeDataset || versionId === activeVersionId) return;
    setIsVersionLoading(true);
    try {
      await apiClient.activateDatasetVersion(activeDataset.id, versionId);
      setActiveVersionId(versionId);
      await fetchRecommendations(activeDataset.id, true);
      await fetchPlan(activeDataset.id);
      setPreview(null);
      setSuccessBanner(`Switched active dataset version to ${versionId}`);
    } catch (err) {
      setError(`Failed to activate version ${versionId}`);
    } finally {
      setIsVersionLoading(false);
    }
  };

  // Derive column list from preview or recommendations
  const availableColumns = Array.from(
    new Set([
      ...(preview?.columns_before || []),
      ...recommendations.flatMap((r) => r.suggested_step.input_columns || []),
    ])
  );

  // 1. Loading active dataset
  if (isDatasetLoading) {
    return (
      <div className="ax-stack">
        <PageHeader
          title="Clean & Transform"
          description="Build deterministic transformation pipelines, preview changes, and create versioned datasets."
        />
        <div
          style={{
            height: "300px",
            backgroundColor: "var(--bg-surface)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-tertiary)",
          }}
        >
          <div className="spin" style={{ width: "32px", height: "32px", border: "3px solid var(--border-subtle)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
        </div>
      </div>
    );
  }

  // 2. Empty state: No active dataset
  if (!activeDataset) {
    return (
      <div className="ax-stack">
        <PageHeader
          title="Clean & Transform"
          description="Build deterministic transformation pipelines, preview changes, and create versioned datasets."
        />
        <GuidedOnboarding
          title="Intelligent Data Cleaning Studio"
          description="Fix messy records, fill missing values, strip whitespace, and normalize text with one click. Safely preview transformation diffs and track changes across versions."
          badgeText="Data Cleaning"
          features={[
            "1-click automated cleaning recommendations & data deduplication",
            "Deterministic imputation (mean, median, mode, forward-fill, constant)",
            "Auditable version lineage with zero risk to original data",
          ]}
        />
      </div>
    );
  }

  return (
    <div className="ax-stack">
      {/* Header with Version Selector */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <PageHeader
          title="Clean & Transform"
          description={`Transforming ${activeDataset.name} • Non-destructive execution with immutable version lineage`}
        />

        {versions.length > 0 && (
          <DatasetVersionSelector
            versions={versions}
            activeVersionId={activeVersionId}
            onSelectVersion={handleSelectVersion}
            isLoading={isVersionLoading}
          />
        )}
      </div>

      {/* Success Banner */}
      {successBanner && (
        <div
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "8px",
            color: "#10b981",
            fontSize: "0.82rem",
            fontWeight: 500,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>{successBanner}</span>
          <button
            onClick={() => setSuccessBanner(null)}
            style={{
              background: "none",
              border: "none",
              color: "#10b981",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div
          style={{
            padding: "0.75rem 1rem",
            backgroundColor: "rgba(244, 63, 94, 0.12)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "8px",
            color: "#f43f5e",
            fontSize: "0.82rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <AlertCircleIcon size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Two-Column Studio Layout */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 1fr) minmax(380px, 1.4fr)",
          gap: "1.25rem",
          alignItems: "start",
        }}
      >
        {/* Left Column: Recommendations */}
        <div
          style={{
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            padding: "1.25rem",
            minHeight: "540px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <CleaningRecommendations
            recommendations={recommendations}
            planSteps={planSteps}
            onAddStep={handleAddStep}
            onRefresh={() => fetchRecommendations(activeDataset.id, true)}
            isLoading={isLoadingRecs}
          />
        </div>

        {/* Right Column: Pipeline Plan Builder */}
        <div
          style={{
            backgroundColor: "var(--bg-canvas)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "10px",
            padding: "1.25rem",
            minHeight: "540px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <TransformationPlanBuilder
            steps={planSteps}
            availableColumns={availableColumns}
            onUpdateSteps={handleUpdateSteps}
            onPreview={handlePreviewPlan}
            onApply={() => setIsApplyDialogOpen(true)}
            isPreviewLoading={isPreviewLoading}
            isApplyLoading={isApplyLoading}
          />
        </div>
      </div>

      {/* Full-width Interactive Before/After Preview Table */}
      <div style={{ marginTop: "0.5rem" }}>
        <h3
          style={{
            fontSize: "0.95rem",
            fontWeight: 600,
            color: "var(--text-primary)",
            marginBottom: "0.75rem",
          }}
        >
          Transformation Dry-Run & Sample Inspection
        </h3>
        <DataPreviewTable preview={preview} isLoading={isPreviewLoading} />
      </div>

      {/* Apply Confirmation Dialog */}
      <ApplyPlanDialog
        isOpen={isApplyDialogOpen}
        onClose={() => setIsApplyDialogOpen(false)}
        onConfirm={handleConfirmApply}
        steps={planSteps}
        isLoading={isApplyLoading}
      />

      {/* Post-Apply Before/After Scorecard Modal */}
      <BeforeAfterComparisonModal
        isOpen={!!comparisonModalData}
        onClose={() => setComparisonModalData(null)}
        comparison={comparisonModalData?.comparison || null}
        newVersion={comparisonModalData?.newVersion || null}
        datasetId={activeDataset.id}
      />
    </div>
  );
}

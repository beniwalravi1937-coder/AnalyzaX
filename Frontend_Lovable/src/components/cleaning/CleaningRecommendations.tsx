"use client";

import React, { useState } from "react";
import { CleaningRecommendation, TransformationStep } from "@/types";
import { WandIcon, CheckIcon, PlusIcon, AlertCircleIcon, RefreshIcon } from "@/components/icons";

interface CleaningRecommendationsProps {
  recommendations: CleaningRecommendation[];
  planSteps: TransformationStep[];
  onAddStep: (step: TransformationStep) => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

export function CleaningRecommendations({
  recommendations,
  planSteps,
  onAddStep,
  onRefresh,
  isLoading = false,
}: CleaningRecommendationsProps) {
  const [filterRisk, setFilterRisk] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const isStepInPlan = (suggestedStep: TransformationStep) => {
    return planSteps.some(
      (s) =>
        s.type === suggestedStep.type &&
        JSON.stringify(s.parameters) === JSON.stringify(suggestedStep.parameters)
    );
  };

  const filteredRecs = recommendations.filter((rec) => {
    if (filterRisk !== "ALL" && rec.risk !== filterRisk) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = rec.title.toLowerCase().includes(q);
      const matchDesc = rec.description.toLowerCase().includes(q);
      const matchReason = rec.reason.toLowerCase().includes(q);
      if (!matchTitle && !matchDesc && !matchReason) return false;
    }
    return true;
  });

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case "LOW":
        return {
          bg: "rgba(16, 185, 129, 0.12)",
          color: "#10b981",
          border: "rgba(16, 185, 129, 0.3)",
          label: "Low Risk",
        };
      case "MEDIUM":
        return {
          bg: "rgba(245, 158, 11, 0.12)",
          color: "#f59e0b",
          border: "rgba(245, 158, 11, 0.3)",
          label: "Medium Risk",
        };
      case "HIGH":
      default:
        return {
          bg: "rgba(244, 63, 94, 0.12)",
          color: "#f43f5e",
          border: "rgba(244, 63, 94, 0.3)",
          label: "High Risk",
        };
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        height: "100%",
      }}
    >
      {/* Header & Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "6px",
              backgroundColor: "rgba(99, 102, 241, 0.15)",
              color: "#6366f1",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <WandIcon size={16} />
          </div>
          <h3
            style={{
              fontSize: "0.95rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Quality Recommendations
          </h3>
          <span
            style={{
              fontSize: "0.75rem",
              padding: "2px 8px",
              borderRadius: "12px",
              backgroundColor: "var(--bg-surface-raised)",
              color: "var(--text-secondary)",
              fontWeight: 500,
            }}
          >
            {filteredRecs.length}
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            padding: "0.35rem 0.65rem",
            fontSize: "0.75rem",
            borderRadius: "6px",
            border: "1px solid var(--border-subtle)",
            backgroundColor: "var(--bg-surface)",
            color: "var(--text-secondary)",
            cursor: isLoading ? "not-allowed" : "pointer",
            transition: "all 0.15s ease",
          }}
          title="Re-evaluate dataset quality"
        >
          <RefreshIcon size={12} className={isLoading ? "spin" : ""} />
          {isLoading ? "Scanning..." : "Re-scan"}
        </button>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="Search actions..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            minWidth: "140px",
            padding: "0.35rem 0.65rem",
            fontSize: "0.78rem",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px",
            color: "var(--text-primary)",
            outline: "none",
          }}
        />

        <div style={{ display: "flex", gap: "0.25rem" }}>
          {["ALL", "LOW", "MEDIUM", "HIGH"].map((risk) => (
            <button
              key={risk}
              onClick={() => setFilterRisk(risk)}
              style={{
                padding: "0.25rem 0.5rem",
                fontSize: "0.7rem",
                fontWeight: 600,
                borderRadius: "4px",
                border: "1px solid",
                borderColor:
                  filterRisk === risk
                    ? "var(--accent-primary)"
                    : "var(--border-subtle)",
                backgroundColor:
                  filterRisk === risk
                    ? "rgba(99, 102, 241, 0.15)"
                    : "transparent",
                color:
                  filterRisk === risk
                    ? "var(--accent-primary)"
                    : "var(--text-tertiary)",
                cursor: "pointer",
              }}
            >
              {risk}
            </button>
          ))}
        </div>
      </div>

      {/* Recommendations Cards List */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
          overflowY: "auto",
          paddingRight: "4px",
          flex: 1,
        }}
      >
        {filteredRecs.length === 0 ? (
          <div
            style={{
              padding: "2rem 1rem",
              textAlign: "center",
              backgroundColor: "var(--bg-surface)",
              borderRadius: "8px",
              border: "1px dashed var(--border-subtle)",
              color: "var(--text-tertiary)",
              fontSize: "0.85rem",
            }}
          >
            <AlertCircleIcon size={24} style={{ marginBottom: "0.5rem", opacity: 0.6 }} />
            <p style={{ margin: 0, fontWeight: 500 }}>No matching recommendations found.</p>
            <p style={{ margin: "4px 0 0 0", fontSize: "0.75rem" }}>
              The dataset looks healthy or filter criteria returned no items.
            </p>
          </div>
        ) : (
          filteredRecs.map((rec) => {
            const inPlan = isStepInPlan(rec.suggested_step);
            const riskBadge = getRiskBadge(rec.risk);

            return (
              <div
                key={rec.recommendation_id}
                style={{
                  padding: "0.9rem",
                  backgroundColor: "var(--bg-surface)",
                  border: `1px solid ${inPlan ? "var(--border-strong)" : "var(--border-subtle)"}`,
                  borderRadius: "8px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                  transition: "border-color 0.15s ease, transform 0.1s ease",
                  position: "relative",
                }}
              >
                {/* Card Title & Risk */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    gap: "0.5rem",
                  }}
                >
                  <h4
                    style={{
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      margin: 0,
                      lineHeight: 1.3,
                    }}
                  >
                    {rec.title}
                  </h4>
                  <span
                    style={{
                      fontSize: "0.68rem",
                      fontWeight: 600,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      backgroundColor: riskBadge.bg,
                      color: riskBadge.color,
                      border: `1px solid ${riskBadge.border}`,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {riskBadge.label}
                  </span>
                </div>

                {/* Description */}
                <p
                  style={{
                    fontSize: "0.78rem",
                    color: "var(--text-secondary)",
                    margin: 0,
                    lineHeight: 1.4,
                  }}
                >
                  {rec.description}
                </p>

                {/* Technical Rationale */}
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: "var(--text-tertiary)",
                    backgroundColor: "var(--bg-canvas)",
                    padding: "0.4rem 0.6rem",
                    borderRadius: "4px",
                    border: "1px solid var(--border-subtle)",
                    lineHeight: 1.3,
                  }}
                >
                  <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Why: </span>
                  {rec.reason}
                </div>

                {/* Action button */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "0.25rem",
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.68rem",
                      color: "var(--text-tertiary)",
                    }}
                  >
                    Confidence: {(rec.confidence * 100).toFixed(0)}%
                  </span>

                  <button
                    onClick={() => !inPlan && onAddStep(rec.suggested_step)}
                    disabled={inPlan}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem",
                      padding: "0.35rem 0.75rem",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      borderRadius: "6px",
                      border: inPlan ? "1px solid rgba(16, 185, 129, 0.4)" : "none",
                      backgroundColor: inPlan
                        ? "rgba(16, 185, 129, 0.12)"
                        : "var(--accent-primary)",
                      color: inPlan ? "#10b981" : "#ffffff",
                      cursor: inPlan ? "default" : "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {inPlan ? (
                      <>
                        <CheckIcon size={12} />
                        In Plan
                      </>
                    ) : (
                      <>
                        <PlusIcon size={12} />
                        Add to Plan
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

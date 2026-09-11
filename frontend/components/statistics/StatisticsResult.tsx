"use client";

import React, { useState } from "react";
import { StatisticalResult } from "@/types/statistics";
import { StatisticsSummary } from "./StatisticsSummary";
import { AssumptionPanel } from "./AssumptionPanel";
import { ConfidenceIntervalCard } from "./ConfidenceIntervalCard";
import { EffectSizeCard } from "./EffectSizeCard";
import { StatisticalFinding } from "./StatisticalFinding";
import { RegressionSummary } from "./RegressionSummary";
import { CorrelationMatrix } from "./CorrelationMatrix";
import { DistributionPanel } from "./DistributionPanel";
import { GroupComparisonPanel } from "./GroupComparisonPanel";
import { CategoricalAnalysisPanel } from "./CategoricalAnalysisPanel";
import { StatisticsInspector } from "./StatisticsInspector";
import { ChartRenderer } from "@/components/visualization/ChartRenderer";

interface StatisticsResultProps {
  result: StatisticalResult;
}

export const StatisticsResultView: React.FC<StatisticsResultProps> = ({ result }) => {
  const [activeTab, setActiveTab] = useState<"summary" | "assumptions" | "visualizations" | "details">("summary");
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Executive Summary Card */}
      <StatisticsSummary result={result} onOpenInspector={() => setIsInspectorOpen(true)} />

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "0.5rem",
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab("summary")}
          className={`btn btn-sm ${activeTab === "summary" ? "btn-primary" : "btn-secondary"}`}
        >
          Key Findings & Evidence
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("assumptions")}
          className={`btn btn-sm ${activeTab === "assumptions" ? "btn-primary" : "btn-secondary"}`}
        >
          Assumptions ({result.assumptions?.length || 0})
        </button>
        {result.chart_specs && result.chart_specs.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab("visualizations")}
            className={`btn btn-sm ${activeTab === "visualizations" ? "btn-primary" : "btn-secondary"}`}
          >
            Visualizations ({result.chart_specs.length})
          </button>
        )}
        <button
          type="button"
          onClick={() => setActiveTab("details")}
          className={`btn btn-sm ${activeTab === "details" ? "btn-primary" : "btn-secondary"}`}
        >
          Detailed Method Output
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "summary" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Effect Sizes & Confidence Intervals */}
          {(result.effect_sizes?.length > 0 || result.confidence_intervals?.length > 0) && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
              {result.effect_sizes?.map((eff, i) => (
                <EffectSizeCard key={i} effect={eff} />
              ))}
              {result.confidence_intervals?.map((ci, i) => (
                <ConfidenceIntervalCard key={i} ci={ci} />
              ))}
            </div>
          )}

          {/* Ranked Findings */}
          <div>
            <h4 style={{ margin: "0 0 0.75rem 0", fontSize: "0.9375rem", fontWeight: 600 }}>
              Statistical Findings ({result.findings?.length || 0})
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {result.findings?.map((finding) => (
                <StatisticalFinding key={finding.finding_id} finding={finding} />
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "assumptions" && (
        <AssumptionPanel assumptions={result.assumptions || []} />
      )}

      {activeTab === "visualizations" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "1.5rem" }}>
          {result.chart_specs?.map((spec, i) => (
            <div
              key={spec.chart_id || i}
              style={{
                padding: "1rem",
                borderRadius: "8px",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "0.9375rem" }}>{spec.title}</h4>
              <ChartRenderer spec={spec as any} height={320} />
            </div>
          ))}
        </div>
      )}

      {activeTab === "details" && (
        <div>
          {result.method === "ols_regression" && (
            <RegressionSummary statistics={result.statistics} />
          )}
          {["correlation_matrix", "pearson", "spearman", "kendall"].includes(result.method) && result.statistics?.matrix && (
            <CorrelationMatrix statistics={result.statistics} />
          )}
          {result.method === "distribution_analysis" && (
            <DistributionPanel statistics={result.statistics} />
          )}
          {["t_test_welch", "t_test_ind", "mann_whitney_u", "anova_oneway", "kruskal_wallis"].includes(result.method) && (
            <GroupComparisonPanel statistics={result.statistics} />
          )}
          {["chi_square", "fisher_exact"].includes(result.method) && (
            <CategoricalAnalysisPanel statistics={result.statistics} />
          )}
          {result.method === "descriptive_summary" && (
            <pre
              style={{
                padding: "1rem",
                borderRadius: "8px",
                background: "var(--bg-subtle)",
                border: "1px solid var(--border-subtle)",
                overflowX: "auto",
                fontSize: "0.75rem",
              }}
            >
              {JSON.stringify(result.statistics, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Provenance Inspector Drawer */}
      <StatisticsInspector
        result={result}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />
    </div>
  );
};

"use client";

import React, { useState, useEffect } from "react";
import {
  ExportFormat,
  ReportTemplate,
  ReportTemplateMeta,
  FORMAT_LABELS,
  REPORT_FORMATS,
  ExportJob,
} from "@/types/exports";
import {
  generateReport,
  listReportTemplates,
  downloadExport,
} from "@/services/exportApi";
import {
  BarChart3,
  ShieldCheck,
  Microscope,
  Cpu,
  TrendingDown,
  FileText,
  Edit3,
  type LucideIcon,
} from "lucide-react";

interface ReportBuilderPanelProps {
  datasetId: string;
  versionId?: string;
}

const TEMPLATE_ICONS: Record<string, LucideIcon> = {
  EXECUTIVE_SUMMARY: BarChart3,
  DATA_QUALITY: ShieldCheck,
  EDA_DEEP_DIVE: Microscope,
  ML_EXPERIMENT: Cpu,
  FORECAST_BRIEF: TrendingDown,
  FULL_ANALYSIS: FileText,
  CUSTOM: Edit3,
};

export function ReportBuilderPanel({ datasetId, versionId }: ReportBuilderPanelProps) {
  const [templates, setTemplates] = useState<ReportTemplateMeta[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate>("EXECUTIVE_SUMMARY");
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("HTML_REPORT");
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<ExportJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await listReportTemplates();
      setTemplates(data);
    } catch {
      // Templates are optional — show default set on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const job = await generateReport({
        dataset_id: datasetId,
        version_id: versionId,
        template: selectedTemplate,
        title: title || undefined,
        subtitle: subtitle || undefined,
        format: selectedFormat,
      });

      setResult(job);

      if (job.status === "COMPLETED") {
        await downloadExport(job.job_id);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Report generation failed";
      setError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedMeta = templates.find((t) => t.template === selectedTemplate);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Template Selector */}
      <div>
        <label
          style={{
            display: "block",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            marginBottom: "0.5rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Report Template
        </label>
        {isLoading ? (
          <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Loading templates...
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: "0.625rem",
            }}
          >
            {templates.map((tmpl) => (
              <button
                key={tmpl.template}
                type="button"
                onClick={() => setSelectedTemplate(tmpl.template as ReportTemplate)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.25rem",
                  padding: "0.875rem",
                  borderRadius: "8px",
                  border: `1px solid ${
                    selectedTemplate === tmpl.template
                      ? "var(--primary)"
                      : "var(--border-subtle)"
                  }`,
                  background:
                    selectedTemplate === tmpl.template
                      ? "rgba(99, 102, 241, 0.08)"
                      : "var(--bg-secondary)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  {(() => {
                    const TIcon = TEMPLATE_ICONS[tmpl.template] || FileText;
                    return <TIcon className="w-4 h-4 text-indigo-400 shrink-0" />;
                  })()}
                  <span
                    style={{
                      fontWeight: 600,
                      fontSize: "0.8125rem",
                      color:
                        selectedTemplate === tmpl.template
                          ? "var(--primary)"
                          : "var(--text-primary)",
                    }}
                  >
                    {tmpl.name}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-muted)",
                    lineHeight: 1.4,
                  }}
                >
                  {tmpl.description}
                </span>
                <span
                  style={{
                    fontSize: "0.625rem",
                    color: "var(--text-muted)",
                    marginTop: "0.25rem",
                  }}
                >
                  {tmpl.section_count} section{tmpl.section_count !== 1 ? "s" : ""}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Title & Subtitle Customization */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div>
          <label
            style={{
              display: "block",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "var(--text-muted)",
              marginBottom: "0.375rem",
            }}
          >
            Custom Title (optional)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={selectedMeta?.name || "Report Title"}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: "6px",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
            }}
          />
        </div>
        <div>
          <label
            style={{
              display: "block",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "var(--text-muted)",
              marginBottom: "0.375rem",
            }}
          >
            Subtitle (optional)
          </label>
          <input
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            placeholder="Report subtitle..."
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: "6px",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
            }}
          />
        </div>
      </div>

      {/* Format Selector */}
      <div>
        <label
          style={{
            display: "block",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--text-muted)",
            marginBottom: "0.5rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Output Format
        </label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {REPORT_FORMATS.map((fmt) => (
            <button
              key={fmt}
              type="button"
              onClick={() => setSelectedFormat(fmt)}
              className={`btn btn-sm ${
                selectedFormat === fmt ? "btn-primary" : "btn-secondary"
              }`}
              style={{ minWidth: "120px" }}
            >
              {FORMAT_LABELS[fmt]}
            </button>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={isGenerating}
          style={{ minWidth: "160px" }}
        >
          {isGenerating ? (
            <span style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span
                style={{
                  width: "14px",
                  height: "14px",
                  border: "2px solid rgba(255,255,255,0.3)",
                  borderTopColor: "white",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              Generating...
            </span>
          ) : (
            <>📄 Generate Report</>
          )}
        </button>

        {result && result.status === "COMPLETED" && (
          <span
            style={{
              fontSize: "0.8125rem",
              color: "var(--success)",
              display: "flex",
              alignItems: "center",
              gap: "0.375rem",
            }}
          >
            ✓ Report generated ({((result.file_size_bytes || 0) / 1024).toFixed(1)} KB)
          </span>
        )}

        {result && result.status === "FAILED" && (
          <span style={{ fontSize: "0.8125rem", color: "var(--danger)" }}>
            ✕ {result.error_message || "Report generation failed"}
          </span>
        )}

        {error && (
          <span style={{ fontSize: "0.8125rem", color: "var(--danger)" }}>
            ✕ {error}
          </span>
        )}
      </div>

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

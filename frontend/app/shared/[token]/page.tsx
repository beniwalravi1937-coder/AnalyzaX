"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { collaborationApi } from "@/services/collaborationApi";
import { SharedResourceView } from "@/types/collaboration";
import { Shield, Download, AlertTriangle, FileText, LayoutDashboard, Database } from "lucide-react";

export default function SharedResourcePage() {
  const params = useParams();
  const token = params?.token as string;

  const [resource, setResource] = useState<SharedResourceView | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSharedView = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await collaborationApi.getSharedResource(token);
      setResource(data);
    } catch (err: any) {
      setError(err.message || "This shared link is invalid, revoked, or has expired.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSharedView();
  }, [fetchSharedView]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Restricted Minimal Header */}
      <header className="border-b border-border bg-surface px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-black text-sm tracking-tight text-foreground">
            <span className="text-brand">AnalyzaX</span>
            <span className="text-foreground-muted font-normal">| Shared View</span>
          </div>
          {resource && (
            <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-brand/10 text-brand uppercase">
              {resource.resource_type}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {resource?.can_export && (
            <button
              onClick={() => alert("Export initiated based on share policy.")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-border text-foreground text-xs font-semibold transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export</span>
            </button>
          )}
          <span className="text-xs text-foreground-muted flex items-center gap-1">
            <Shield className="w-3.5 h-3.5 text-success" />
            <span>Secure Share</span>
          </span>
        </div>
      </header>

      {/* Main Presentation Container */}
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-6">
        {isLoading ? (
          <div className="py-24 text-center text-xs text-foreground-muted animate-pulse">
            Resolving restricted shared resource...
          </div>
        ) : error ? (
          <div className="py-24 text-center max-w-md mx-auto space-y-4">
            <div className="p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs font-medium">
              {error}
            </div>
            <p className="text-xs text-foreground-muted">
              Please contact the resource owner to request an active invitation or fresh link.
            </p>
          </div>
        ) : resource ? (
          <div className="space-y-6">
            {/* Title & Metadata Banner */}
            <div className="bg-surface-elevated border border-border rounded-xl p-6 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-black tracking-tight text-foreground">
                    {resource.title}
                  </h1>
                  <p className="text-xs text-foreground-muted mt-1">
                    Shared under {resource.permission} policy • Restricted Presentation Mode
                  </p>
                </div>
              </div>

              {/* Masked Dependency Warning */}
              {resource.masked_dependencies && resource.masked_dependencies.length > 0 && (
                <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-500 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>
                    Some underlying content is restricted or unavailable due to privacy policies.
                  </span>
                </div>
              )}
            </div>

            {/* Render Content Based on Resource Type */}
            <div className="bg-surface-elevated border border-border rounded-xl p-6 shadow-sm min-h-[350px]">
              {resource.resource_type === "DASHBOARD" ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-foreground-muted uppercase tracking-wider">
                    <LayoutDashboard className="w-4 h-4 text-brand" />
                    <span>Dashboard Layout</span>
                  </div>
                  {resource.content?.components ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      {resource.content.components.map((comp: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl border border-border bg-surface flex flex-col justify-between h-48"
                        >
                          <div className="font-bold text-sm text-foreground">{comp.title || `Chart ${idx + 1}`}</div>
                          <div className="text-xs text-foreground-muted">{comp.type || "Visualization"}</div>
                          <div className="text-[11px] text-foreground-muted/80 bg-surface-muted p-2 rounded">
                            Interactive widget preview rendered within share boundary.
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-xs text-foreground-muted">
                      Shared dashboard components are ready for viewing.
                    </div>
                  )}
                </div>
              ) : resource.resource_type === "REPORT" ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-foreground-muted uppercase tracking-wider">
                    <FileText className="w-4 h-4 text-brand" />
                    <span>Report Document</span>
                  </div>
                  <div className="prose prose-invert max-w-none text-xs leading-relaxed text-foreground-muted">
                    {resource.content?.summary || "Analytical report content rendered safely without leaking private upstream dataset metadata."}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-foreground-muted uppercase tracking-wider">
                    <Database className="w-4 h-4 text-brand" />
                    <span>Asset Data Preview</span>
                  </div>
                  <pre className="p-4 rounded-lg bg-surface border border-border text-[11px] font-mono text-foreground-muted overflow-x-auto">
                    {JSON.stringify(resource.content, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "./sheet";
import { Button } from "./button";
import { Terminal, Copy, Check, Info, ShieldCheck, Database, Cpu } from "lucide-react";

export interface AnalysisDetailsProps {
  title?: string;
  trigger?: React.ReactNode;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  datasetId?: string;
  datasetName?: string;
  versionId?: string;
  executionId?: string;
  jobId?: string;
  queryId?: string;
  modelName?: string;
  provider?: string;
  executionTimeMs?: number;
  engine?: string;
  additionalDetails?: Record<string, any>;
}

export function AnalysisDetailsDrawer({
  title = "Analysis Details & Execution Provenance",
  trigger,
  isOpen,
  onOpenChange,
  datasetId,
  datasetName,
  versionId,
  executionId,
  jobId,
  queryId,
  modelName,
  provider,
  executionTimeMs,
  engine = "DuckDB / FastAPI Analytical Engine",
  additionalDetails,
}: AnalysisDetailsProps) {
  const [copied, setCopied] = useState(false);

  const payload = {
    dataset: {
      name: datasetName,
      id: datasetId,
      version: versionId,
    },
    execution: {
      execution_id: executionId,
      job_id: jobId,
      query_id: queryId,
      execution_time_ms: executionTimeMs,
      engine,
    },
    intelligence: {
      model: modelName,
      provider,
    },
    custom: additionalDetails,
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      {trigger && <SheetTrigger asChild>{trigger}</SheetTrigger>}

      <SheetContent className="w-full sm:max-w-lg bg-slate-950 border-white/10 text-white flex flex-col p-0 overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-white/10 space-y-2 bg-slate-900/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-indigo-400">
              <Terminal className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Audit & Diagnostics
              </span>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="h-7 text-xs gap-1.5 border-white/10 bg-slate-900 hover:bg-slate-800 text-slate-300"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy JSON"}</span>
            </Button>
          </div>

          <SheetTitle className="text-lg font-bold text-white tracking-tight">
            {title}
          </SheetTitle>
          <SheetDescription className="text-xs text-slate-400">
            Technical execution metadata, engine parameters, and verifiable lineage isolated from the presentation layer.
          </SheetDescription>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto">
          {/* Dataset Provenance */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>Dataset Provenance</span>
            </div>

            <div className="rounded-lg border border-white/10 bg-slate-900/50 p-3.5 space-y-2 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-white/5">
                <span className="text-slate-400">Dataset Name</span>
                <span className="font-semibold text-slate-200">{datasetName || "Unspecified"}</span>
              </div>
              {datasetId && (
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Internal Dataset ID</span>
                  <code className="font-mono text-[11px] text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {datasetId}
                  </code>
                </div>
              )}
              {versionId && (
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">Version Hash</span>
                  <code className="font-mono text-[11px] text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {versionId}
                  </code>
                </div>
              )}
            </div>
          </div>

          {/* Engine & Compute */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Engine & Execution</span>
            </div>

            <div className="rounded-lg border border-white/10 bg-slate-900/50 p-3.5 space-y-2 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-white/5">
                <span className="text-slate-400">Execution Engine</span>
                <span className="font-medium text-slate-200">{engine}</span>
              </div>
              {executionTimeMs !== undefined && (
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Duration</span>
                  <span className="font-mono text-emerald-400 font-medium">{executionTimeMs} ms</span>
                </div>
              )}
              {executionId && (
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Execution ID</span>
                  <code className="font-mono text-[11px] text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {executionId}
                  </code>
                </div>
              )}
              {jobId && (
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Job ID</span>
                  <code className="font-mono text-[11px] text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {jobId}
                  </code>
                </div>
              )}
              {queryId && (
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">Query ID</span>
                  <code className="font-mono text-[11px] text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-white/5">
                    {queryId}
                  </code>
                </div>
              )}
            </div>
          </div>

          {/* Model & AI Details */}
          {(modelName || provider) && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span>AI Configuration</span>
              </div>

              <div className="rounded-lg border border-white/10 bg-slate-900/50 p-3.5 space-y-2 text-xs">
                {modelName && (
                  <div className="flex justify-between items-center py-1 border-b border-white/5">
                    <span className="text-slate-400">Model</span>
                    <span className="font-mono text-slate-200 font-medium">{modelName}</span>
                  </div>
                )}
                {provider && (
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-400">Provider</span>
                    <span className="font-medium text-slate-200">{provider}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Additional details JSON */}
          {additionalDetails && Object.keys(additionalDetails).length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Raw Context Payload
              </span>
              <pre className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] font-mono text-slate-400 overflow-x-auto">
                {JSON.stringify(additionalDetails, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 bg-slate-900/40 text-[11px] text-slate-500 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-400" />
            <span>Verifiable audit trail generated by AnalyzaX</span>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default AnalysisDetailsDrawer;

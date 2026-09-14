"use client";

import React, { useState } from "react";
import { CleaningProposal } from "@/types/ai_analyst";
import { confirmCleaningProposal } from "@/services/aiAnalystApi";

interface CleaningConfirmationCardProps {
  proposal: CleaningProposal;
  sessionId: string;
  onApplied?: (newVersionId: string) => void;
}

export function CleaningConfirmationCard({
  proposal,
  sessionId,
  onApplied,
}: CleaningConfirmationCardProps) {
  const [isApplying, setIsApplying] = useState(false);
  const [appliedVersion, setAppliedVersion] = useState<string | null>(
    proposal.status === "applied" ? "Applied" : null
  );
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setIsApplying(true);
    setError(null);
    try {
      const res = await confirmCleaningProposal(sessionId, proposal.proposal_id);
      setAppliedVersion(res.new_version_id || "v2");
      if (onApplied && res.new_version_id) {
        onApplied(res.new_version_id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to execute cleaning proposal.");
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div
      style={{
        marginTop: "1rem",
        marginBottom: "1rem",
        padding: "1rem",
        background: "rgba(245, 158, 11, 0.05)",
        border: "1px solid rgba(245, 158, 11, 0.3)",
        borderRadius: "0.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "1.2rem" }}>🛡️</span>
        <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "var(--amber-600, #d97706)" }}>
          Human-in-the-Loop Confirmation Required
        </h4>
      </div>

      <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
        <strong>Action:</strong> <code>{proposal.operation_type}</code>
      </p>
      <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
        <strong>Rationale:</strong> {proposal.rationale}
      </p>
      <p style={{ margin: "0.25rem 0 0.75rem 0", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
        <strong>Impact:</strong> {proposal.impact_summary}
      </p>

      {appliedVersion ? (
        <div
          style={{
            padding: "0.5rem 0.75rem",
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "0.375rem",
            fontSize: "0.85rem",
            color: "var(--emerald-600, #059669)",
            fontWeight: 500,
          }}
        >
          ✓ Successfully created new immutable version: <strong>{appliedVersion}</strong>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button
            onClick={handleConfirm}
            disabled={isApplying}
            style={{
              padding: "0.4rem 0.9rem",
              background: "var(--accent-primary, #4f46e5)",
              color: "#fff",
              border: "none",
              borderRadius: "0.375rem",
              fontSize: "0.85rem",
              fontWeight: 500,
              cursor: isApplying ? "not-allowed" : "pointer",
              opacity: isApplying ? 0.7 : 1,
            }}
          >
            {isApplying ? "Creating New Version..." : "Confirm & Apply"}
          </button>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Original data will remain immutable.
          </span>
        </div>
      )}

      {error && (
        <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", color: "var(--red-600, #dc2626)" }}>
          {error}
        </div>
      )}
    </div>
  );
}

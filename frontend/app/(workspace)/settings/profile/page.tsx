"use client";

import React, { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { SettingsNav } from "@/components/settings/SettingsNav";
import { useAuth } from "@/context/AuthContext";
import { authApi } from "@/services/authApi";

export default function ProfileSettingsPage() {
  const { user, workspaceMemberships, refreshUser } = useAuth();
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setIsSaving(true);

    try {
      await authApi.updateProfile(displayName);
      await refreshUser();
      setSuccessMessage("Profile updated successfully");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Settings — User Profile"
        description="Manage your account identity, display name, and active workspace memberships."
      />

      <SettingsNav />

      {successMessage && (
        <div className="alert alert-success" style={{ marginBottom: "1.25rem" }}>
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger" style={{ marginBottom: "1.25rem" }}>
          {errorMessage}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Personal Details */}
        <SectionCard
          title="Personal Information"
          subtitle="Your primary account details across AnalyzaX workspaces"
        >
          <form onSubmit={handleSaveProfile} style={{ maxWidth: "520px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Account User ID
                </label>
                <input
                  type="text"
                  readOnly
                  value={user?.user_id || ""}
                  className="analyzax-input"
                  style={{ opacity: 0.7, cursor: "not-allowed", fontFamily: "var(--font-mono)" }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Email Address
                </label>
                <input
                  type="email"
                  readOnly
                  value={user?.email || ""}
                  className="analyzax-input"
                  style={{ opacity: 0.7, cursor: "not-allowed" }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Display Name
                </label>
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="analyzax-input"
                  placeholder="Your Name"
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Account Status
                </label>
                <div>
                  <span className="badge badge-emerald" style={{ textTransform: "uppercase" }}>
                    {user?.status || "ACTIVE"}
                  </span>
                </div>
              </div>

              <div style={{ marginTop: "0.5rem" }}>
                <button type="submit" disabled={isSaving} className="btn btn-primary btn-sm">
                  {isSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          </form>
        </SectionCard>

        {/* Workspace Memberships */}
        <SectionCard
          title="Workspace Memberships"
          subtitle="Organizations and workspaces you currently have access to"
        >
          <div className="table-wrapper">
            <table className="analyzax-table">
              <thead>
                <tr>
                  <th>Workspace</th>
                  <th>Workspace ID</th>
                  <th>Assigned Role</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {workspaceMemberships.map((m) => (
                  <tr key={m.workspace_id}>
                    <td style={{ fontWeight: 600 }}>{m.workspace_name}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {m.workspace_id}
                    </td>
                    <td>
                      <span className="badge badge-indigo">{m.role}</span>
                    </td>
                    <td>
                      <span className="badge badge-emerald">{m.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

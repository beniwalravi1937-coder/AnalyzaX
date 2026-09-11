"use client";

import React, { useState, useEffect, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { SettingsNav } from "@/components/settings/SettingsNav";
import { authApi } from "@/services/authApi";
import { SafeSession } from "@/types/auth";

export default function SecuritySettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isChanging, setIsChanging] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [sessions, setSessions] = useState<SafeSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);

  const loadSessions = useCallback(async () => {
    try {
      setIsLoadingSessions(true);
      const data = await authApi.getSessions();
      setSessions(data);
    } catch {
      // ignore
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);

    if (newPassword.length < 8) {
      setPasswordMsg({ type: "error", text: "New password must be at least 8 characters long." });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: "error", text: "New passwords do not match." });
      return;
    }

    setIsChanging(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setPasswordMsg({ type: "success", text: "Password updated successfully. Other sessions have been revoked." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      await loadSessions();
    } catch (err: any) {
      setPasswordMsg({ type: "error", text: err.message || "Failed to update password." });
    } finally {
      setIsChanging(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await authApi.revokeSession(sessionId);
      await loadSessions();
    } catch (err: any) {
      alert(err.message || "Failed to revoke session");
    }
  };

  return (
    <div>
      <PageHeader
        title="Settings — Security & Sessions"
        description="Update your credentials, monitor active browser sessions, and manage device access."
      />

      <SettingsNav />

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Password Change */}
        <SectionCard
          title="Change Password"
          subtitle="Ensure your account is using a long, randomized password to protect analytical assets"
        >
          {passwordMsg && (
            <div
              className={`alert ${passwordMsg.type === "success" ? "alert-success" : "alert-danger"}`}
              style={{ marginBottom: "1rem" }}
            >
              {passwordMsg.text}
            </div>
          )}

          <form onSubmit={handleChangePassword} style={{ maxWidth: "480px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Current Password
                </label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="analyzax-input"
                  placeholder="••••••••••••"
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  New Password (min. 8 characters)
                </label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="analyzax-input"
                  placeholder="••••••••••••"
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="analyzax-input"
                  placeholder="••••••••••••"
                />
              </div>

              <div style={{ marginTop: "0.5rem" }}>
                <button type="submit" disabled={isChanging} className="btn btn-primary btn-sm">
                  {isChanging ? "Updating Password..." : "Update Password"}
                </button>
              </div>
            </div>
          </form>
        </SectionCard>

        {/* Active Sessions */}
        <SectionCard
          title="Active Sessions"
          subtitle="Devices and browsers that currently hold authenticated access to your account"
        >
          {isLoadingSessions ? (
            <div style={{ color: "var(--text-muted)", fontSize: "0.875rem", padding: "1rem 0" }}>
              Loading active sessions...
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="analyzax-table">
                <thead>
                  <tr>
                    <th>Session ID</th>
                    <th>Device / User Agent</th>
                    <th>IP Address</th>
                    <th>Last Active</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.session_id}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                            {s.session_id.slice(0, 12)}...
                          </span>
                          {s.is_current && <span className="badge badge-emerald">CURRENT</span>}
                        </div>
                      </td>
                      <td style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                        {s.user_agent || "Web Browser"}
                      </td>
                      <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {s.ip_address || "Localhost"}
                      </td>
                      <td style={{ fontSize: "0.8125rem" }}>
                        {new Date(s.last_seen_at).toLocaleString()}
                      </td>
                      <td>
                        {!s.is_current ? (
                          <button
                            type="button"
                            onClick={() => handleRevokeSession(s.session_id)}
                            className="btn btn-secondary btn-sm"
                            style={{ color: "#ef4444" }}
                          >
                            Revoke
                          </button>
                        ) : (
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Active Now</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

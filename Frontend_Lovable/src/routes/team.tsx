import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Copy, Mail, UserPlus, Trash2, RefreshCw } from "lucide-react";
import { PageHeader } from "../components/ax/ui";
import { collaborationApi } from "../services/collaborationApi";
import { useWorkspace } from "../context/WorkspaceContext";
import { useAuth } from "../context/AuthContext";
import { InvitationResponse } from "../types/collaboration";

export const Route = createFileRoute("/team")({
  head: () => ({
    meta: [
      { title: "Team Members & Permissions — AnalyzaX" },
      {
        name: "description",
        content:
          "Invite team members, share project links, and manage who can view, edit, or export analytical dashboards in your workspace.",
      },
      { property: "og:title", content: "Team Members & Permissions — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Invite team members, share project links, and manage workspace roles and permissions.",
      },
    ],
  }),
  component: TeamPage,
});

const ROLES = ["ANALYST", "VIEWER", "ADMIN", "EDITOR"];

function TeamPage() {
  const { user } = useAuth();
  const { activeWorkspace } = useWorkspace();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("ANALYST");
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const fetchInvitations = async () => {
    if (!activeWorkspace?.workspace_id) return;
    try {
      setIsLoading(true);
      const data = await collaborationApi.listInvitations(activeWorkspace.workspace_id);
      setInvitations(data);
    } catch (err: any) {
      console.error("Failed to load invitations:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, [activeWorkspace?.workspace_id]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace?.workspace_id || !email.trim()) return;
    setIsCreating(true);
    setError(null);
    try {
      await collaborationApi.createInvitation(activeWorkspace.workspace_id, {
        email: email.trim().toLowerCase(),
        role: role as any,
      });
      setEmail("");
      await fetchInvitations();
    } catch (err: any) {
      setError(err.message || "Could not send the invitation.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevoke = async (invitationId: string) => {
    try {
      await collaborationApi.revokeInvitation(invitationId);
      await fetchInvitations();
    } catch (err: any) {
      alert(err.message || "Failed to revoke invitation.");
    }
  };

  const copyLink = (token: string) => {
    const url = `${window.location.origin}/invite/${token}`;
    void navigator.clipboard.writeText(url);
    setCopied(token);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Workspace"
        title="Team & Collaborators"
        description="Invite teammates, assign analytical permissions, and share access to your active workspace."
      />

      <div className="card" style={{ marginBottom: "1rem" }}>
        <div className="card-header">
          <div>
            <div className="card-title">
              <UserPlus className="w-4 h-4" /> Invite a Teammate
            </div>
            <div className="card-subtitle">
              Invitations generate a secure link with designated workspace permissions.
            </div>
          </div>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <span>{error}</span>
          </div>
        )}

        <form className="filter-row" onSubmit={handleCreate}>
          <div className="field" style={{ minWidth: "16rem", flex: 1 }}>
            <label htmlFor="inviteEmail">Email address</label>
            <input
              id="inviteEmail"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teammate@company.com"
            />
          </div>
          <div className="field">
            <label htmlFor="inviteRole">Role</label>
            <select id="inviteRole" value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary" disabled={isCreating || !email.trim()}>
            {isCreating ? "Creating…" : "Send invitation"}
          </button>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <Mail className="w-4 h-4" /> Pending & Active Invitations
            </div>
            <div className="card-subtitle">Share the invitation token link with your teammate.</div>
          </div>
          <button onClick={fetchInvitations} className="btn btn-secondary btn-sm" title="Refresh">
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {isLoading && invitations.length === 0 && <p className="stat-subtext">Loading invitations…</p>}
        {!isLoading && invitations.length === 0 && <p className="stat-subtext">No invitations found for this workspace.</p>}

        {invitations.length > 0 && (
          <div className="table-wrapper">
            <table className="analyzax-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Expires</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((inv) => {
                  const status = (inv.status || "PENDING").toLowerCase();
                  return (
                    <tr key={inv.invitation_id}>
                      <td style={{ fontWeight: 600 }}>{inv.email}</td>
                      <td>
                        <span className="badge badge-neutral">{inv.role}</span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            status === "accepted"
                              ? "badge-cyan"
                              : status === "pending"
                              ? "badge-emerald"
                              : "badge-rose"
                          }`}
                        >
                          {status}
                        </span>
                      </td>
                      <td className="mono text-xs">
                        {inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : "—"}
                      </td>
                      <td style={{ display: "flex", gap: "0.35rem", justifyContent: "flex-end" }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => copyLink(inv.token)}>
                          <Copy className="w-3.5 h-3.5" />
                          {copied === inv.token ? "Copied!" : "Copy Link"}
                        </button>
                        {status === "pending" && (
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleRevoke(inv.invitation_id)}
                            title="Revoke Invitation"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

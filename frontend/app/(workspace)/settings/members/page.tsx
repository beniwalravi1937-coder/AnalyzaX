"use client";

import React, { useState, useEffect, useCallback } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { SettingsNav } from "@/components/settings/SettingsNav";
import { useAuth } from "@/context/AuthContext";
import { useWorkspace } from "@/context/WorkspaceContext";
import { authApi } from "@/services/authApi";
import { collaborationApi } from "@/services/collaborationApi";
import { RoleName, SecurityAuditEvent, WorkspaceMemberDetail } from "@/types/auth";
import { InvitationResponse } from "@/types/collaboration";
import { Users, Mail, Shield, Activity, RefreshCw, Copy, Check, UserPlus } from "lucide-react";

export default function MembersSettingsPage() {
  const { user, hasPermission } = useAuth();
  const { activeWorkspace } = useWorkspace();

  const [activeTab, setActiveTab] = useState<"members" | "invitations" | "roles" | "activity">("members");

  const [members, setMembers] = useState<WorkspaceMemberDetail[]>([]);
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [auditLogs, setAuditLogs] = useState<SecurityAuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Search & filter
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("ALL");

  // Invite modal/form
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<string>("ANALYST");
  const [inviteExpiresDays, setInviteExpiresDays] = useState<number>(7);
  const [isInviting, setIsInviting] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const canManage = hasPermission("workspace.manage_members");
  const canViewAudit = hasPermission("audit.read");

  const loadData = useCallback(async () => {
    if (!activeWorkspace?.workspace_id) return;
    setIsLoading(true);
    try {
      // 1. Members
      const memberList = await authApi.getMembers(activeWorkspace.workspace_id);
      setMembers(memberList);

      // 2. Invitations
      try {
        const invs = await collaborationApi.listInvitations(activeWorkspace.workspace_id);
        setInvitations(invs);
      } catch {
        // ignore if not authorized
      }

      // 3. Audit logs
      if (canViewAudit) {
        try {
          const logs = await authApi.getAuditLogs(activeWorkspace.workspace_id, 30);
          setAuditLogs(logs);
        } catch {
          // ignore
        }
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  }, [activeWorkspace?.workspace_id, canViewAudit]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace) return;
    setMessage(null);
    setIsInviting(true);

    try {
      const res = await collaborationApi.createInvitation(activeWorkspace.workspace_id, {
        email: inviteEmail,
        intended_role: inviteRole,
        expires_in_days: inviteExpiresDays,
      });
      setMessage({
        type: "success",
        text: `Invitation created for ${inviteEmail} (${inviteRole}). Token preview generated.`,
      });
      setInviteEmail("");
      await loadData();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to create invitation." });
    } finally {
      setIsInviting(false);
    }
  };

  const handleRevokeInvitation = async (invitationId: string) => {
    if (!confirm("Are you sure you want to revoke this pending invitation?")) return;
    try {
      await collaborationApi.revokeInvitation(invitationId);
      setMessage({ type: "success", text: "Invitation revoked successfully." });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to revoke invitation");
    }
  };

  const handleResendInvitation = async (invitationId: string) => {
    try {
      await collaborationApi.resendInvitation(invitationId);
      setMessage({ type: "success", text: "Invitation refreshed with fresh single-use token." });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to resend invitation");
    }
  };

  const handleRoleChange = async (memberUserId: string, role: RoleName) => {
    if (!activeWorkspace) return;
    try {
      await authApi.updateMemberRole(activeWorkspace.workspace_id, memberUserId, role);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to change member role");
    }
  };

  const handleRemoveMember = async (memberUserId: string, memberEmail: string) => {
    if (!activeWorkspace) return;
    if (!confirm(`Are you sure you want to remove ${memberEmail} from this workspace?`)) return;

    try {
      await authApi.removeMember(activeWorkspace.workspace_id, memberUserId);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to remove member");
    }
  };

  const copyInviteLink = (previewToken: string) => {
    const url = `${window.location.origin}/invite/${previewToken}`;
    navigator.clipboard.writeText(url);
    setCopiedToken(previewToken);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  // Filtered members
  const filteredMembers = members.filter((m) => {
    const matchesSearch =
      m.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === "ALL" || m.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Collaboration & Secure Access"
        description={`Manage workspace invitations, role assignments, and member access for "${activeWorkspace?.name || "Workspace"}".`}
      />

      <SettingsNav />

      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-medium border ${
            message.type === "success"
              ? "bg-success/10 text-success border-success/20"
              : "bg-danger/10 text-danger border-danger/20"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border space-x-1">
        <button
          onClick={() => setActiveTab("members")}
          className={`flex items-center gap-2 py-3 px-4 text-xs font-bold border-b-2 transition-colors ${
            activeTab === "members"
              ? "border-brand text-brand"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Members ({members.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("invitations")}
          className={`flex items-center gap-2 py-3 px-4 text-xs font-bold border-b-2 transition-colors ${
            activeTab === "invitations"
              ? "border-brand text-brand"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          <Mail className="w-4 h-4" />
          <span>Invitations ({invitations.filter((i) => i.status === "PENDING").length})</span>
        </button>
        <button
          onClick={() => setActiveTab("roles")}
          className={`flex items-center gap-2 py-3 px-4 text-xs font-bold border-b-2 transition-colors ${
            activeTab === "roles"
              ? "border-brand text-brand"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Roles & Permissions</span>
        </button>
        <button
          onClick={() => setActiveTab("activity")}
          className={`flex items-center gap-2 py-3 px-4 text-xs font-bold border-b-2 transition-colors ${
            activeTab === "activity"
              ? "border-brand text-brand"
              : "border-transparent text-foreground-muted hover:text-foreground"
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Collaboration Activity</span>
        </button>
      </div>

      {/* TAB 1: MEMBERS DIRECTORY */}
      {activeTab === "members" && (
        <SectionCard title="Team Directory" subtitle="All active users and role privileges in this workspace.">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <input
                type="text"
                placeholder="Search members..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand w-full sm:w-64"
              />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-surface border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
              >
                <option value="ALL">All Roles</option>
                <option value="OWNER">Owner</option>
                <option value="ADMIN">Admin</option>
                <option value="ANALYST">Analyst</option>
                <option value="VIEWER">Viewer</option>
              </select>
            </div>

            {canManage && (
              <button
                onClick={() => setActiveTab("invitations")}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand-hover transition-colors"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Invite New Member</span>
              </button>
            )}
          </div>

          {/* Members Table */}
          <div className="border border-border rounded-xl bg-surface overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-muted/50 text-foreground-muted font-semibold">
                  <th className="py-3 px-4">Member</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Joined</th>
                  {canManage && <th className="py-3 px-4 text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredMembers.map((m) => (
                  <tr key={m.user_id} className="hover:bg-surface-muted/20 transition-colors">
                    <td className="py-3 px-4 font-bold text-foreground">
                      {m.display_name} {m.user_id === user?.user_id && <span className="text-[10px] text-brand font-normal">(You)</span>}
                    </td>
                    <td className="py-3 px-4 text-foreground-muted">{m.email}</td>
                    <td className="py-3 px-4">
                      {canManage && m.role !== "OWNER" ? (
                        <select
                          value={m.role}
                          onChange={(e) => handleRoleChange(m.user_id, e.target.value as RoleName)}
                          className="bg-surface-muted border border-border rounded px-2 py-1 text-xs text-foreground font-semibold"
                        >
                          <option value="ADMIN">ADMIN</option>
                          <option value="ANALYST">ANALYST</option>
                          <option value="VIEWER">VIEWER</option>
                        </select>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-surface-muted text-foreground font-semibold text-[11px]">
                          {m.role}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-foreground-muted">
                      {m.created_at ? new Date(m.created_at).toLocaleDateString() : "Active"}
                    </td>
                    {canManage && (
                      <td className="py-3 px-4 text-right">
                        {m.role !== "OWNER" && (
                          <button
                            onClick={() => handleRemoveMember(m.user_id, m.email)}
                            className="text-danger hover:underline font-medium text-xs"
                          >
                            Remove
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      {/* TAB 2: INVITATIONS */}
      {activeTab === "invitations" && (
        <div className="space-y-6">
          {/* Invite Form */}
          {canManage && (
            <SectionCard title="Invite Team Member" subtitle="Send single-use, time-limited workspace invitations.">
              <form onSubmit={handleSendInvitation} className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-foreground-muted mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-foreground-muted mb-1">
                    Intended Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                  >
                    <option value="ANALYST">Analyst (Edit & Analyze)</option>
                    <option value="ADMIN">Admin (Manage Team)</option>
                    <option value="VIEWER">Viewer (Read-Only)</option>
                  </select>
                </div>
                <div>
                  <button
                    type="submit"
                    disabled={isInviting || !inviteEmail}
                    className="w-full py-2 px-4 rounded-lg bg-brand text-white text-xs font-bold hover:bg-brand-hover transition-colors disabled:opacity-50"
                  >
                    {isInviting ? "Sending..." : "Create Invitation"}
                  </button>
                </div>
              </form>
            </SectionCard>
          )}

          {/* Outstanding Invitations List */}
          <SectionCard title="Workspace Invitations" subtitle="Track pending, accepted, and revoked invitations.">
            {invitations.length === 0 ? (
              <div className="p-8 text-center text-xs text-foreground-muted">
                No invitations created for this workspace.
              </div>
            ) : (
              <div className="divide-y divide-border border border-border rounded-xl bg-surface overflow-hidden">
                {invitations.map((inv) => (
                  <div key={inv.invitation_id} className="p-4 flex items-center justify-between text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-foreground">{inv.email}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            inv.status === "PENDING"
                              ? "bg-amber-500/10 text-amber-500"
                              : inv.status === "ACCEPTED"
                              ? "bg-success/10 text-success"
                              : "bg-surface-muted text-foreground-muted"
                          }`}
                        >
                          {inv.status}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-brand/10 text-brand font-semibold text-[10px]">
                          {inv.intended_role}
                        </span>
                      </div>
                      <div className="text-[11px] text-foreground-muted">
                        Invited by {inv.inviter_name} • Expires {new Date(inv.expires_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {inv.preview_token && inv.status === "PENDING" && (
                        <button
                          onClick={() => copyInviteLink(inv.preview_token!)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-muted hover:bg-border text-foreground font-medium transition-colors"
                        >
                          {copiedToken === inv.preview_token ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedToken === inv.preview_token ? "Copied" : "Copy Link"}</span>
                        </button>
                      )}
                      {canManage && inv.status === "PENDING" && (
                        <>
                          <button
                            onClick={() => handleResendInvitation(inv.invitation_id)}
                            className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-muted hover:bg-border text-foreground font-medium transition-colors"
                            title="Generate fresh token"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>Resend</span>
                          </button>
                          <button
                            onClick={() => handleRevokeInvitation(inv.invitation_id)}
                            className="px-2.5 py-1 rounded bg-danger/10 hover:bg-danger/20 text-danger font-medium transition-colors"
                          >
                            Revoke
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {/* TAB 3: ROLES & CAPABILITIES */}
      {activeTab === "roles" && (
        <SectionCard title="Roles & Security Capabilities" subtitle="AnalyzaX standard permission definitions.">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
              <div className="font-bold text-sm text-foreground">OWNER</div>
              <p className="text-xs text-foreground-muted">
                Complete control over workspace assets, membership management, billing, and workspace destruction.
              </p>
              <div className="text-[10px] text-brand font-semibold pt-2">Full Privileges</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
              <div className="font-bold text-sm text-foreground">ADMIN</div>
              <p className="text-xs text-foreground-muted">
                Invite team members, assign project access, create shared assets, manage configuration.
              </p>
              <div className="text-[10px] text-brand font-semibold pt-2">Manage Members & Projects</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
              <div className="font-bold text-sm text-foreground">ANALYST</div>
              <p className="text-xs text-foreground-muted">
                Upload datasets, run SQL queries, train ML models, construct interactive dashboards, and author reports.
              </p>
              <div className="text-[10px] text-brand font-semibold pt-2">Read, Write, Analyze</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-surface space-y-2">
              <div className="font-bold text-sm text-foreground">VIEWER</div>
              <p className="text-xs text-foreground-muted">
                Read-only access to authorized dashboards, reports, and statistical findings. Export restricted by policy.
              </p>
              <div className="text-[10px] text-brand font-semibold pt-2">Read-Only Presentation</div>
            </div>
          </div>
        </SectionCard>
      )}

      {/* TAB 4: COLLABORATION ACTIVITY */}
      {activeTab === "activity" && (
        <SectionCard title="Collaboration Audit Stream" subtitle="Cryptographically logged team access and sharing events.">
          {auditLogs.length === 0 ? (
            <div className="p-8 text-center text-xs text-foreground-muted">
              No audit events recorded for this period.
            </div>
          ) : (
            <div className="divide-y divide-border border border-border rounded-xl bg-surface overflow-hidden">
              {auditLogs.map((log) => (
                <div key={log.event_id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-foreground">{log.event_type}</div>
                    <div className="text-foreground-muted text-[11px] mt-0.5">
                      Actor: {log.user_id} • Result: {log.result}
                    </div>
                  </div>
                  <div className="text-foreground-muted text-[11px]">
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}

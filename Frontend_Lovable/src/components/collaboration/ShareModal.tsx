"use client";

import React, { useState, useEffect, useCallback } from "react";
import { collaborationApi } from "@/services/collaborationApi";
import {
  CollaborationResourceType,
  ResourceAccessSummary,
  ShareLink,
  ShareLinkMode,
  SharePermission,
  ShareRecipientType,
} from "@/types/collaboration";
import { authApi } from "@/services/authApi";
import { useWorkspace } from "@/context/WorkspaceContext";
import { WorkspaceMemberDetail } from "@/types/auth";

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  resourceType: CollaborationResourceType;
  resourceId: string;
  resourceTitle: string;
}

export function ShareModal({
  isOpen,
  onClose,
  resourceType,
  resourceId,
  resourceTitle,
}: ShareModalProps) {
  const { activeWorkspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState<"direct" | "links" | "manage">("direct");
  const [accessSummary, setAccessSummary] = useState<ResourceAccessSummary | null>(null);
  const [workspaceMembers, setWorkspaceMembers] = useState<WorkspaceMemberDetail[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Direct share form
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedPermission, setSelectedPermission] = useState<SharePermission>("VIEW");
  const [expiresInHours, setExpiresInHours] = useState<number | undefined>(undefined);
  const [isSharing, setIsSharing] = useState(false);

  // Link generation form
  const [linkMode, setLinkMode] = useState<ShareLinkMode>("INTERNAL_AUTHENTICATED");
  const [linkPermission, setLinkPermission] = useState<SharePermission>("VIEW");
  const [linkExpiresHours, setLinkExpiresHours] = useState<number | undefined>(undefined);
  const [isGeneratingLink, setIsGeneratingLink] = useState(false);
  const [copiedLinkId, setCopiedLinkId] = useState<string | null>(null);

  const loadAccess = useCallback(async () => {
    if (!isOpen) return;
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const summary = await collaborationApi.getResourceAccess(resourceType, resourceId);
      setAccessSummary(summary);

      if (activeWorkspace?.workspace_id) {
        const members = await authApi.getMembers(activeWorkspace.workspace_id);
        setWorkspaceMembers(members);
      }
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to load access details" });
    } finally {
      setIsLoading(false);
    }
  }, [isOpen, resourceType, resourceId, activeWorkspace?.workspace_id]);

  useEffect(() => {
    if (isOpen) {
      loadAccess();
    }
  }, [isOpen, loadAccess]);

  if (!isOpen) return null;

  const handleCreateShare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) {
      setStatusMessage({ type: "error", text: "Please select a team member" });
      return;
    }
    setIsSharing(true);
    setStatusMessage(null);
    try {
      await collaborationApi.createShare({
        resource_type: resourceType,
        resource_id: resourceId,
        recipient_type: "USER",
        recipient_id: selectedUserId,
        permission: selectedPermission,
        expires_in_hours: expiresInHours ? Number(expiresInHours) : null,
      });
      setStatusMessage({ type: "success", text: "Share created successfully!" });
      setSelectedUserId("");
      await loadAccess();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to create share" });
    } finally {
      setIsSharing(false);
    }
  };

  const handleRevokeShare = async (shareId: string) => {
    if (!confirm("Are you sure you want to revoke this direct share?")) return;
    try {
      await collaborationApi.revokeShare(shareId);
      setStatusMessage({ type: "success", text: "Share revoked successfully." });
      await loadAccess();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to revoke share" });
    }
  };

  const handleCreateLink = async () => {
    setIsGeneratingLink(true);
    setStatusMessage(null);
    try {
      await collaborationApi.createShareLink({
        resource_type: resourceType,
        resource_id: resourceId,
        link_mode: linkMode,
        permission: linkPermission,
        expires_in_hours: linkExpiresHours ? Number(linkExpiresHours) : null,
      });
      setStatusMessage({ type: "success", text: "Share link created successfully!" });
      await loadAccess();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to create share link" });
    } finally {
      setIsGeneratingLink(false);
    }
  };

  const handleRevokeLink = async (linkId: string) => {
    if (!confirm("Are you sure you want to revoke this share link? Anyone using this link will immediately lose access.")) return;
    try {
      await collaborationApi.revokeShareLink(linkId);
      setStatusMessage({ type: "success", text: "Share link revoked." });
      await loadAccess();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to revoke link" });
    }
  };

  const copyToClipboard = (url: string, id: string) => {
    navigator.clipboard.writeText(url);
    setCopiedLinkId(id);
    setTimeout(() => setCopiedLinkId(null), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-surface-elevated border border-border rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-muted/40">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-brand/10 text-brand uppercase tracking-wider">
                {resourceType}
              </span>
              <h2 className="text-lg font-bold text-foreground truncate max-w-md">
                Share &ldquo;{resourceTitle}&rdquo;
              </h2>
            </div>
            <p className="text-xs text-foreground-muted mt-0.5">
              Manage permissions, secure share links, and team access.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-foreground-muted hover:text-foreground p-1.5 rounded-lg hover:bg-surface transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border px-6 bg-surface">
          <button
            onClick={() => setActiveTab("direct")}
            className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "direct"
                ? "border-brand text-brand"
                : "border-transparent text-foreground-muted hover:text-foreground"
            }`}
          >
            Invite People
          </button>
          <button
            onClick={() => setActiveTab("links")}
            className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "links"
                ? "border-brand text-brand"
                : "border-transparent text-foreground-muted hover:text-foreground"
            }`}
          >
            Share Links
          </button>
          <button
            onClick={() => setActiveTab("manage")}
            className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "manage"
                ? "border-brand text-brand"
                : "border-transparent text-foreground-muted hover:text-foreground"
            }`}
          >
            Manage Access ({(accessSummary?.direct_shares.length || 0) + (accessSummary?.inherited_access.length || 0)})
          </button>
        </div>

        {/* Status Alerts */}
        {statusMessage && (
          <div
            className={`mx-6 mt-4 p-3 rounded-lg text-xs font-medium ${
              statusMessage.type === "success"
                ? "bg-success/10 text-success border border-success/20"
                : "bg-danger/10 text-danger border border-danger/20"
            }`}
          >
            {statusMessage.text}
          </div>
        )}

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {isLoading ? (
            <div className="py-12 text-center text-foreground-muted text-sm">
              Loading access rules...
            </div>
          ) : activeTab === "direct" ? (
            /* TAB 1: DIRECT SHARE */
            <form onSubmit={handleCreateShare} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-foreground-muted uppercase tracking-wider mb-2">
                  Select Team Member
                </label>
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                  required
                >
                  <option value="">Choose a member from workspace...</option>
                  {workspaceMembers.map((m) => (
                    <option key={m.user_id} value={m.user_id}>
                      {m.display_name} ({m.email}) — {m.role}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground-muted uppercase tracking-wider mb-2">
                    Permission Level
                  </label>
                  <select
                    value={selectedPermission}
                    onChange={(e) => setSelectedPermission(e.target.value as SharePermission)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                  >
                    <option value="VIEW">Can View (Read-Only)</option>
                    <option value="EDIT">Can Edit (Modify Resource)</option>
                    <option value="EXPORT">Can Export (Download Data/Report)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-foreground-muted uppercase tracking-wider mb-2">
                    Expiration (Optional)
                  </label>
                  <select
                    value={expiresInHours || ""}
                    onChange={(e) => setExpiresInHours(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                  >
                    <option value="">Never Expires</option>
                    <option value="1">1 Hour</option>
                    <option value="24">24 Hours (1 Day)</option>
                    <option value="168">7 Days</option>
                    <option value="720">30 Days</option>
                  </select>
                </div>
              </div>

              <div className="bg-surface-muted/50 border border-border rounded-lg p-3 text-xs text-foreground-muted leading-relaxed">
                ℹ️ <strong>Sharing creates access, not copies:</strong> The selected user will view or edit the exact same analytical asset live. They will not automatically gain access to unrelated datasets.
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={isSharing}
                  className="px-5 py-2 rounded-lg bg-brand hover:bg-brand-hover text-white text-sm font-semibold transition-all disabled:opacity-50"
                >
                  {isSharing ? "Granting Access..." : "Grant Access"}
                </button>
              </div>
            </form>
          ) : activeTab === "links" ? (
            /* TAB 2: SHARE LINKS */
            <div className="space-y-6">
              <div className="bg-surface border border-border rounded-xl p-4 space-y-4">
                <h3 className="text-sm font-bold text-foreground">Create a New Share Link</h3>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-foreground-muted mb-1">
                      Link Security Mode
                    </label>
                    <select
                      value={linkMode}
                      onChange={(e) => setLinkMode(e.target.value as ShareLinkMode)}
                      className="w-full bg-surface-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground"
                    >
                      <option value="INTERNAL_AUTHENTICATED">Internal (Requires Login)</option>
                      <option value="PUBLIC_READ_ONLY">Public Read-Only (Anyone with link)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-foreground-muted mb-1">
                      Permission
                    </label>
                    <select
                      value={linkPermission}
                      onChange={(e) => setLinkPermission(e.target.value as SharePermission)}
                      className="w-full bg-surface-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground"
                    >
                      <option value="VIEW">Can View</option>
                      <option value="EXPORT">Can Export</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-foreground-muted mb-1">
                      Expires In
                    </label>
                    <select
                      value={linkExpiresHours || ""}
                      onChange={(e) => setLinkExpiresHours(e.target.value ? Number(e.target.value) : undefined)}
                      className="w-full bg-surface-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground"
                    >
                      <option value="">Never</option>
                      <option value="24">1 Day</option>
                      <option value="168">7 Days</option>
                      <option value="720">30 Days</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleCreateLink}
                    disabled={isGeneratingLink}
                    className="px-4 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand-hover transition-colors disabled:opacity-50"
                  >
                    {isGeneratingLink ? "Generating Link..." : "+ Generate Secure Link"}
                  </button>
                </div>
              </div>

              {/* Active Links List */}
              <div>
                <h4 className="text-xs font-bold text-foreground-muted uppercase tracking-wider mb-3">
                  Active Share Links ({accessSummary?.active_links.length || 0})
                </h4>
                {(!accessSummary?.active_links || accessSummary.active_links.length === 0) ? (
                  <p className="text-xs text-foreground-muted italic">No active share links created yet.</p>
                ) : (
                  <div className="space-y-2">
                    {accessSummary.active_links.map((link) => (
                      <div
                        key={link.share_link_id}
                        className="flex items-center justify-between p-3 rounded-lg border border-border bg-surface text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                                link.link_mode === "PUBLIC_READ_ONLY"
                                  ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                                  : "bg-blue-500/10 text-blue-500 border border-blue-500/20"
                              }`}
                            >
                              {link.link_mode === "PUBLIC_READ_ONLY" ? "Public" : "Internal Auth"}
                            </span>
                            <span className="font-semibold text-foreground uppercase">{link.permission}</span>
                            <span className="text-foreground-muted">
                              • Accessed {link.access_count} times
                            </span>
                          </div>
                          <div className="text-[11px] text-foreground-muted">
                            {link.expires_at ? `Expires: ${new Date(link.expires_at).toLocaleDateString()}` : "Does not expire"}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {link.share_url && (
                            <button
                              onClick={() => copyToClipboard(link.share_url!, link.share_link_id)}
                              className="px-2.5 py-1 rounded bg-surface-muted hover:bg-border text-foreground font-medium transition-colors"
                            >
                              {copiedLinkId === link.share_link_id ? "✓ Copied!" : "Copy Link"}
                            </button>
                          )}
                          <button
                            onClick={() => handleRevokeLink(link.share_link_id)}
                            className="px-2.5 py-1 rounded bg-danger/10 hover:bg-danger/20 text-danger font-medium transition-colors"
                          >
                            Revoke
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* TAB 3: MANAGE ACCESS (DIRECT + INHERITED) */
            <div className="space-y-6">
              {/* Direct Shares */}
              <div>
                <h4 className="text-xs font-bold text-foreground-muted uppercase tracking-wider mb-2">
                  Directly Shared Users ({accessSummary?.direct_shares.length || 0})
                </h4>
                {(!accessSummary?.direct_shares || accessSummary.direct_shares.length === 0) ? (
                  <p className="text-xs text-foreground-muted italic">No direct shares assigned.</p>
                ) : (
                  <div className="divide-y divide-border border border-border rounded-lg bg-surface overflow-hidden">
                    {accessSummary.direct_shares.map((entry) => (
                      <div key={entry.principal_id} className="flex items-center justify-between p-3 text-xs">
                        <div>
                          <div className="font-bold text-foreground">{entry.principal_name}</div>
                          <div className="text-foreground-muted flex items-center gap-2 mt-0.5">
                            <span className="font-medium text-brand">{entry.permission}</span>
                            <span>•</span>
                            <span>Direct Share</span>
                            {entry.expires_at && (
                              <span>• Expires {new Date(entry.expires_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                        {entry.share_id && (
                          <button
                            onClick={() => handleRevokeShare(entry.share_id!)}
                            className="text-danger hover:underline font-medium"
                          >
                            Revoke
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Inherited Workspace / Project Access */}
              <div>
                <h4 className="text-xs font-bold text-foreground-muted uppercase tracking-wider mb-2">
                  Inherited Workspace & Project Access ({accessSummary?.inherited_access.length || 0})
                </h4>
                <div className="divide-y divide-border border border-border rounded-lg bg-surface overflow-hidden">
                  {accessSummary?.inherited_access.map((entry) => (
                    <div key={entry.principal_id} className="flex items-center justify-between p-3 text-xs">
                      <div>
                        <div className="font-bold text-foreground">{entry.principal_name}</div>
                        <div className="text-foreground-muted flex items-center gap-2 mt-0.5">
                          <span className="font-semibold text-foreground uppercase">{entry.permission}</span>
                          <span>•</span>
                          <span className="text-foreground-muted">{entry.source}</span>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-surface-muted text-foreground-muted text-[10px] font-semibold uppercase">
                        Inherited
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-surface-muted/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-surface border border-border hover:bg-surface-muted text-xs font-medium text-foreground transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useCallback } from "react";
import { collaborationApi } from "@/services/collaborationApi";
import { authApi } from "@/services/authApi";
import { ProjectMemberDetail } from "@/types/collaboration";
import { WorkspaceMemberDetail } from "@/types/auth";
import { useWorkspace } from "@/context/WorkspaceContext";

interface ProjectAccessModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
}

export function ProjectAccessModal({
  isOpen,
  onClose,
  projectId,
  projectName,
}: ProjectAccessModalProps) {
  const { activeWorkspace } = useWorkspace();
  const [projectMembers, setProjectMembers] = useState<ProjectMemberDetail[]>([]);
  const [workspaceMembers, setWorkspaceMembers] = useState<WorkspaceMemberDetail[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedRole, setSelectedRole] = useState<string>("ANALYST");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = useCallback(async () => {
    if (!isOpen || !projectId) return;
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const pm = await collaborationApi.listProjectMembers(projectId);
      setProjectMembers(pm);

      if (activeWorkspace?.workspace_id) {
        const wm = await authApi.getMembers(activeWorkspace.workspace_id);
        setWorkspaceMembers(wm);
      }
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to load project members" });
    } finally {
      setIsLoading(false);
    }
  }, [isOpen, projectId, activeWorkspace?.workspace_id]);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen, loadData]);

  if (!isOpen) return null;

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) return;
    setIsSubmitting(true);
    setStatusMessage(null);
    try {
      await collaborationApi.addProjectMember(projectId, {
        user_id: selectedUserId,
        role: selectedRole,
      });
      setStatusMessage({ type: "success", text: "Added member to project successfully!" });
      setSelectedUserId("");
      await loadData();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to add project member" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemoveMember = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to remove ${email} from this project?`)) return;
    try {
      await collaborationApi.removeProjectMember(projectId, userId);
      setStatusMessage({ type: "success", text: "Member removed from project." });
      await loadData();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to remove member" });
    }
  };

  // Filter workspace members not already in the project
  const currentMemberIds = new Set(projectMembers.map((m) => m.user_id));
  const availableWorkspaceMembers = workspaceMembers.filter(
    (wm) => !currentMemberIds.has(wm.user_id)
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-surface-elevated border border-border rounded-xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-muted/40">
          <div>
            <h2 className="text-lg font-bold text-foreground">
              Project Access — {projectName}
            </h2>
            <p className="text-xs text-foreground-muted mt-0.5">
              Control explicit team member access to this project&apos;s assets.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-foreground-muted hover:text-foreground p-1.5 rounded-lg hover:bg-surface transition-colors"
          >
            ✕
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
          {/* Add member form */}
          <form onSubmit={handleAddMember} className="bg-surface border border-border rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-bold text-foreground-muted uppercase tracking-wider">
              Add Existing Workspace Member
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="w-full bg-surface-muted border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                  required
                >
                  <option value="">Select workspace member...</option>
                  {availableWorkspaceMembers.map((wm) => (
                    <option key={wm.user_id} value={wm.user_id}>
                      {wm.display_name} ({wm.email})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full bg-surface-muted border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand"
                >
                  <option value="ANALYST">Analyst</option>
                  <option value="ADMIN">Admin</option>
                  <option value="VIEWER">Viewer</option>
                </select>
              </div>
            </div>
            <div className="flex justify-between items-center pt-1">
              <span className="text-[11px] text-foreground-muted">
                Invariant: Only members of workspace can join projects.
              </span>
              <button
                type="submit"
                disabled={isSubmitting || !selectedUserId}
                className="px-4 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand-hover transition-colors disabled:opacity-50"
              >
                {isSubmitting ? "Adding..." : "+ Add to Project"}
              </button>
            </div>
          </form>

          {/* Current project members */}
          <div>
            <h4 className="text-xs font-bold text-foreground-muted uppercase tracking-wider mb-2">
              Current Project Members ({projectMembers.length})
            </h4>
            {isLoading ? (
              <div className="py-6 text-center text-xs text-foreground-muted">Loading project members...</div>
            ) : projectMembers.length === 0 ? (
              <div className="p-4 border border-border rounded-lg text-center text-xs text-foreground-muted">
                No explicit project members assigned yet.
              </div>
            ) : (
              <div className="divide-y divide-border border border-border rounded-lg bg-surface overflow-hidden">
                {projectMembers.map((pm) => (
                  <div key={pm.user_id} className="flex items-center justify-between p-3 text-xs">
                    <div>
                      <div className="font-bold text-foreground">{pm.display_name}</div>
                      <div className="text-foreground-muted flex items-center gap-2 mt-0.5">
                        <span className="text-foreground">{pm.email}</span>
                        <span>•</span>
                        <span className="font-semibold text-brand">{pm.role}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveMember(pm.user_id, pm.email)}
                      className="text-danger hover:underline font-medium"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-surface-muted/30 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-surface border border-border hover:bg-surface-muted text-xs font-medium text-foreground transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

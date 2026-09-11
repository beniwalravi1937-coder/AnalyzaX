"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { collaborationApi } from "@/services/collaborationApi";
import { VerifyInvitationResponse } from "@/types/collaboration";
import { useAuth } from "@/context/AuthContext";
import { CheckCircle, XCircle, AlertCircle, ArrowRight, Shield } from "lucide-react";

export default function InviteAcceptancePage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;
  const { user, refreshUser } = useAuth();

  const [invitation, setInvitation] = useState<VerifyInvitationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAccepting, setIsAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accepted, setAccepted] = useState(false);

  const verifyToken = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await collaborationApi.verifyInvitation(token);
      setInvitation(data);
    } catch (err: any) {
      setError(err.message || "Invalid or expired invitation link.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    verifyToken();
  }, [verifyToken]);

  const handleAccept = async () => {
    if (!invitation || !token) return;
    setIsAccepting(true);
    setError(null);
    try {
      await collaborationApi.acceptInvitation(invitation.invitation_id, token);
      setAccepted(true);
      if (refreshUser) {
        await refreshUser();
      }
      setTimeout(() => {
        router.push("/workspace");
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to accept invitation.");
    } finally {
      setIsAccepting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-background">
      <div className="w-full max-w-md bg-surface-elevated border border-border rounded-2xl shadow-2xl p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-full bg-brand/10 text-brand mb-2">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            Team Workspace Invitation
          </h1>
          <p className="text-xs text-foreground-muted">
            You&apos;ve been invited to collaborate on AnalyzaX
          </p>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-xs text-foreground-muted animate-pulse">
            Verifying invitation credentials...
          </div>
        ) : error ? (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-danger/10 border border-danger/20 flex items-start gap-3">
              <XCircle className="w-5 h-5 text-danger shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-danger">Invitation Unavailable</h4>
                <p className="text-xs text-danger/80 mt-1">{error}</p>
              </div>
            </div>
            <div className="text-center">
              <Link
                href="/login"
                className="text-xs text-brand hover:underline font-semibold"
              >
                Return to Login
              </Link>
            </div>
          </div>
        ) : accepted ? (
          <div className="space-y-4 text-center py-6">
            <CheckCircle className="w-12 h-12 text-success mx-auto" />
            <h3 className="text-base font-bold text-foreground">Welcome to the Team!</h3>
            <p className="text-xs text-foreground-muted">
              Redirecting you to the workspace dashboard now...
            </p>
          </div>
        ) : invitation ? (
          <div className="space-y-6">
            <div className="p-4 rounded-xl bg-surface border border-border space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground-muted">Workspace:</span>
                <span className="font-bold text-foreground">{invitation.workspace_name}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground-muted">Invited By:</span>
                <span className="font-medium text-foreground">{invitation.inviter_name}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground-muted">Intended Role:</span>
                <span className="px-2 py-0.5 rounded bg-brand/10 text-brand font-bold text-[11px] uppercase">
                  {invitation.intended_role}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-foreground-muted">Target Account:</span>
                <span className="font-medium text-foreground">{invitation.email}</span>
              </div>
            </div>

            {user ? (
              <div className="space-y-3">
                <div className="text-xs text-center text-foreground-muted">
                  Signed in as <strong>{user.email}</strong>
                </div>
                <button
                  onClick={handleAccept}
                  disabled={isAccepting}
                  className="w-full py-3 px-4 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold text-sm transition-all shadow-lg shadow-brand/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isAccepting ? "Accepting Invitation..." : "Accept Invitation & Join"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-500 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Please sign in or register to accept this workspace invitation.</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Link
                    href={`/login?redirect=/invite/${token}`}
                    className="py-2.5 px-4 rounded-xl bg-surface border border-border hover:bg-surface-muted text-foreground text-center font-bold text-xs transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href={`/register?redirect=/invite/${token}&email=${encodeURIComponent(invitation.email)}`}
                    className="py-2.5 px-4 rounded-xl bg-brand text-white text-center font-bold text-xs hover:bg-brand-hover transition-colors"
                  >
                    Create Account
                  </Link>
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}

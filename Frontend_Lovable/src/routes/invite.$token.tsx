import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { useState } from "react";
import { AlertCircle, ArrowRight, CheckCircle, Shield, XCircle } from "lucide-react";

import { acceptInvitation, verifyInvitation } from "@/lib/team.functions";
import { useAuth } from "@/lib/auth/auth";

export const Route = createFileRoute("/invite/$token")({
  head: () => ({
    meta: [
      { title: "Accept your AnalyzaX workspace invitation" },
      {
        name: "description",
        content: "Review and accept an invitation to collaborate on an AnalyzaX analytics workspace.",
      },
      { property: "og:title", content: "AnalyzaX workspace invitation" },
      { property: "og:description", content: "You have been invited to collaborate on AnalyzaX." },
    ],
  }),
  component: InvitePage,
});

function InvitePage() {
  const { token } = Route.useParams();
  const navigate = useNavigate();
  const { session, user, loading } = useAuth();
  const verify = useServerFn(verifyInvitation);
  const accept = useServerFn(acceptInvitation);
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["invitation", token],
    queryFn: () => verify({ data: { token } }),
  });

  async function handleAccept() {
    setError(null);
    setAccepting(true);
    try {
      await accept({ data: { token } });
      setAccepted(true);
      setTimeout(() => navigate({ to: "/team" }), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not accept this invitation.");
    } finally {
      setAccepting(false);
    }
  }

  const nextPath = `/invite/${token}`;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header" style={{ textAlign: "center" }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: "0.75rem" }}>
            <img src="/logo.png" alt="AnalyzaX Logo" style={{ width: "52px", height: "52px", objectFit: "contain", filter: "drop-shadow(0 4px 14px rgba(59, 130, 246, 0.45))" }} />
          </div>
          <h1 className="auth-title">Workspace invitation</h1>
          <p className="auth-subtitle">You&apos;ve been invited to collaborate on AnalyzaX</p>
        </div>

        {isLoading && <p className="stat-subtext">Checking your invitation…</p>}

        {!isLoading && data && data.status !== "valid" && (
          <div className="auth-alert auth-alert-error" role="alert">
            <XCircle className="w-4 h-4" />
            <span>
              {data.status === "expired" && "This invitation has expired. Ask for a new link."}
              {data.status === "accepted" && "This invitation has already been used."}
              {data.status === "revoked" && "This invitation was cancelled."}
              {data.status === "invalid" && "This invitation link is not valid."}
            </span>
          </div>
        )}

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {accepted && (
          <div className="auth-alert auth-alert-success" role="status">
            <CheckCircle className="w-4 h-4" />
            <span>Invitation accepted. Opening your workspace…</span>
          </div>
        )}

        {!isLoading && data?.status === "valid" && !accepted && (
          <>
            <ul className="invite-details">
              <li>
                <span>Workspace</span>
                <strong>{data.workspaceName}</strong>
              </li>
              <li>
                <span>Invited email</span>
                <strong>{data.email}</strong>
              </li>
              <li>
                <span>Role</span>
                <strong>{data.role}</strong>
              </li>
              {data.invitedByName && (
                <li>
                  <span>Invited by</span>
                  <strong>{data.invitedByName}</strong>
                </li>
              )}
            </ul>

            {loading ? null : session ? (
              <>
                <p className="stat-subtext" style={{ marginBottom: "0.75rem" }}>
                  Signed in as {user?.email}
                </p>
                <button className="btn btn-primary auth-submit" onClick={handleAccept} disabled={accepting}>
                  {accepting ? "Accepting…" : "Accept invitation"}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <p className="stat-subtext" style={{ marginBottom: "0.75rem" }}>
                  Sign in or create an account to accept this invitation.
                </p>
                <Link to="/login" search={{ next: nextPath }} className="btn btn-primary auth-submit">
                  Sign in
                </Link>
                <Link
                  to="/register"
                  search={{ next: nextPath }}
                  className="btn btn-secondary auth-submit"
                  style={{ marginTop: "0.5rem" }}
                >
                  Create an account
                </Link>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

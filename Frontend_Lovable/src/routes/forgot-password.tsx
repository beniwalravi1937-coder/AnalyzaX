import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AlertCircle, CheckCircle } from "lucide-react";
import { authApi } from "../services/authApi";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Forgot Password — AnalyzaX" },
      {
        name: "description",
        content:
          "Reset your password securely. Enter your account email to receive a password recovery link and regain access to your workspaces.",
      },
      { property: "og:title", content: "Forgot Password — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Reset your password securely and regain access to your AnalyzaX workspaces.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
    ],
  }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authApi.requestPasswordReset(email.trim());
      setSent(true);
    } catch (err: any) {
      setError(err.message || "Failed to send reset link. Please check your email address.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <Link to="/" className="auth-brand-logo-wrap" title="AnalyzaX Home">
            <img
              src="/logo.png"
              alt="AnalyzaX Logo"
              style={{
                width: "56px",
                height: "56px",
                objectFit: "contain",
                filter: "drop-shadow(0 4px 16px rgba(59, 130, 246, 0.5))",
              }}
            />
          </Link>
          <div className="auth-brand-badge">
            <span>FastAPI Security Gate</span>
          </div>
          <h1 className="auth-title">Reset your password</h1>
          <p className="auth-subtitle">Enter your registered email address to receive reset instructions.</p>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {sent ? (
          <div className="space-y-4 text-center">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
              <CheckCircle className="w-5 h-5 mx-auto mb-2" />
              Password reset request dispatched. If this account exists in the platform, instructions have been generated.
            </div>
            <Link to="/login" className="btn btn-primary auth-submit">
              Return to sign in
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label htmlFor="email">Account Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                disabled={isLoading}
              />
            </div>

            <button type="submit" className="btn btn-primary auth-submit" disabled={isLoading || !email.trim()}>
              {isLoading ? "Sending..." : "Send reset instructions"}
            </button>
          </form>
        )}

        <p className="auth-footer">
          Remembered your password?{" "}
          <Link to="/login" className="auth-link">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AlertCircle, CheckCircle, Sparkles, Eye, EyeOff } from "lucide-react";
import { authApi } from "../services/authApi";

export const Route = createFileRoute("/reset-password")({
  validateSearch: (search: Record<string, unknown>) => ({
    token: (search["token"] as string) || "",
  }),
  head: () => ({
    meta: [
      { title: "Set a new AnalyzaX password" },
      {
        name: "description",
        content: "Choose a new secure password to finish recovering your AnalyzaX account.",
      },
    ],
  }),
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const [resetToken, setResetToken] = useState(token);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!resetToken.trim()) {
      setError("Password reset token is missing.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await authApi.confirmPasswordReset(resetToken.trim(), newPassword);
      setSuccess(true);
      setTimeout(() => {
        navigate({ to: "/login", replace: true });
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to reset password. The token may be expired or invalid.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-badge">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>FastAPI Security Gate</span>
          </div>
          <h1 className="auth-title">Set new password</h1>
          <p className="auth-subtitle">Enter your recovery token and new password.</p>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {success ? (
          <div className="space-y-4 text-center">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
              <CheckCircle className="w-5 h-5 mx-auto mb-2" />
              Password updated successfully! Redirecting to sign in...
            </div>
            <Link to="/login" className="btn btn-primary auth-submit">
              Sign in now
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form">
            {!token && (
              <div className="field">
                <label htmlFor="token">Reset Token</label>
                <input
                  id="token"
                  type="text"
                  required
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Paste your reset token"
                  disabled={isLoading}
                />
              </div>
            )}

            <div className="field">
              <label htmlFor="newPassword">New Password</label>
              <div className="password-wrap">
                <input
                  id="newPassword"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="field">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                id="confirmPassword"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            <button type="submit" className="btn btn-primary auth-submit" disabled={isLoading}>
              {isLoading ? "Updating password..." : "Update password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

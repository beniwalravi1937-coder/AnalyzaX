import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Eye, EyeOff, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const Route = createFileRoute("/register")({
  validateSearch: (search: Record<string, unknown>) => ({
    next: (search["next"] as string) || (search["redirect"] as string) || "/",
  }),
  head: () => ({
    meta: [
      { title: "Turn RAW Data Into Insightful Decisions — AnalyzaX" },
      {
        name: "description",
        content:
          "Turn RAW data into insightful decisions. Upload spreadsheets, run automated quality audits, and discover insights in seconds without coding.",
      },
      { property: "og:title", content: "Turn RAW Data Into Insightful Decisions — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Turn RAW data into insightful decisions, automated quality checks, and predictive intelligence.",
      },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const { next } = Route.useSearch();
  const navigate = useNavigate();
  const { user, register, isLoading: authLoading } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!authLoading && user && !success) {
      navigate({ to: next || "/", replace: true });
    }
  }, [authLoading, user, next, navigate, success]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await register(email, password, displayName.trim() || email.split("@")[0]);
      setSuccess(true);
      setTimeout(() => {
        navigate({ to: next || "/", replace: true });
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">
            <div className="auth-brand-badge" style={{ color: "var(--accent-emerald)" }}>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Registration Successful</span>
            </div>
            <h1 className="auth-title">Welcome to AnalyzaX!</h1>
            <p className="auth-subtitle">Your analytical account has been created. Redirecting to workspace...</p>
          </div>
        </div>
      </div>
    );
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
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Turn RAW data into insightful analytics</span>
          </div>
          <h1 className="auth-title" style={{ fontSize: "1.45rem", lineHeight: 1.25 }}>
            Turn RAW data into{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #38bdf8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              insightful decisions
            </span>
          </h1>
          <p className="auth-subtitle">
            Turn raw data into insightful, executive decisions and charts in seconds.
          </p>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label htmlFor="displayName">Full Name</label>
            <input
              id="displayName"
              type="text"
              autoComplete="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Alex Smith"
              disabled={isLoading}
            />
          </div>

          <div className="field">
            <label htmlFor="email">Work Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              disabled={isLoading}
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <div className="password-wrap">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
            <label htmlFor="confirmPassword">Confirm Password</label>
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
            {isLoading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login" search={{ next }} className="auth-link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

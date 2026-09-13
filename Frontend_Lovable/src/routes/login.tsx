import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Eye, EyeOff, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const Route = createFileRoute("/login")({
  validateSearch: (search: Record<string, unknown>) => ({
    next: (search["next"] as string) || (search["redirect"] as string) || "/",
  }),
  head: () => ({
    meta: [
      { title: "Sign In — AnalyzaX" },
      {
        name: "description",
        content:
          "Sign in to your AnalyzaX workspace to explore datasets, build interactive dashboards, and generate AI-assisted insights.",
      },
      { property: "og:title", content: "Sign In — AnalyzaX" },
      {
        property: "og:description",
        content:
          "Sign in to your AnalyzaX workspace to explore datasets and generate AI-assisted insights.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { next } = Route.useSearch();
  const navigate = useNavigate();
  const { user, login, isLoading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && user) {
      navigate({ to: next || "/", replace: true });
    }
  }, [authLoading, user, next, navigate]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      navigate({ to: next || "/", replace: true });
    } catch (err: any) {
      setError(err.message || "Invalid email or password.");
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
            <span>FastAPI Analytical Cloud</span>
          </div>
          <h1 className="auth-title">Welcome back to AnalyzaX</h1>
          <p className="auth-subtitle">Sign in to your analytical workspaces, pipelines and models.</p>
        </div>

        {error && (
          <div className="auth-alert auth-alert-error" role="alert">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
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
            <div className="field-row">
              <label htmlFor="password">Password</label>
              <Link to="/forgot-password" className="auth-link-sm">
                Forgot password?
              </Link>
            </div>
            <div className="password-wrap">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
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

          <button type="submit" className="btn btn-primary auth-submit" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link to="/register" search={{ next }} className="auth-link">
            Create account
          </Link>
        </p>
      </div>
    </div>
  );
}

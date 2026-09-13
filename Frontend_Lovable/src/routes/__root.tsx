import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  useRouterState,
  useNavigate,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";
import {
  BarChart3,
  Bell,
  Brain,
  Calculator,
  Database,
  Download,
  FlaskConical,
  Folder,
  ShieldCheck,
  LayoutDashboard,
  Lightbulb,
  LogIn,
  LogOut,
  Users,
  Menu,
  Microscope,
  Settings,
  Sigma,
  Terminal,
  TrendingUp,
  Wand2,
  X,
} from "lucide-react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { DatasetProvider, useDataset } from "@/context/DatasetContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { AnalyzaXLogo } from "@/components/brand/AnalyzaXLogo";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, section: "Overview" },
  { to: "/insights", label: "Insights", icon: Lightbulb, section: "Overview" },
  { to: "/notifications", label: "Notifications", icon: Bell, section: "Overview" },
  { to: "/data", label: "Data Sources", icon: Database, section: "Data" },
  { to: "/quality", label: "Data Quality", icon: ShieldCheck, section: "Data" },
  { to: "/cleaning", label: "Cleaning Studio", icon: Wand2, section: "Data" },
  { to: "/sql", label: "SQL Workbench", icon: Terminal, section: "Data" },
  { to: "/visualizations", label: "Visualizations", icon: BarChart3, section: "Analysis" },
  { to: "/eda", label: "Explore", icon: Microscope, section: "Analysis" },
  { to: "/statistics", label: "Statistics", icon: Sigma, section: "Analysis" },
  { to: "/ai-analyst", label: "AI Analyst", icon: Brain, section: "Analysis" },
  { to: "/ml", label: "Machine Learning", icon: FlaskConical, section: "Modelling" },
  { to: "/forecasting", label: "Forecasting", icon: TrendingUp, section: "Modelling" },
  { to: "/projects", label: "Projects", icon: Folder, section: "Workspace" },
  { to: "/team", label: "Team", icon: Users, section: "Workspace" },
  { to: "/metrics", label: "Metric Library", icon: Calculator, section: "Workspace" },
  { to: "/exports", label: "Exports", icon: Download, section: "Workspace" },
  { to: "/settings", label: "Settings", icon: Settings, section: "Workspace" },
] as const;

function NotFoundComponent() {
  return (
    <div className="empty-state" style={{ marginTop: "3rem" }}>
      <div className="empty-state-title">Page not found</div>
      <div className="empty-state-desc">That screen isn&apos;t part of this workspace.</div>
      <Link to="/" className="btn btn-primary">
        Back to dashboard
      </Link>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="empty-state" style={{ marginTop: "3rem" }}>
      <div className="empty-state-title">This page didn&apos;t load</div>
      <div className="empty-state-desc">{error.message}</div>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          className="btn btn-primary"
          onClick={() => {
            router.invalidate();
            reset();
          }}
        >
          Try again
        </button>
        <a className="btn btn-secondary" href="/">
          Go home
        </a>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { name: "author", content: "AnalyzaX" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;500;600&display=swap",
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceProvider>
          <DatasetProvider>
            <AppShell />
          </DatasetProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

const AUTH_ROUTES = ["/login", "/register", "/forgot-password", "/reset-password", "/invite"];

function AppShell() {
  const [open, setOpen] = useState(false);
  const { datasets, activeDataset, selectDataset } = useDataset();
  const { user, logout, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const sections = [...new Set(NAV.map((n) => n.section))];

  const isAuthRoute = AUTH_ROUTES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  const isLandingRoute = pathname === "/";

  // Redirect unauthenticated visitors attempting to access internal protected routes
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated && !isAuthRoute && !isLandingRoute) {
      navigate({
        to: "/login",
        search: { next: pathname },
        replace: true,
      });
    }
  }, [isAuthLoading, isAuthenticated, isAuthRoute, isLandingRoute, pathname, navigate]);

  // Auth pages render without workspace shell
  if (isAuthRoute) {
    return <Outlet />;
  }

  // Unauthenticated visitor on / renders the public marketing landing page
  if (isLandingRoute && !isAuthenticated) {
    return <Outlet />;
  }

  // Loading state while checking auth status
  if (isAuthLoading && !isAuthenticated) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#0b0f19", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
          <AnalyzaXLogo size={36} showText={true} />
          <div style={{ width: "24px", height: "24px", border: "2px solid rgba(99, 102, 241, 0.2)", borderTopColor: "#6366f1", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
        </div>
      </div>
    );
  }

  // Guard protected routes while redirecting
  if (!isAuthenticated && !isLandingRoute) {
    return null;
  }

  return (
    <div className="app-shell">
      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}
      <aside className={open ? "sidebar open" : "sidebar"}>
        <div className="sidebar-header">
          <Link to="/" className="brand" onClick={() => setOpen(false)}>
            <AnalyzaXLogo size={28} showText={true} />
          </Link>
          <button className="icon-btn md-hide" onClick={() => setOpen(false)} aria-label="Close menu">
            <X className="w-4 h-4" />
          </button>
        </div>
        <nav className="sidebar-nav">
          {sections.map((section) => (
            <div key={section}>
              <div className="nav-section-title">{section}</div>
              {NAV.filter((n) => n.section === section).map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  activeOptions={{ exact: item.to === "/" }}
                  className="nav-item"
                  activeProps={{ className: "nav-item active" }}
                  onClick={() => setOpen(false)}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          {isAuthenticated && user ? (
            <div className="account-box">
              <span className="account-name">{user.display_name || user.email}</span>
              <span className="account-email">{user.email}</span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={async () => {
                  await logout();
                  navigate({ to: "/login" });
                }}
              >
                <LogOut className="w-3.5 h-3.5" /> Sign out
              </button>
            </div>
          ) : (
            <div className="account-box">
              <Link to="/login" className="btn btn-primary btn-sm">
                <LogIn className="w-3.5 h-3.5" /> Sign in
              </Link>
              <Link to="/register" className="auth-link">
                Create an account
              </Link>
            </div>
          )}
          <span className="stat-subtext">
            Smart data analysis, automated cleaning & predictive insights.
          </span>
        </div>
      </aside>

      <div className="main-viewport">
        <header className="topbar">
          <button className="icon-btn md-show" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="w-4 h-4" />
          </button>
          <div className="topbar-dataset">
            <Database className="w-3.5 h-3.5" style={{ color: "var(--accent-emerald)" }} />
            {datasets.length > 0 ? (
              <select
                className="dataset-select"
                value={activeDataset?.id ?? ""}
                onChange={(e) => selectDataset(e.target.value)}
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} {d.status !== "READY" ? `(${d.status})` : ""}
                  </option>
                ))}
              </select>
            ) : (
              <span className="stat-subtext">No dataset selected</span>
            )}
          </div>
          <span className="topbar-meta">
            {activeDataset
              ? `${(activeDataset.row_count ?? 0).toLocaleString()} rows · ${activeDataset.column_count ?? 0} columns`
              : "0 datasets loaded"}
          </span>
        </header>
        <main className="workspace-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

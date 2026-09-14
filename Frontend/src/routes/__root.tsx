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
import { ArrowRight, Lock, X } from "lucide-react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { DatasetProvider } from "@/context/DatasetContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { WorkspaceSidebar } from "@/components/layout/WorkspaceSidebar";
import { WorkspaceTopBar } from "@/components/layout/WorkspaceTopBar";
import { GlobalSearchModal } from "@/components/workspace/GlobalSearchModal";

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
    <div className="empty-state" style={{ marginTop: "3rem", padding: "2.5rem 1.5rem", maxWidth: "600px", margin: "3rem auto", textAlign: "center" }}>
      <div style={{ display: "inline-flex", padding: "1rem", borderRadius: "12px", background: "rgba(239, 68, 68, 0.1)", marginBottom: "1rem" }}>
        <X className="w-8 h-8" style={{ color: "#f87171" }} />
      </div>
      <div className="empty-state-title" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
        An unexpected error occurred
      </div>
      <div className="empty-state-desc" style={{ color: "var(--text-muted)", fontSize: "0.875rem", lineHeight: 1.6, marginBottom: "1.5rem" }}>
        {error.message || "A rendering or runtime exception interrupted this view. Details have been safely logged."}
      </div>
      <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
        <button
          className="btn btn-primary"
          onClick={() => {
            router.invalidate();
            reset();
          }}
        >
          Reload View
        </button>
        <a className="btn btn-secondary" href="/">
          Return Home
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
      { property: "og:site_name", content: "AnalyzaX" },
      { property: "og:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
      { property: "og:image:width", content: "1200" },
      { property: "og:image:height", content: "630" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: "https://analyzaxab-vp.vercel.app/og-image.png" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "canonical", href: "https://analyzaxab-vp.vercel.app/" },
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
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem("analyzax_sidebar_collapsed") === "true";
    } catch {
      return false;
    }
  });

  const toggleSidebarCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("analyzax_sidebar_collapsed", String(next));
      } catch {}
      return next;
    });
  };

  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Global Ctrl+K / Cmd+K search listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

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

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Modern Collapsible / Persistent Categorized Workspace Sidebar */}
      <WorkspaceSidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
      />

      {/* Main Viewport */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden bg-slate-950">
        {/* Global Top Bar */}
        <WorkspaceTopBar
          onToggleMobileSidebar={() => setIsMobileOpen(true)}
          onOpenSearch={() => setIsSearchOpen(true)}
        />

        {/* Main Workspace Content Area */}
        <main className="flex-1 overflow-y-auto bg-slate-900/30 focus:outline-none">
          {isAuthLoading && !isAuthenticated ? (
            <div style={{ padding: "2rem", width: "100%", maxWidth: "1200px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
                <div>
                  <div style={{ width: "240px", height: "32px", borderRadius: "8px", background: "rgba(255,255,255,0.08)", marginBottom: "0.5rem" }} />
                  <div style={{ width: "380px", height: "18px", borderRadius: "6px", background: "rgba(255,255,255,0.04)" }} />
                </div>
                <div style={{ width: "130px", height: "36px", borderRadius: "8px", background: "rgba(255,255,255,0.06)" }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} style={{ height: "110px", borderRadius: "12px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }} />
                ))}
              </div>
              <div style={{ height: "320px", borderRadius: "12px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }} />
            </div>
          ) : !isAuthenticated && !isLandingRoute ? (
            <div style={{ padding: "3.5rem 1.5rem", maxWidth: "680px", margin: "2rem auto", textAlign: "center" }}>
              <div style={{ display: "inline-flex", padding: "1rem", borderRadius: "16px", background: "rgba(99, 102, 241, 0.12)", border: "1px solid rgba(99, 102, 241, 0.3)", marginBottom: "1.25rem" }}>
                <Lock style={{ width: "36px", height: "36px", color: "#818cf8" }} />
              </div>
              <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.5rem", letterSpacing: "-0.02em" }}>
                Sign In to Access This Workspace
              </h2>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem", lineHeight: 1.6, marginBottom: "1.75rem" }}>
                This analytical engine requires an authenticated session. Sign in to run queries, view automated data profiling, and deploy models.
              </p>
              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center", flexWrap: "wrap", marginBottom: "2rem" }}>
                <Link to="/login" search={{ next: pathname }} className="btn btn-primary" style={{ padding: "0.65rem 1.5rem", display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
                  <span>Sign In to Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link to="/register" className="btn btn-secondary" style={{ padding: "0.65rem 1.5rem" }}>
                  Create Free Account
                </Link>
              </div>
              <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "1.5rem" }}>
                <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Want to explore first? <Link to="/" style={{ color: "var(--accent-indigo)", fontWeight: 500 }}>Explore demo on homepage &rarr;</Link>
                </p>
              </div>
            </div>
          ) : (
            <Outlet />
          )}
        </main>
      </div>

      <GlobalSearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </div>
  );
}

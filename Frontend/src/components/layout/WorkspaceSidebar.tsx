import React from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { AnalyzaXLogo } from "@/components/brand/AnalyzaXLogo";
import {
  Folder,
  LayoutDashboard,
  Lightbulb,
  Calculator,
  Database,
  ShieldCheck,
  Wand2,
  Microscope,
  Terminal,
  BarChart3,
  Sigma,
  FlaskConical,
  TrendingUp,
  Brain,
  Download,
  Settings,
  HelpCircle,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GettingStartedChecklist } from "./GettingStartedChecklist";

export interface NavEntry {
  label: string;
  to: string;
  icon: React.ElementType;
  badge?: string;
  isExternal?: boolean;
}

export interface NavCategory {
  title: string;
  items: NavEntry[];
}

export const SIDEBAR_CATEGORIES: NavCategory[] = [
  {
    title: "WORKSPACE",
    items: [
      { label: "Projects", to: "/projects", icon: Folder },
      { label: "Dashboard", to: "/", icon: LayoutDashboard },
      { label: "Insights", to: "/insights", icon: Lightbulb },
      { label: "Metrics", to: "/metrics", icon: Calculator },
    ],
  },
  {
    title: "DATA",
    items: [
      { label: "Dataset", to: "/data", icon: Database },
      { label: "Data Quality", to: "/quality", icon: ShieldCheck },
      { label: "Clean & Transform", to: "/cleaning", icon: Wand2 },
      { label: "EDA", to: "/eda", icon: Microscope },
    ],
  },
  {
    title: "ANALYZE",
    items: [
      { label: "SQL", to: "/sql", icon: Terminal },
      { label: "Visualizations", to: "/visualizations", icon: BarChart3 },
      { label: "Statistics", to: "/statistics", icon: Sigma },
      { label: "Machine Learning", to: "/ml", icon: FlaskConical },
      { label: "Forecasting", to: "/forecasting", icon: TrendingUp },
    ],
  },
  {
    title: "AI",
    items: [
      { label: "AI Analyst", to: "/ai-analyst", icon: Brain, badge: "AI" },
    ],
  },
  {
    title: "OUTPUT",
    items: [
      { label: "Exports", to: "/exports", icon: Download },
    ],
  },
  {
    title: "SYSTEM",
    items: [
      { label: "Settings", to: "/settings", icon: Settings },
      { label: "Documentation & Help", to: "https://github.com/beniwalravi1937-coder/AnalyzaX#readme", icon: HelpCircle, isExternal: true },
    ],
  },
];

interface WorkspaceSidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  className?: string;
}

export const WorkspaceSidebar: React.FC<WorkspaceSidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
  className,
}) => {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { user, isAuthenticated, logout } = useAuth();

  const isRouteActive = (itemTo: string) => {
    if (itemTo === "/") return pathname === "/";
    return pathname === itemTo || pathname.startsWith(`${itemTo}/`);
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-950/95 border-r border-slate-800/80 select-none">
      {/* Brand Header */}
      <div className={cn(
        "flex items-center h-14 px-4 border-b border-slate-800/80 shrink-0",
        isCollapsed ? "justify-center px-2" : "justify-between"
      )}>
        <Link
          to="/"
          onClick={onCloseMobile}
          className="flex items-center gap-2.5 overflow-hidden transition-opacity hover:opacity-90"
        >
          <AnalyzaXLogo size={26} showText={!isCollapsed} />
        </Link>

        {/* Mobile close button */}
        <button
          onClick={onCloseMobile}
          className="md:hidden p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          aria-label="Close sidebar"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Desktop toggle button */}
        <button
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/60 transition-colors"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-slate-400" />
          )}
        </button>
      </div>

      {/* Navigation Body */}
      <nav className="sidebar-nav flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-4 no-scrollbar flex flex-col" aria-label="Primary Workspace Navigation">
        <TooltipProvider delayDuration={150}>
          {/* Getting Started Onboarding Checklist */}
          <div className="mb-2 relative z-10 block opacity-100 visible shrink-0 w-full">
            <GettingStartedChecklist isCollapsed={isCollapsed} />
          </div>

          {SIDEBAR_CATEGORIES.map((category) => (
            <div key={category.title} className="space-y-0.5">
              {!isCollapsed ? (
                <div className="px-2.5 py-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-mono">
                  {category.title}
                </div>
              ) : (
                <div className="h-2" />
              )}

              {category.items.map((item) => {
                const active = !item.isExternal && isRouteActive(item.to);
                const Icon = item.icon;

                const linkElement = item.isExternal ? (
                  <a
                    key={item.label}
                    href={item.to}
                    target="_blank"
                    rel="noreferrer noopener"
                    className={cn(
                      "group relative flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors",
                      isCollapsed ? "justify-center px-0 h-9 w-9 mx-auto" : "h-8.5",
                      "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
                    )}
                  >
                    <Icon className="w-4 h-4 shrink-0 text-slate-400 group-hover:text-slate-200 transition-colors" />
                    {!isCollapsed && <span className="truncate">{item.label}</span>}
                  </a>
                ) : (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={onCloseMobile}
                    className={cn(
                      "group relative flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors",
                      isCollapsed ? "justify-center px-0 h-9 w-9 mx-auto" : "h-8.5",
                      active
                        ? "bg-indigo-500/10 text-white font-semibold"
                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
                    )}
                  >
                    {/* Small accent indicator bar for active item */}
                    {active && (
                      <span className={cn(
                        "absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-md bg-indigo-500",
                        isCollapsed && "left-0 top-2 bottom-2 w-0.5"
                      )} />
                    )}

                    <Icon
                      className={cn(
                        "w-4 h-4 shrink-0 transition-colors",
                        active
                          ? "text-indigo-400"
                          : "text-slate-400 group-hover:text-slate-200"
                      )}
                    />

                    {!isCollapsed && (
                      <>
                        <span className="truncate flex-1">{item.label}</span>
                        {item.badge && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                );

                if (isCollapsed) {
                  return (
                    <Tooltip key={item.label}>
                      <TooltipTrigger asChild>{linkElement}</TooltipTrigger>
                      <TooltipContent side="right" className="bg-slate-900 border-slate-700 text-xs text-white">
                        <div className="flex items-center gap-1.5">
                          <span>{item.label}</span>
                          {item.badge && (
                            <span className="px-1 rounded text-[9px] bg-indigo-500/20 text-indigo-300">
                              {item.badge}
                            </span>
                          )}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                return linkElement;
              })}
            </div>
          ))}
        </TooltipProvider>
      </nav>

      {/* Sidebar Footer: System Status & Bottom-most Session Management */}
      <div className={cn(
        "p-2.5 border-t border-slate-800/80 shrink-0 text-slate-500 text-[11px] flex flex-col gap-2 bg-slate-950/80",
        isCollapsed ? "items-center px-1" : ""
      )}>
        {/* Engine status indicator */}
        {!isCollapsed && (
          <div className="flex items-center justify-between px-1 text-[10px] text-slate-500 font-mono">
            <span>AnalyzaX Engine</span>
            <span>v1.0 · DuckDB</span>
          </div>
        )}

        {/* Bottom-most Session Management */}
        {isAuthenticated && user && (
          isCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={logout}
                  aria-label="Sign out"
                  className="flex items-center justify-center h-8 w-8 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800/60 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-slate-900 border-slate-700 text-xs text-white">
                Sign out ({user.email})
              </TooltipContent>
            </Tooltip>
          ) : (
            <div className="flex items-center justify-between gap-2 p-1.5 rounded-lg bg-slate-900/60 border border-slate-800/60">
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-xs font-medium text-slate-300 truncate">
                  {user.display_name || user.email?.split("@")[0]}
                </span>
                <span className="text-[10px] text-slate-500 truncate font-mono">
                  {user.email}
                </span>
              </div>
              <button
                type="button"
                onClick={logout}
                aria-label="Sign out of AnalyzaX"
                title="Sign out"
                className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
              >
                <LogOut className="w-3 h-3" />
                <span>Sign out</span>
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop & Tablet Persistent / Collapsible Sidebar */}
      <aside
        className={cn(
          "hidden md:block shrink-0 transition-all duration-200 ease-in-out z-30 h-screen sticky top-0",
          isCollapsed ? "w-16" : "w-60 lg:w-64",
          className
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Slide-Over Drawer with Backdrop */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
            onClick={onCloseMobile}
          />
          <div className="fixed inset-y-0 left-0 w-64 max-w-[85vw] shadow-2xl animate-in slide-in-from-left duration-200 z-50">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};

export default WorkspaceSidebar;

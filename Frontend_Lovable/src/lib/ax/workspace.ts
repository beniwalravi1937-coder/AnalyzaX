/* Browser-local workspace: projects, activity and notifications. */

import { uid } from "./profile";

export type Env = "PRODUCTION" | "STAGING";
export type AssetType = "DATASET" | "DASHBOARD" | "REPORT" | "QUERY" | "EXPORT";

export interface WorkspaceAsset {
  id: string;
  name: string;
  type: AssetType;
  createdAt: number;
  note?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  env: Env;
  archived: boolean;
  createdAt: number;
  updatedAt: number;
  assets: WorkspaceAsset[];
  activity: ActivityRecord[];
}

export interface ActivityRecord {
  id: string;
  at: number;
  actor: string;
  action: string;
  detail?: string;
}

export type NotificationCategory =
  | "DATA"
  | "ANALYSIS"
  | "QUALITY"
  | "PROJECT"
  | "EXPORT"
  | "SYSTEM";
export type NotificationPriority = "CRITICAL" | "HIGH" | "NORMAL" | "LOW";

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  at: number;
  read: boolean;
  link?: string;
}

const PROJECTS_KEY = "analyzax.projects.v1";
const NOTIFICATIONS_KEY = "analyzax.notifications.v1";

function read<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write<T>(key: string, value: T) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* quota */
  }
}

/* -------------------------------- projects -------------------------------- */

function seedProjects(): Project[] {
  const now = Date.now();
  const day = 86_400_000;
  const p: Project = {
    id: uid("prj"),
    name: "Revenue Analytics",
    description: "Default workspace for the dataset loaded in this browser.",
    env: "PRODUCTION",
    archived: false,
    createdAt: now - 12 * day,
    updatedAt: now - day,
    assets: [
      { id: uid("as"), name: "sample_sales_2025.csv", type: "DATASET", createdAt: now - 12 * day },
      { id: uid("as"), name: "Executive overview", type: "DASHBOARD", createdAt: now - 9 * day },
      { id: uid("as"), name: "Top segments query", type: "QUERY", createdAt: now - 4 * day },
      { id: uid("as"), name: "Quality summary.md", type: "REPORT", createdAt: now - day },
    ],
    activity: [
      { id: uid("ac"), at: now - day, actor: "You", action: "Generated quality report" },
      { id: uid("ac"), at: now - 4 * day, actor: "You", action: "Saved SQL query", detail: "Top segments" },
      { id: uid("ac"), at: now - 12 * day, actor: "You", action: "Created project" },
    ],
  };
  return [p];
}

export function loadProjects(): Project[] {
  const existing = read<Project[] | null>(PROJECTS_KEY, null);
  if (existing && existing.length) return existing;
  const seeded = seedProjects();
  write(PROJECTS_KEY, seeded);
  return seeded;
}

export function saveProjects(projects: Project[]) {
  write(PROJECTS_KEY, projects);
}

export function createProject(name: string, description: string, env: Env): Project {
  const now = Date.now();
  return {
    id: uid("prj"),
    name,
    description,
    env,
    archived: false,
    createdAt: now,
    updatedAt: now,
    assets: [],
    activity: [{ id: uid("ac"), at: now, actor: "You", action: "Created project" }],
  };
}

export function duplicateProject(p: Project): Project {
  const now = Date.now();
  return {
    ...p,
    id: uid("prj"),
    name: `${p.name} (copy)`,
    createdAt: now,
    updatedAt: now,
    assets: p.assets.map((a) => ({ ...a, id: uid("as") })),
    activity: [{ id: uid("ac"), at: now, actor: "You", action: "Duplicated project", detail: p.name }],
  };
}

export function logActivity(p: Project, action: string, detail?: string): Project {
  return {
    ...p,
    updatedAt: Date.now(),
    activity: [{ id: uid("ac"), at: Date.now(), actor: "You", action, detail }, ...p.activity].slice(0, 50),
  };
}

export function projectHealth(p: Project): { score: number; label: string; notes: string[] } {
  const notes: string[] = [];
  let score = 100;
  if (!p.assets.some((a) => a.type === "DATASET")) {
    score -= 35;
    notes.push("No dataset attached to this project.");
  }
  if (!p.assets.some((a) => a.type === "DASHBOARD" || a.type === "REPORT")) {
    score -= 20;
    notes.push("No dashboard or report produced yet.");
  }
  const stale = Date.now() - p.updatedAt > 14 * 86_400_000;
  if (stale) {
    score -= 15;
    notes.push("No activity in the last 14 days.");
  }
  if (!p.description) {
    score -= 10;
    notes.push("Missing a description for teammates.");
  }
  score = Math.max(0, score);
  const label = score >= 85 ? "Healthy" : score >= 60 ? "Needs attention" : "At risk";
  return { score, label, notes };
}

/* ----------------------------- notifications ------------------------------ */

export function loadNotifications(): AppNotification[] {
  return read<AppNotification[]>(NOTIFICATIONS_KEY, []);
}

export function saveNotifications(list: AppNotification[]) {
  write(NOTIFICATIONS_KEY, list);
}

export function makeNotification(
  n: Omit<AppNotification, "id" | "at" | "read"> & { at?: number },
): AppNotification {
  return { id: uid("nt"), at: n.at ?? Date.now(), read: false, ...n };
}

export function mergeNotifications(
  existing: AppNotification[],
  generated: AppNotification[],
): AppNotification[] {
  const keyOf = (n: AppNotification) => `${n.category}|${n.title}`;
  const byKey = new Map(existing.map((n) => [keyOf(n), n]));
  const merged = [...existing];
  for (const g of generated) {
    if (!byKey.has(keyOf(g))) merged.push(g);
  }
  return merged.sort((a, b) => b.at - a.at).slice(0, 60);
}

export const timeAgo = (ts: number) => {
  const s = Math.max(1, Math.round((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
};

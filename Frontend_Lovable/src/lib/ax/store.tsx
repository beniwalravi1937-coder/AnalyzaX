import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { uid } from "./profile";
import { SAMPLE_COLUMNS, buildSampleRows } from "./sample";
import type { Dataset, DatasetVersion, Row, TransformStep } from "./types";

const STORAGE_KEY = "analyzax.workspace.v1";

interface Workspace {
  datasets: Dataset[];
  activeId: string | null;
}

function makeDataset(name: string, columns: string[], rows: Row[]): Dataset {
  const version: DatasetVersion = {
    id: "v1",
    label: "v1 · raw",
    createdAt: Date.now(),
    steps: [],
    columns,
    rows,
  };
  return {
    id: uid("ds"),
    name,
    createdAt: Date.now(),
    columns,
    versions: [version],
    activeVersionId: "v1",
  };
}

function seedWorkspace(): Workspace {
  const ds = makeDataset("sample_sales_2025.csv", SAMPLE_COLUMNS, buildSampleRows());
  return { datasets: [ds], activeId: ds.id };
}

interface Ctx {
  ready: boolean;
  datasets: Dataset[];
  activeDataset: Dataset | null;
  activeVersion: DatasetVersion | null;
  columns: string[];
  rows: Row[];
  setActiveDataset: (id: string) => void;
  setActiveVersion: (versionId: string) => void;
  addDataset: (name: string, columns: string[], rows: Row[]) => void;
  removeDataset: (id: string) => void;
  commitVersion: (steps: TransformStep[], columns: string[], rows: Row[]) => DatasetVersion | null;
  resetToSample: () => void;
}

// Share a single context instance across duplicate module copies (HMR / code splitting),
// otherwise a consumer can hold a different context object than the provider.
const globalStore = globalThis as unknown as { __analyzaxDatasetContext?: React.Context<Ctx | null> };
const DatasetContext: React.Context<Ctx | null> =
  globalStore.__analyzaxDatasetContext ?? createContext<Ctx | null>(null);
globalStore.__analyzaxDatasetContext = DatasetContext;


export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [ws, setWs] = useState<Workspace>({ datasets: [], activeId: null });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Workspace;
        if (parsed?.datasets?.length) {
          setWs(parsed);
          setReady(true);
          return;
        }
      }
    } catch {
      /* ignore corrupted storage */
    }
    setWs(seedWorkspace());
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ws));
    } catch {
      /* quota exceeded — keep working in memory */
    }
  }, [ws, ready]);

  const activeDataset = useMemo(
    () => ws.datasets.find((d) => d.id === ws.activeId) ?? ws.datasets[0] ?? null,
    [ws],
  );
  const activeVersion = useMemo(
    () =>
      activeDataset
        ? activeDataset.versions.find((v) => v.id === activeDataset.activeVersionId) ??
          activeDataset.versions[0]
        : null,
    [activeDataset],
  );

  const setActiveDataset = useCallback((id: string) => {
    setWs((w) => ({ ...w, activeId: id }));
  }, []);

  const setActiveVersion = useCallback((versionId: string) => {
    setWs((w) => ({
      ...w,
      datasets: w.datasets.map((d) =>
        d.id === (w.activeId ?? w.datasets[0]?.id) ? { ...d, activeVersionId: versionId } : d,
      ),
    }));
  }, []);

  const addDataset = useCallback((name: string, columns: string[], rows: Row[]) => {
    const ds = makeDataset(name, columns, rows);
    setWs((w) => ({ datasets: [ds, ...w.datasets], activeId: ds.id }));
  }, []);

  const removeDataset = useCallback((id: string) => {
    setWs((w) => {
      const datasets = w.datasets.filter((d) => d.id !== id);
      return { datasets, activeId: w.activeId === id ? (datasets[0]?.id ?? null) : w.activeId };
    });
  }, []);

  const commitVersion = useCallback(
    (steps: TransformStep[], columns: string[], rows: Row[]) => {
      if (!activeDataset) return null;
      const version: DatasetVersion = {
        id: `v${activeDataset.versions.length + 1}`,
        label: `v${activeDataset.versions.length + 1} · ${steps.length} step${steps.length === 1 ? "" : "s"}`,
        createdAt: Date.now(),
        steps,
        columns,
        rows,
      };
      setWs((w) => ({
        ...w,
        datasets: w.datasets.map((d) =>
          d.id === activeDataset.id
            ? { ...d, versions: [...d.versions, version], activeVersionId: version.id }
            : d,
        ),
      }));
      return version;
    },
    [activeDataset],
  );

  const resetToSample = useCallback(() => setWs(seedWorkspace()), []);

  const value: Ctx = {
    ready,
    datasets: ws.datasets,
    activeDataset,
    activeVersion,
    columns: activeVersion?.columns ?? [],
    rows: activeVersion?.rows ?? [],
    setActiveDataset,
    setActiveVersion,
    addDataset,
    removeDataset,
    commitVersion,
    resetToSample,
  };

  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>;
}

export function useDataset(): Ctx {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error("useDataset must be used inside DatasetProvider");
  return ctx;
}

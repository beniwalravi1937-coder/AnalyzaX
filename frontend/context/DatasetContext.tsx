"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { DatasetResponse } from "@/types";
import { apiClient } from "@/services/api";

interface DatasetContextValue {
  datasets: DatasetResponse[];
  activeDataset: DatasetResponse | null;
  isLoading: boolean;
  error: string | null;
  selectDataset: (datasetId: string) => void;
  refreshDatasets: () => Promise<void>;
  deleteDataset: (datasetId: string) => Promise<void>;
}

const DatasetContext = createContext<DatasetContextValue | undefined>(undefined);

const STORAGE_KEY = "analyzax_active_dataset_id";

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [activeDataset, setActiveDataset] = useState<DatasetResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshDatasets = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await apiClient.listDatasets();
      const list = res.datasets || [];
      setDatasets(list);

      // Re-evaluate active dataset
      const savedId = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
      let matched = list.find((d) => d.id === savedId);

      if (!matched && list.length > 0) {
        // Fallback to the latest ready dataset or first item
        matched = list.find((d) => d.status === "READY") || list[0];
      }

      if (matched) {
        setActiveDataset(matched);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, matched.id);
        }
      } else {
        setActiveDataset(null);
        if (typeof window !== "undefined") {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
    } catch (err: any) {
      console.warn("Could not fetch datasets from backend:", err);
      setError(err?.message || "Failed to load datasets.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  const selectDataset = useCallback(
    (datasetId: string) => {
      const found = datasets.find((d) => d.id === datasetId);
      if (found) {
        setActiveDataset(found);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, found.id);
        }
      }
    },
    [datasets]
  );

  const deleteDataset = useCallback(
    async (datasetId: string) => {
      try {
        await apiClient.deleteDataset(datasetId);
        await refreshDatasets();
      } catch (err: any) {
        console.error("Failed to delete dataset:", err);
        throw err;
      }
    },
    [refreshDatasets]
  );

  return (
    <DatasetContext.Provider
      value={{
        datasets,
        activeDataset,
        isLoading,
        error,
        selectDataset,
        refreshDatasets,
        deleteDataset,
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
}

export function useDataset(): DatasetContextValue {
  const context = useContext(DatasetContext);
  if (!context) {
    throw new Error("useDataset must be used within a DatasetProvider");
  }
  return context;
}

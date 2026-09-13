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
  loadSampleDataset: () => Promise<DatasetResponse | null>;
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

  const loadSampleDataset = useCallback(async (): Promise<DatasetResponse | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if sample dataset already exists
      const existing = datasets.find(
        (d) =>
          d.name?.toLowerCase().includes("sample") ||
          d.original_filename?.toLowerCase().includes("sample")
      );
      if (existing) {
        setActiveDataset(existing);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, existing.id);
        }
        return existing;
      }

      // Fetch sample CSV or fallback
      let csvText = "";
      try {
        const resp = await fetch("/sample-datasets/ecommerce_sales_sample.csv");
        if (resp.ok) {
          csvText = await resp.text();
        }
      } catch (fetchErr) {
        console.warn("Could not fetch sample CSV asset, using embedded fallback:", fetchErr);
      }

      if (!csvText || !csvText.includes("order_id")) {
        csvText = `order_id,order_date,customer_segment,region,category,sub_category,sales,profit,discount,quantity,rating,customer_churned
ORD-1001,2024-01-15,Consumer,North America,Technology,Phones,850.50,210.20,0.05,2,4.8,0
ORD-1002,2024-01-18,Corporate,Europe,Office Supplies,Binders,45.20,12.50,0.00,5,4.2,0
ORD-1003,2024-01-22,Home Office,Asia Pacific,Furniture,Chairs,320.00,-45.00,0.20,1,3.5,1
ORD-1004,2024-02-05,Consumer,North America,Technology,Accessories,120.00,38.40,0.10,3,4.6,0
ORD-1005,2024-02-12,Corporate,Latin America,Office Supplies,Paper,28.90,9.10,0.00,4,4.0,0
ORD-1006,2024-02-20,Consumer,Europe,Furniture,Tables,650.00,-110.00,0.25,1,2.9,1
ORD-1007,2024-03-02,Home Office,North America,Technology,Machines,1250.00,340.00,0.05,1,4.9,0
ORD-1008,2024-03-10,Corporate,Asia Pacific,Furniture,Bookcases,290.00,42.00,0.15,2,3.8,0
ORD-1009,2024-03-15,Consumer,Latin America,Office Supplies,Appliances,180.50,52.20,0.10,2,4.4,0
ORD-1010,2024-03-28,Home Office,Europe,Technology,Phones,920.00,245.00,0.00,1,4.7,0`;
      }

      const sampleFile = new File([csvText], "Sample_Retail_Analytics.csv", { type: "text/csv" });
      const uploaded = await apiClient.uploadDataset(sampleFile);

      // Refresh list
      const res = await apiClient.listDatasets();
      const updatedList = res.datasets || [];
      setDatasets(updatedList);

      const target = updatedList.find((d) => d.id === uploaded.dataset_id) || updatedList[0] || null;
      if (target) {
        setActiveDataset(target);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, target.id);
        }
      }
      return target;
    } catch (err: any) {
      console.error("Failed to load sample dataset:", err);
      setError(err?.message || "Failed to load sample dataset.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [datasets]);

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
        loadSampleDataset,
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

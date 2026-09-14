"use client";

import { useEffect, useState } from "react";
import { type HealthStatus, apiClient } from "@/services/api";

type ConnectionState = "connecting" | "connected" | "disconnected";

interface SystemStatus {
  connection: ConnectionState;
  health: HealthStatus | null;
  lastChecked: Date | null;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useBackendHealth(pollIntervalMs = 15_000): SystemStatus {
  const [status, setStatus] = useState<Omit<SystemStatus, "refetch">>({
    connection: "connecting",
    health: null,
    lastChecked: null,
    error: null,
  });

  const checkHealth = async () => {
    try {
      const health = await apiClient.getHealth();
      setStatus({
        connection: "connected",
        health,
        lastChecked: new Date(),
        error: null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setStatus((prev) => ({
        ...prev,
        connection: "disconnected",
        error: message,
        lastChecked: new Date(),
      }));
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [pollIntervalMs]);

  return {
    ...status,
    refetch: checkHealth,
  };
}

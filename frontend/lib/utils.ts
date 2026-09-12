/**
 * Frontend utility helpers.
 * Business logic must NOT live here — it belongs in the backend.
 */

/**
 * Capitalizes the first letter of a string.
 */
export function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Returns a user-friendly label for a backend database status string.
 */
export function formatDbStatus(status: string): string {
  const map: Record<string, string> = {
    connected: "Connected",
    configured: "Configured",
    not_configured: "Not Configured",
  };
  return map[status] ?? capitalize(status);
}

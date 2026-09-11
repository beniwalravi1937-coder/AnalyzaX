"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { DatasetProvider } from "@/context/DatasetContext";
import { WorkspaceProvider } from "@/context/WorkspaceContext";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <ProtectedRoute>
      <WorkspaceProvider>
        <DatasetProvider>
          <div className="app-shell">
            {/* Collapsible / Responsive Sidebar */}
            <Sidebar
              isOpen={isSidebarOpen}
              onClose={() => setIsSidebarOpen(false)}
            />

            {/* Main Viewport */}
            <div className="main-viewport">
              <TopBar
                onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
              />
              <main className="workspace-container">{children}</main>
            </div>
          </div>
        </DatasetProvider>
      </WorkspaceProvider>
    </ProtectedRoute>
  );
}


'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { Workspace, Project } from '../types/workspace';
import { workspaceApi } from '../services/workspaceApi';

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  projects: Project[];
  activeProject: Project | null;
  isLoading: boolean;
  setActiveWorkspace: (ws: Workspace) => void;
  setActiveProject: (proj: Project) => void;
  refreshWorkspaces: () => Promise<void>;
  refreshProjects: () => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
  archiveProject: (projectId: string) => Promise<void>;
  restoreProject: (projectId: string) => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProjectState] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load workspaces on initial mount
  const refreshWorkspaces = useCallback(async () => {
    try {
      const list = await workspaceApi.getWorkspaces(true);
      setWorkspaces(list);

      const savedWsId = typeof window !== 'undefined' ? localStorage.getItem('analyzax_active_workspace_id') : null;
      let matchedWs = list.find((w) => w.workspace_id === savedWsId);
      if (!matchedWs && list.length > 0) {
        matchedWs = list.find((w) => w.status === 'ACTIVE') || list[0];
      }
      if (matchedWs) {
        setActiveWorkspaceState(matchedWs);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  }, []);

  // Load projects for active workspace
  const refreshProjects = useCallback(async () => {
    if (!activeWorkspace) return;
    try {
      const list = await workspaceApi.getProjects(activeWorkspace.workspace_id, true);
      setProjects(list);

      const savedProjId = typeof window !== 'undefined' ? localStorage.getItem('analyzax_active_project_id') : null;
      let matchedProj = list.find((p) => p.project_id === savedProjId);
      if (!matchedProj && list.length > 0) {
        matchedProj = list.find((p) => p.status === 'ACTIVE') || list[0];
      }
      if (matchedProj) {
        setActiveProjectState(matchedProj);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  }, [activeWorkspace]);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await refreshWorkspaces();
      setIsLoading(false);
    };
    init();
  }, [refreshWorkspaces]);

  useEffect(() => {
    if (activeWorkspace) {
      refreshProjects();
    }
  }, [activeWorkspace, refreshProjects]);

  const setActiveWorkspace = (ws: Workspace) => {
    setActiveWorkspaceState(ws);
    if (typeof window !== 'undefined') {
      localStorage.setItem('analyzax_active_workspace_id', ws.workspace_id);
    }
  };

  const setActiveProject = (proj: Project) => {
    setActiveProjectState(proj);
    if (typeof window !== 'undefined') {
      localStorage.setItem('analyzax_active_project_id', proj.project_id);
    }
  };

  const createProject = async (name: string, description?: string): Promise<Project> => {
    if (!activeWorkspace) throw new Error('No active workspace selected');
    const created = await workspaceApi.createProject(activeWorkspace.workspace_id, name, description);
    await refreshProjects();
    setActiveProject(created);
    return created;
  };

  const archiveProject = async (projectId: string) => {
    await workspaceApi.archiveProject(projectId);
    await refreshProjects();
  };

  const restoreProject = async (projectId: string) => {
    await workspaceApi.restoreProject(projectId);
    await refreshProjects();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        projects,
        activeProject,
        isLoading,
        setActiveWorkspace,
        setActiveProject,
        refreshWorkspaces,
        refreshProjects,
        createProject,
        archiveProject,
        restoreProject,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = (): WorkspaceContextType => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};

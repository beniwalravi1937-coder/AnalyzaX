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

const DEFAULT_WORKSPACE: Workspace = {
  workspace_id: 'ws_default',
  name: 'AnalyzaX Production Workspace',
  slug: 'analyzax-production-workspace',
  description: 'Primary production analytical workspace',
  status: 'ACTIVE',
  owner_id: 'usr_default',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  settings: {
    enforce_two_factor: false,
    allowed_ip_ranges: [],
    session_timeout_minutes: 1440,
    retention_days: 90,
  },
};

const DEFAULT_PROJECT: Project = {
  project_id: 'proj_default',
  workspace_id: 'ws_default',
  name: 'Default Analytical Project',
  slug: 'default-analytical-project',
  description: 'Primary project for datasets, notebooks, and models',
  status: 'ACTIVE',
  visibility: 'PRIVATE',
  created_by: 'usr_default',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([DEFAULT_WORKSPACE]);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(DEFAULT_WORKSPACE);
  const [projects, setProjects] = useState<Project[]>([DEFAULT_PROJECT]);
  const [activeProject, setActiveProjectState] = useState<Project | null>(DEFAULT_PROJECT);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load workspaces on initial mount
  const refreshWorkspaces = useCallback(async () => {
    try {
      const list = await workspaceApi.getWorkspaces(true);
      if (!list || list.length === 0) {
        setWorkspaces([DEFAULT_WORKSPACE]);
        setActiveWorkspaceState(DEFAULT_WORKSPACE);
      } else {
        setWorkspaces(list);
        const savedWsId = typeof window !== 'undefined' ? localStorage.getItem('analyzax_active_workspace_id') : null;
        let matchedWs = list.find((w) => w.workspace_id === savedWsId);
        if (!matchedWs && list.length > 0) {
          matchedWs = list.find((w) => w.status === 'ACTIVE') || list[0];
        }
        if (matchedWs) {
          setActiveWorkspaceState(matchedWs);
        }
      }
    } catch (err) {
      console.warn('Backend workspaces unavailable, using default workspace:', err);
      setWorkspaces([DEFAULT_WORKSPACE]);
      setActiveWorkspaceState(DEFAULT_WORKSPACE);
    }
  }, []);

  // Load projects for active workspace
  const refreshProjects = useCallback(async () => {
    const wsId = activeWorkspace?.workspace_id || 'ws_default';
    try {
      const list = await workspaceApi.getProjects(wsId, true);
      if (!list || list.length === 0) {
        setProjects([DEFAULT_PROJECT]);
        setActiveProjectState(DEFAULT_PROJECT);
      } else {
        setProjects(list);
        const savedProjId = typeof window !== 'undefined' ? localStorage.getItem('analyzax_active_project_id') : null;
        let matchedProj = list.find((p) => p.project_id === savedProjId);
        if (!matchedProj && list.length > 0) {
          matchedProj = list.find((p) => p.status === 'ACTIVE') || list[0];
        }
        if (matchedProj) {
          setActiveProjectState(matchedProj);
        }
      }
    } catch (err) {
      console.warn('Backend projects unavailable, using default project:', err);
      setProjects([DEFAULT_PROJECT]);
      setActiveProjectState(DEFAULT_PROJECT);
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

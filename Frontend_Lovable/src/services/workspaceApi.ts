import {
  Workspace,
  Project,
  Asset,
  AssetRelationship,
  ActivityRecord,
  ProjectHealth,
  DependencySummary,
  LineageGraph,
  DatasetVersionComparisonResult,
  SearchResponse,
  RelationshipType,
} from '../types/workspace';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const workspaceApi = {
  // ── Workspaces ──
  async getWorkspaces(includeArchived: boolean = false): Promise<Workspace[]> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces?include_archived=${includeArchived}`);
    return handleResponse<Workspace[]>(res);
  },

  async createWorkspace(name: string, description?: string): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    return handleResponse<Workspace>(res);
  },

  async archiveWorkspace(workspaceId: string): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/archive`, {
      method: 'POST',
    });
    return handleResponse<Workspace>(res);
  },

  async restoreWorkspace(workspaceId: string): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/restore`, {
      method: 'POST',
    });
    return handleResponse<Workspace>(res);
  },

  // ── Projects ──
  async getProjects(workspaceId: string, includeArchived: boolean = false): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/projects?include_archived=${includeArchived}`);
    return handleResponse<Project[]>(res);
  },

  async getProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`);
    return handleResponse<Project>(res);
  },

  async createProject(workspaceId: string, name: string, description?: string, icon?: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/workspaces/${workspaceId}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, icon }),
    });
    return handleResponse<Project>(res);
  },

  async updateProject(projectId: string, updates: { name?: string; description?: string; icon?: string }): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return handleResponse<Project>(res);
  },

  async archiveProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/archive`, {
      method: 'POST',
    });
    return handleResponse<Project>(res);
  },

  async restoreProject(projectId: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/restore`, {
      method: 'POST',
    });
    return handleResponse<Project>(res);
  },

  async duplicateProject(projectId: string, newName?: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName, copy_configuration_only: true }),
    });
    return handleResponse<Project>(res);
  },

  async deleteProject(projectId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async getProjectHealth(projectId: string): Promise<ProjectHealth> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/health`);
    return handleResponse<ProjectHealth>(res);
  },

  async getProjectActivity(projectId: string, limit: number = 30): Promise<ActivityRecord[]> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/activity?limit=${limit}`);
    return handleResponse<ActivityRecord[]>(res);
  },

  async exportProjectManifest(projectId: string): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/export-manifest`);
    return handleResponse<Record<string, any>>(res);
  },

  // ── Assets ──
  async getAssets(
    projectId: string,
    params?: {
      asset_type?: string;
      status?: string;
      is_favorite?: boolean;
      tag?: string;
      page?: number;
      page_size?: number;
    }
  ): Promise<{ assets: Asset[]; total: number; page: number; page_size: number }> {
    const query = new URLSearchParams();
    if (params?.asset_type) query.set('asset_type', params.asset_type);
    if (params?.status) query.set('status', params.status);
    if (params?.is_favorite !== undefined) query.set('is_favorite', String(params.is_favorite));
    if (params?.tag) query.set('tag', params.tag);
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));

    const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/assets?${query.toString()}`);
    return handleResponse<{ assets: Asset[]; total: number; page: number; page_size: number }>(res);
  },

  async getAsset(assetId: string): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}`);
    return handleResponse<Asset>(res);
  },

  async updateAsset(assetId: string, updates: { name?: string; description?: string; tags?: string[] }): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return handleResponse<Asset>(res);
  },

  async favoriteAsset(assetId: string): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/favorite`, {
      method: 'POST',
    });
    return handleResponse<Asset>(res);
  },

  async unfavoriteAsset(assetId: string): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/favorite`, {
      method: 'DELETE',
    });
    return handleResponse<Asset>(res);
  },

  async archiveAsset(assetId: string): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/archive`, {
      method: 'POST',
    });
    return handleResponse<Asset>(res);
  },

  async restoreAsset(assetId: string): Promise<Asset> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/restore`, {
      method: 'POST',
    });
    return handleResponse<Asset>(res);
  },

  async deleteAsset(assetId: string, force: boolean = false): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}?force=${force}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async getAssetDependencies(assetId: string): Promise<DependencySummary> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/dependencies`);
    return handleResponse<DependencySummary>(res);
  },

  async getAssetLineage(assetId: string): Promise<LineageGraph> {
    const res = await fetch(`${API_BASE}/api/v1/assets/${assetId}/lineage`);
    return handleResponse<LineageGraph>(res);
  },

  async createRelationship(sourceAssetId: string, targetAssetId: string, relationshipType: RelationshipType): Promise<AssetRelationship> {
    const res = await fetch(`${API_BASE}/api/v1/assets/relationships`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_asset_id: sourceAssetId,
        target_asset_id: targetAssetId,
        relationship_type: relationshipType,
      }),
    });
    return handleResponse<AssetRelationship>(res);
  },

  // ── Global & Project Search ──
  async searchAssets(params: {
    q: string;
    project_id?: string;
    workspace_id?: string;
    asset_type?: string;
    status?: string;
    is_favorite?: boolean;
    tag?: string;
    sort_by?: string;
    sort_desc?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> {
    const query = new URLSearchParams();
    query.set('q', params.q);
    if (params.project_id) query.set('project_id', params.project_id);
    if (params.workspace_id) query.set('workspace_id', params.workspace_id);
    if (params.asset_type) query.set('asset_type', params.asset_type);
    if (params.status) query.set('status', params.status);
    if (params.is_favorite !== undefined) query.set('is_favorite', String(params.is_favorite));
    if (params.tag) query.set('tag', params.tag);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_desc !== undefined) query.set('sort_desc', String(params.sort_desc));
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));

    const res = await fetch(`${API_BASE}/api/v1/search?${query.toString()}`);
    return handleResponse<SearchResponse>(res);
  },

  // ── Dataset Versions & Comparison ──
  async compareDatasetVersionsMetadata(datasetId: string, before: string, after: string): Promise<DatasetVersionComparisonResult> {
    const res = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/versions/compare?before=${before}&after=${after}`);
    return handleResponse<DatasetVersionComparisonResult>(res);
  },

  async archiveDataset(datasetId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/archive`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async restoreDataset(datasetId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/restore`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },
};

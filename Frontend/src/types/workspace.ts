/**
 * Workspace, Project & Asset Organization Types for Phase 16
 */

export type WorkspaceStatus = 'ACTIVE' | 'ARCHIVED';
export type ProjectStatus = 'ACTIVE' | 'ARCHIVED';

export type AssetType =
  | 'DATASET'
  | 'DATASET_VERSION'
  | 'VISUALIZATION'
  | 'QUERY'
  | 'STATISTICAL_ANALYSIS'
  | 'ML_EXPERIMENT'
  | 'ML_RESULT'
  | 'FORECAST_EXPERIMENT'
  | 'FORECAST_RESULT'
  | 'AI_SESSION'
  | 'DASHBOARD'
  | 'REPORT'
  | 'EXPORT';

export type AssetStatus = 'ACTIVE' | 'ARCHIVED' | 'DELETED';

export type RelationshipType =
  | 'DERIVED_FROM'
  | 'USES'
  | 'CONTAINS'
  | 'REFERENCES'
  | 'GENERATED_FROM'
  | 'VISUALIZES'
  | 'SUMMARIZES'
  | 'EXPORTED_FROM'
  | 'DEPENDS_ON';

export type ActivityType =
  | 'WORKSPACE_CREATED'
  | 'WORKSPACE_ARCHIVED'
  | 'WORKSPACE_RESTORED'
  | 'PROJECT_CREATED'
  | 'PROJECT_UPDATED'
  | 'PROJECT_ARCHIVED'
  | 'PROJECT_RESTORED'
  | 'PROJECT_DUPLICATED'
  | 'ASSET_CREATED'
  | 'ASSET_ACCESSED'
  | 'ASSET_FAVORITED'
  | 'ASSET_UNFAVORITED'
  | 'ASSET_ARCHIVED'
  | 'ASSET_RESTORED'
  | 'ASSET_DELETED'
  | 'DATASET_CREATED'
  | 'DATASET_ARCHIVED'
  | 'DATASET_RESTORED'
  | 'DATASET_VERSION_CREATED'
  | 'DASHBOARD_CREATED'
  | 'DASHBOARD_UPDATED'
  | 'REPORT_CREATED'
  | 'REPORT_EXPORTED'
  | 'VISUALIZATION_CREATED'
  | 'QUERY_SAVED'
  | 'STATISTICAL_ANALYSIS_CREATED'
  | 'ML_EXPERIMENT_CREATED'
  | 'FORECAST_CREATED'
  | 'AI_SESSION_CREATED'
  | 'EXPORT_COMPLETED';

export interface Workspace {
  workspace_id: string;
  name: string;
  slug: string;
  description?: string;
  status: WorkspaceStatus;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  metadata?: Record<string, any>;
  configuration_version: number;
}

export interface Project {
  project_id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description?: string;
  status: ProjectStatus;
  icon?: string;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  last_activity_at: string;
  metadata?: Record<string, any>;
  configuration_version: number;
}

export interface Asset {
  asset_id: string;
  asset_type: AssetType;
  project_id: string;
  workspace_id: string;
  source_entity_id: string;
  name: string;
  description?: string;
  status: AssetStatus;
  created_at: string;
  updated_at: string;
  last_accessed_at?: string | null;
  archived_at?: string | null;
  is_favorite: boolean;
  metadata?: Record<string, any>;
  tags: string[];
  source_version_reference?: string | null;
  provenance_reference?: string | null;
}

export interface AssetRelationship {
  relationship_id: string;
  source_asset_id: string;
  target_asset_id: string;
  relationship_type: RelationshipType;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface ActivityRecord {
  activity_id: string;
  workspace_id: string;
  project_id: string;
  asset_id?: string | null;
  activity_type: ActivityType;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface BrokenReference {
  source_asset_id: string;
  source_asset_name: string;
  missing_target_id: string;
  relationship_type: string;
  reason: string;
}

export interface ProjectHealth {
  project_id: string;
  workspace_id: string;
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  datasets_ready: number;
  datasets_failed: number;
  archived_datasets: number;
  total_assets: number;
  broken_references: BrokenReference[];
  failed_jobs_count: number;
}

export interface DependencyItem {
  asset_id: string;
  asset_name: string;
  asset_type: AssetType;
  relationship: RelationshipType;
  is_direct: boolean;
}

export interface DependencySummary {
  asset_id: string;
  asset_name: string;
  asset_type: AssetType;
  can_safely_delete: boolean;
  downstream_dependencies: DependencyItem[];
  upstream_dependencies: DependencyItem[];
  warnings: string[];
}

export interface LineageNode {
  id: string;
  label: string;
  type: string;
  status: string;
  is_stale: boolean;
  metadata?: Record<string, any>;
}

export interface LineageEdge {
  source: string;
  target: string;
  label: string;
  relationship_type: string;
}

export interface LineageGraph {
  root_asset_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export interface SchemaDiff {
  added_columns: Array<{ name: string; type: string }>;
  removed_columns: Array<{ name: string; type: string }>;
  modified_types: Array<{ name: string; type_a: string; type_b: string }>;
  unchanged_columns: Array<{ name: string; type: string }>;
}

export interface DatasetVersionComparisonResult {
  dataset_id: string;
  version_a_id: string;
  version_b_id: string;
  row_count_a: number;
  row_count_b: number;
  row_count_delta: number;
  column_count_a: number;
  column_count_b: number;
  column_count_delta: number;
  schema_diff: SchemaDiff;
  transformation_summary_a?: string | null;
  transformation_summary_b?: string | null;
  comparison_available: boolean;
  notes?: string | null;
}

export interface SearchResult {
  asset_id: string;
  asset_type: AssetType;
  name: string;
  description?: string | null;
  project_id: string;
  project_name?: string | null;
  workspace_id: string;
  status: AssetStatus;
  is_favorite: boolean;
  tags: string[];
  created_at: string;
  updated_at: string;
  navigation_url: string;
  source_entity_id: string;
  score?: number;
  matched_field?: string;
}

export interface SearchResponse {
  query: string;
  total: number;
  page: number;
  page_size: number;
  results: SearchResult[];
}

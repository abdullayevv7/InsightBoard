/**
 * Data Sources API module: CRUD, connection testing, schema, queries.
 */

import apiClient from "./client";

export interface DataSource {
  id: string;
  name: string;
  description: string;
  source_type: string;
  source_type_display: string;
  status: "active" | "inactive" | "error" | "testing";
  last_synced_at: string | null;
  sync_interval_minutes: number;
  schema_cache: Record<string, unknown> | null;
  connection?: DataConnection;
  query_count?: number;
  created_by: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface DataConnection {
  id: string;
  host: string;
  port: number | null;
  database_name: string;
  username: string;
  has_password: boolean;
  ssl_enabled: boolean;
  api_url: string;
  has_api_key: boolean;
  auth_type: string;
  file: string | null;
  spreadsheet_id: string;
  sheet_name: string;
}

export interface DataSourceCreatePayload {
  name: string;
  description?: string;
  source_type: string;
  sync_interval_minutes?: number;
  connection?: Record<string, unknown>;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  execution_time_ms: number;
}

export const datasourcesApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get<{ results: DataSource[] }>("/datasources/", { params }),

  get: (id: string) =>
    apiClient.get<DataSource>(`/datasources/${id}/`),

  create: (data: DataSourceCreatePayload) =>
    apiClient.post<DataSource>("/datasources/", data),

  update: (id: string, data: Partial<DataSourceCreatePayload>) =>
    apiClient.patch<DataSource>(`/datasources/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/datasources/${id}/`),

  testConnection: (id: string) =>
    apiClient.post<{ success: boolean; message: string }>(
      `/datasources/${id}/test-connection/`
    ),

  fetchSchema: (id: string) =>
    apiClient.post<{ schema: Record<string, unknown> }>(
      `/datasources/${id}/fetch-schema/`
    ),

  executeQuery: (id: string, query: string, params?: Record<string, unknown>) =>
    apiClient.post<QueryResult>(`/datasources/${id}/query/`, {
      query,
      parameters: params,
    }),

  updateConnection: (id: string, data: Record<string, unknown>) =>
    apiClient.put(`/datasources/${id}/update-connection/`, data),

  // Saved queries
  listQueries: (params?: Record<string, string>) =>
    apiClient.get("/datasources/queries/", { params }),

  createQuery: (data: Record<string, unknown>) =>
    apiClient.post("/datasources/queries/", data),

  executeNamedQuery: (queryId: string, params?: Record<string, unknown>) =>
    apiClient.post(`/datasources/queries/${queryId}/execute/`, {
      parameters: params,
    }),
};

/**
 * Dashboard API module: CRUD, widgets, layouts, sharing.
 */

import apiClient from "./client";

export interface Widget {
  id: string;
  dashboard: string;
  title: string;
  widget_type: string;
  widget_type_display: string;
  data_source: string | null;
  query_config: Record<string, unknown>;
  visualization_config: Record<string, unknown>;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  cache_duration_seconds: number;
  cached_data: unknown;
  cached_at: string | null;
}

export interface Dashboard {
  id: string;
  title: string;
  description: string;
  owner: string;
  owner_name: string;
  organization: string;
  is_public: boolean;
  is_template: boolean;
  tags: string[];
  settings: Record<string, unknown>;
  auto_refresh_seconds: number;
  thumbnail: string | null;
  widgets: Widget[];
  widget_count: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardCreatePayload {
  title: string;
  description?: string;
  is_public?: boolean;
  is_template?: boolean;
  tags?: string[];
  settings?: Record<string, unknown>;
  auto_refresh_seconds?: number;
}

export interface WidgetCreatePayload {
  title: string;
  widget_type: string;
  data_source?: string;
  query_config?: Record<string, unknown>;
  visualization_config?: Record<string, unknown>;
  position_x?: number;
  position_y?: number;
  width?: number;
  height?: number;
}

export interface LayoutItem {
  widget_id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export const dashboardsApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get<{ results: Dashboard[] }>("/dashboards/", { params }),

  get: (id: string) =>
    apiClient.get<Dashboard>(`/dashboards/${id}/`),

  create: (data: DashboardCreatePayload) =>
    apiClient.post<Dashboard>("/dashboards/", data),

  update: (id: string, data: Partial<DashboardCreatePayload>) =>
    apiClient.patch<Dashboard>(`/dashboards/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/dashboards/${id}/`),

  clone: (id: string, title?: string) =>
    apiClient.post<Dashboard>(`/dashboards/${id}/clone/`, { title }),

  // Widgets
  listWidgets: (dashboardId: string) =>
    apiClient.get<Widget[]>(`/dashboards/${dashboardId}/widgets/`),

  addWidget: (dashboardId: string, data: WidgetCreatePayload) =>
    apiClient.post<Widget>(`/dashboards/${dashboardId}/widgets/`, data),

  updateWidget: (widgetId: string, data: Partial<WidgetCreatePayload>) =>
    apiClient.patch<Widget>(`/dashboards/widgets/${widgetId}/`, data),

  deleteWidget: (widgetId: string) =>
    apiClient.delete(`/dashboards/widgets/${widgetId}/`),

  refreshWidget: (widgetId: string) =>
    apiClient.post(`/dashboards/widgets/${widgetId}/refresh-data/`),

  // Layout
  updateLayout: (dashboardId: string, layouts: LayoutItem[]) =>
    apiClient.put(`/dashboards/${dashboardId}/layout/`, { layouts }),

  // Sharing
  listShares: (dashboardId: string) =>
    apiClient.get(`/dashboards/${dashboardId}/shares/`),

  createShare: (dashboardId: string, data: Record<string, unknown>) =>
    apiClient.post(`/dashboards/${dashboardId}/shares/`, data),
};

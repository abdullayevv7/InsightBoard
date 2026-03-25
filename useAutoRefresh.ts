/**
 * Reports API module: CRUD, exports, schedules.
 */

import apiClient from "./client";

export interface Report {
  id: string;
  title: string;
  description: string;
  organization: string;
  status: "draft" | "published" | "archived";
  default_format: string;
  sections: ReportSection[];
  parameters: ReportParameter[];
  filters: Record<string, unknown>;
  page_orientation: "portrait" | "landscape";
  page_size: string;
  is_public: boolean;
  share_token: string | null;
  tags: string[];
  export_count: number;
  has_schedule: boolean;
  created_by: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface ReportSection {
  type: "text" | "chart" | "table" | "metric";
  title: string;
  config: Record<string, unknown>;
  visualization_id?: string;
}

export interface ReportParameter {
  name: string;
  type: string;
  label: string;
  default_value: unknown;
}

export interface ReportExport {
  id: string;
  report: string;
  report_title: string;
  format: string;
  status: "pending" | "processing" | "completed" | "failed";
  file: string | null;
  file_size_bytes: number;
  error_message: string;
  generation_time_ms: number;
  created_at: string;
}

export interface ReportSchedule {
  id: string;
  report: string;
  report_title: string;
  frequency: string;
  frequency_display: string;
  day_of_week: number | null;
  day_of_month: number | null;
  time_of_day: string;
  timezone: string;
  export_format: string;
  recipients: string[];
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
}

export const reportsApi = {
  list: (params?: Record<string, string>) =>
    apiClient.get<{ results: Report[] }>("/reports/", { params }),

  get: (id: string) =>
    apiClient.get<Report>(`/reports/${id}/`),

  create: (data: Partial<Report>) =>
    apiClient.post<Report>("/reports/", data),

  update: (id: string, data: Partial<Report>) =>
    apiClient.patch<Report>(`/reports/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/reports/${id}/`),

  publish: (id: string) =>
    apiClient.post<Report>(`/reports/${id}/publish/`),

  archive: (id: string) =>
    apiClient.post<Report>(`/reports/${id}/archive/`),

  // Exports
  requestExport: (id: string, format: string, parameters?: Record<string, unknown>) =>
    apiClient.post<ReportExport>(`/reports/${id}/export/`, { format, parameters }),

  listExports: (id: string) =>
    apiClient.get<ReportExport[]>(`/reports/${id}/exports/`),

  downloadExport: (exportId: string) =>
    apiClient.get(`/reports/exports/${exportId}/download/`, {
      responseType: "blob",
    }),

  // Schedules
  listSchedules: (reportId: string) =>
    apiClient.get<ReportSchedule[]>(`/reports/${reportId}/schedules/`),

  createSchedule: (reportId: string, data: Partial<ReportSchedule>) =>
    apiClient.post<ReportSchedule>(`/reports/${reportId}/schedules/`, data),

  toggleSchedule: (scheduleId: string) =>
    apiClient.post<ReportSchedule>(`/reports/schedules/${scheduleId}/toggle/`),

  // Share
  generateShareLink: (id: string) =>
    apiClient.post<{ share_token: string; share_url: string }>(
      `/reports/${id}/generate-share-link/`
    ),
};

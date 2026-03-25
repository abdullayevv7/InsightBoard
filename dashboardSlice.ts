/**
 * Data Source Connector: form component for configuring data source connections.
 * Dynamically shows fields based on selected source type.
 */

import React, { useState } from "react";
import { DataSourceCreatePayload } from "../../api/datasources";

interface DataSourceConnectorProps {
  onSubmit: (data: DataSourceCreatePayload) => void;
  onCancel: () => void;
  onTestConnection: (data: DataSourceCreatePayload) => void;
  isLoading?: boolean;
  testResult?: { success: boolean; message: string } | null;
}

const SOURCE_TYPES = [
  { value: "postgresql", label: "PostgreSQL", category: "Database" },
  { value: "mysql", label: "MySQL", category: "Database" },
  { value: "rest_api", label: "REST API", category: "API" },
  { value: "csv", label: "CSV Upload", category: "File" },
  { value: "excel", label: "Excel Upload", category: "File" },
  { value: "google_sheets", label: "Google Sheets", category: "Cloud" },
  { value: "json", label: "JSON Endpoint", category: "API" },
];

const AUTH_TYPES = [
  { value: "none", label: "No Auth" },
  { value: "api_key", label: "API Key" },
  { value: "bearer", label: "Bearer Token" },
  { value: "basic", label: "Basic Auth" },
  { value: "oauth2", label: "OAuth 2.0" },
];

const DataSourceConnector: React.FC<DataSourceConnectorProps> = ({
  onSubmit,
  onCancel,
  onTestConnection,
  isLoading = false,
  testResult,
}) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [sourceType, setSourceType] = useState("postgresql");
  const [syncInterval, setSyncInterval] = useState(0);

  // Database fields
  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const [databaseName, setDatabaseName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [sslEnabled, setSslEnabled] = useState(false);

  // API fields
  const [apiUrl, setApiUrl] = useState("");
  const [authType, setAuthType] = useState("none");
  const [apiKey, setApiKey] = useState("");

  // Google Sheets
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [sheetName, setSheetName] = useState("");

  const isDatabase = ["postgresql", "mysql"].includes(sourceType);
  const isApi = ["rest_api", "json"].includes(sourceType);
  const isFile = ["csv", "excel"].includes(sourceType);
  const isGoogleSheets = sourceType === "google_sheets";

  const buildPayload = (): DataSourceCreatePayload => {
    const connection: Record<string, unknown> = {};

    if (isDatabase) {
      connection.host = host;
      connection.port = parseInt(port) || (sourceType === "postgresql" ? 5432 : 3306);
      connection.database_name = databaseName;
      connection.username = username;
      connection.password_encrypted = password;
      connection.ssl_enabled = sslEnabled;
    } else if (isApi) {
      connection.api_url = apiUrl;
      connection.auth_type = authType;
      if (apiKey) connection.api_key_encrypted = apiKey;
    } else if (isGoogleSheets) {
      connection.spreadsheet_id = spreadsheetId;
      connection.sheet_name = sheetName;
    }

    return {
      name,
      description,
      source_type: sourceType,
      sync_interval_minutes: syncInterval,
      connection: Object.keys(connection).length > 0 ? connection : undefined,
    };
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(buildPayload());
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Data Source Details</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            placeholder="Production Database"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            placeholder="Main PostgreSQL database for sales data"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Source Type</label>
          <div className="grid grid-cols-4 gap-2">
            {SOURCE_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => setSourceType(type.value)}
                className={`p-3 rounded-lg border-2 text-center transition-colors ${
                  sourceType === type.value
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="text-xs text-gray-400">{type.category}</div>
                <div className="text-sm font-medium">{type.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Database Connection */}
      {isDatabase && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-md font-medium text-gray-900">Database Connection</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
              <input type="text" value={host} onChange={(e) => setHost(e.target.value)} required
                className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="db.example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
              <input type="number" value={port} onChange={(e) => setPort(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder={sourceType === "postgresql" ? "5432" : "3306"} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Database Name</label>
              <input type="text" value={databaseName} onChange={(e) => setDatabaseName(e.target.value)} required
                className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="mydb" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required
                className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="admin" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2" />
            </div>
            <div className="flex items-center pt-6">
              <input type="checkbox" id="ssl" checked={sslEnabled}
                onChange={(e) => setSslEnabled(e.target.checked)}
                className="h-4 w-4 text-blue-600 rounded" />
              <label htmlFor="ssl" className="ml-2 text-sm text-gray-700">Enable SSL</label>
            </div>
          </div>
        </div>
      )}

      {/* API Connection */}
      {isApi && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-md font-medium text-gray-900">API Connection</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API URL</label>
            <input type="url" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} required
              className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="https://api.example.com/data" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Authentication</label>
            <select value={authType} onChange={(e) => setAuthType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2">
              {AUTH_TYPES.map((a) => (
                <option key={a.value} value={a.value}>{a.label}</option>
              ))}
            </select>
          </div>
          {authType !== "none" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key / Token</label>
              <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2" />
            </div>
          )}
        </div>
      )}

      {/* File upload placeholder */}
      {isFile && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-md font-medium text-gray-900 mb-3">File Upload</h3>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-sm text-gray-500">
              Drag and drop your {sourceType.toUpperCase()} file here, or click to browse
            </p>
            <input type="file" accept={sourceType === "csv" ? ".csv" : ".xlsx,.xls"}
              className="mt-3" />
          </div>
        </div>
      )}

      {/* Google Sheets */}
      {isGoogleSheets && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-md font-medium text-gray-900">Google Sheets</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Spreadsheet ID</label>
            <input type="text" value={spreadsheetId} onChange={(e) => setSpreadsheetId(e.target.value)} required
              className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sheet Name</label>
            <input type="text" value={sheetName} onChange={(e) => setSheetName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="Sheet1" />
          </div>
        </div>
      )}

      {/* Sync Interval */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Auto-sync Interval (minutes, 0 = manual only)
        </label>
        <input type="number" value={syncInterval} onChange={(e) => setSyncInterval(parseInt(e.target.value) || 0)}
          min={0} className="w-full border border-gray-300 rounded-lg px-3 py-2" />
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`p-3 rounded-lg text-sm ${
          testResult.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
        }`}>
          {testResult.success ? "Connection successful" : "Connection failed"}: {testResult.message}
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between pt-4 border-t">
        <button type="button" onClick={() => onTestConnection(buildPayload())}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50">
          Test Connection
        </button>
        <div className="space-x-3">
          <button type="button" onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            Cancel
          </button>
          <button type="submit" disabled={isLoading || !name}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {isLoading ? "Saving..." : "Save Data Source"}
          </button>
        </div>
      </div>
    </form>
  );
};

export default DataSourceConnector;

/**
 * Main App component with routing and layout.
 */

import React from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink, Outlet } from "react-router-dom";
import { Provider } from "react-redux";
import { store, useAppSelector, useAppDispatch } from "./store";
import { logout } from "./store/authSlice";

import DashboardPage from "./pages/DashboardPage";
import DashboardBuilderPage from "./pages/DashboardBuilderPage";
import DataSourcesPage from "./pages/DataSourcesPage";
import ReportsPage from "./pages/ReportsPage";
import AlertsPage from "./pages/AlertsPage";
import SettingsPage from "./pages/SettingsPage";

const NAV_ITEMS = [
  { path: "/dashboards", label: "Dashboards" },
  { path: "/datasources", label: "Data Sources" },
  { path: "/reports", label: "Reports" },
  { path: "/alerts", label: "Alerts" },
  { path: "/settings", label: "Settings" },
];

const AppLayout: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();

  const handleLogout = () => {
    dispatch(logout()).then(() => {
      window.location.href = "/login";
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div className="flex items-center space-x-8">
              <NavLink to="/dashboards" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                  IB
                </div>
                <span className="font-semibold text-gray-900">InsightBoard</span>
              </NavLink>

              {/* Nav Links */}
              <div className="flex space-x-1">
                {NAV_ITEMS.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {user?.full_name || user?.email}
              </div>
              <div className="text-xs text-gray-400 capitalize">
                {user?.role}
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main>
        <Outlet />
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/dashboards" element={<DashboardPage />} />
            <Route path="/dashboards/:id" element={<DashboardBuilderPage />} />
            <Route path="/dashboards/:id/edit" element={<DashboardBuilderPage />} />
            <Route path="/datasources" element={<DataSourcesPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route path="/" element={<Navigate to="/dashboards" replace />} />
          <Route path="*" element={<Navigate to="/dashboards" replace />} />
        </Routes>
      </BrowserRouter>
    </Provider>
  );
};

export default App;

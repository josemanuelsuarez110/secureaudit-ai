/**
 * Cliente API para SecureAudit AI.
 * Maneja JWT, errores y refresh automático.
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =========================================================
// Tipos
// =========================================================

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  organization_id: string;
  domain: string;
  display_name: string | null;
  status: "pending_verification" | "active" | "paused" | "archived";
  verification_token: string;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScanJob {
  id: string;
  organization_id: string;
  asset_id: string;
  created_by: string | null;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  scan_type: "full" | "tls" | "http" | "dns";
  priority: number;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScanResult {
  id: string;
  scan_job_id: string;
  asset_id: string;
  category: string;
  check_name: string;
  status: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string | null;
  evidence: Record<string, unknown> | null;
  recommendation: string | null;
  created_at: string;
}

export interface ScanJobDetail extends ScanJob {
  results: ScanResult[];
}

// =========================================================
// Cliente HTTP
// =========================================================

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor: añadir JWT a cada request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor: manejar 401 (token expirado)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// =========================================================
// API methods
// =========================================================

export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    full_name?: string;
    organization_name?: string;
    organization_slug?: string;
  }) => {
    const response = await api.post("/auth/register", data);
    return response.data;
  },

  login: async (data: { email: string; password: string }) => {
    const response = await api.post<{ access_token: string; token_type: string }>(
      "/auth/login",
      data
    );
    return response.data;
  },

  me: async () => {
    const response = await api.get<User>("/auth/me");
    return response.data;
  },
};

export const organizationsApi = {
  list: async () => {
    const response = await api.get<Organization[]>("/organizations");
    return response.data;
  },

  create: async (data: { name: string; slug: string }) => {
    const response = await api.post<Organization>("/organizations", data);
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<Organization>(`/organizations/${id}`);
    return response.data;
  },

  update: async (id: string, data: { name?: string }) => {
    const response = await api.patch<Organization>(`/organizations/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/organizations/${id}`);
  },
};

export const assetsApi = {
  list: async (organizationId: string) => {
    const response = await api.get<Asset[]>(
      `/assets/organizations/${organizationId}/assets`
    );
    return response.data;
  },

  create: async (
    organizationId: string,
    data: { domain: string; display_name?: string }
  ) => {
    const response = await api.post<Asset>(
      `/assets/organizations/${organizationId}/assets`,
      data
    );
    return response.data;
  },

  get: async (assetId: string) => {
    const response = await api.get<Asset>(`/assets/${assetId}`);
    return response.data;
  },

  update: async (assetId: string, data: { display_name?: string; status?: string }) => {
    const response = await api.patch<Asset>(`/assets/${assetId}`, data);
    return response.data;
  },

  delete: async (assetId: string) => {
    await api.delete(`/assets/${assetId}`);
  },

  verify: async (assetId: string) => {
    const response = await api.post(`/assets/${assetId}/verify`);
    return response.data;
  },
};

export const scansApi = {
  list: async (organizationId: string) => {
    const response = await api.get<ScanJob[]>(
      `/scans/organizations/${organizationId}/scans`
    );
    return response.data;
  },

  create: async (
    organizationId: string,
    data: { asset_id: string; scan_type?: string }
  ) => {
    const response = await api.post<ScanJob>(
      `/scans/organizations/${organizationId}/scans`,
      data
    );
    return response.data;
  },

  get: async (scanJobId: string) => {
    const response = await api.get<ScanJobDetail>(`/scans/${scanJobId}`);
    return response.data;
  },

  results: async (scanJobId: string) => {
    const response = await api.get<ScanResult[]>(`/scans/${scanJobId}/results`);
    return response.data;
  },

  cancel: async (scanJobId: string) => {
    const response = await api.post<ScanJob>(`/scans/${scanJobId}/cancel`);
    return response.data;
  },
};

// =========================================================
// Helpers
// =========================================================

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    return error.message;
  }
  return "Error desconocido";
}

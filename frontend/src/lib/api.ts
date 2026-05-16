import axios from 'axios';
import type { PaginatedResponse } from '@/types/api';
import type { LoginRequest, TokenResponse, RefreshRequest, UserMe } from '@/types/auth';
import type { UserOut, UserCreate, UserUpdate } from '@/types/user';
import type { PropertyOut, PropertyListOut, PropertyCreate, PropertyUpdate, PropertyFilter } from '@/types/property';
import type { AuditLogOut } from '@/types/auditLog';
import type { ImportJobOut, ImportJobDetail, ImportErrorOut, ColumnsResponse, PreviewResponse, ImportResult, FieldMappingRequest } from '@/types/import';
import type { GeocodeResult, GeocodeRequest } from '@/types/geo';
import type { RouteMatrixRequest, RouteMatrixResponse } from '@/types/transit';
import type { LeadOut, LeadCreate, LeadUpdate, LeadFilter } from '@/types/lead';
import type {
  ParseLeadRequest,
  ParseLeadResponse,
  GenerateTagsRequest,
  GenerateTagsResponse,
  GenerateMessageRequest,
  GenerateMessageResponse,
  RecommendationSearchRequest,
  RecommendationSearchResponse,
  RecommendationOut,
  SaveMessageRequest,
  MarkSentResponse,
  CleanDataRequest,
  CleanDataResponse,
} from '@/types/ai';
import type {
  LineConversationSummary,
  LineConversationOut,
  LineAIReplyResponse,
  LineReplyRequest,
  LinePushRequest,
} from '@/types/line';
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Attach token to requests
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
let refreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      if (typeof window !== 'undefined') window.location.href = '/login';
      return Promise.reject(error);
    }

    if (!refreshing) {
      refreshing = true;
      try {
        const res = await axios.post<TokenResponse>(
          `${api.defaults.baseURL}/auth/refresh`,
          { refresh_token: refreshToken } as RefreshRequest,
        );
        setTokens(res.data.access_token, res.data.refresh_token);
        refreshQueue.forEach((cb) => cb(res.data.access_token));
        refreshQueue = [];
        originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
        originalRequest._retry = true;
        return api(originalRequest);
      } catch {
        clearTokens();
        refreshQueue = [];
        if (typeof window !== 'undefined') window.location.href = '/login';
        return Promise.reject(error);
      } finally {
        refreshing = false;
      }
    }

    return new Promise((resolve) => {
      refreshQueue.push((token: string) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        originalRequest._retry = true;
        resolve(api(originalRequest));
      });
    });
  },
);

// Auth
export function login(data: LoginRequest) {
  return api.post<TokenResponse>('/auth/login', data).then((r) => r.data);
}
export function refreshToken(data: RefreshRequest) {
  return api.post<TokenResponse>('/auth/refresh', data).then((r) => r.data);
}
export function getMe() {
  return api.get<UserMe>('/auth/me').then((r) => r.data);
}

// Users
export function getUsers(params: Record<string, unknown>) {
  return api.get<PaginatedResponse<UserOut>>('/users/', { params }).then((r) => r.data);
}
export function getUser(id: string) {
  return api.get<UserOut>(`/users/${id}`).then((r) => r.data);
}
export function createUser(data: UserCreate) {
  return api.post<UserOut>('/users/', data).then((r) => r.data);
}
export function updateUser(id: string, data: UserUpdate) {
  return api.put<UserOut>(`/users/${id}`, data).then((r) => r.data);
}
export function deleteUser(id: string) {
  return api.delete(`/users/${id}`).then((r) => r.data);
}

// Properties
export function getProperties(params: PropertyFilter) {
  return api.get<PaginatedResponse<PropertyListOut>>('/properties/', { params }).then((r) => r.data);
}
export function getProperty(id: string) {
  return api.get<PropertyOut>(`/properties/${id}`).then((r) => r.data);
}
export function createProperty(data: PropertyCreate) {
  return api.post<PropertyOut>('/properties/', data).then((r) => r.data);
}
export function updateProperty(id: string, data: PropertyUpdate) {
  return api.put<PropertyOut>(`/properties/${id}`, data).then((r) => r.data);
}
export function deleteProperty(id: string) {
  return api.delete(`/properties/${id}`).then((r) => r.data);
}
export function uploadPropertyImages(propertyId: string, files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  return api.post(`/properties/${propertyId}/images`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
}
export function deletePropertyImage(imageId: string) {
  return api.delete(`/properties/images/${imageId}`).then((r) => r.data);
}
export function exportPropertiesCSV(params?: Record<string, unknown>) {
  return api.get('/properties/export/csv', { params, responseType: 'blob' }).then((r) => r.data);
}
export function bulkUpdateProperties(data: { property_ids: string[]; status?: string; tags?: string[]; assigned_agent_id?: string }) {
  return api.post('/properties/bulk-update', data).then((r) => r.data);
}

// Audit Logs
export function getAuditLogs(params: Record<string, unknown>) {
  return api.get<PaginatedResponse<AuditLogOut>>('/audit-logs/', { params }).then((r) => r.data);
}

// Imports
export function uploadImportFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  return api.post<ImportJobOut>('/imports/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
}
export function getImportColumns(jobId: string) {
  return api.get<ColumnsResponse>(`/imports/${jobId}/columns`).then((r) => r.data);
}
export function previewImport(jobId: string, mapping?: FieldMappingRequest) {
  return api.put<PreviewResponse>(`/imports/${jobId}/preview`, mapping || {}).then((r) => r.data);
}
export function mapImportFields(jobId: string, mapping: FieldMappingRequest) {
  return api.put<ImportJobOut>(`/imports/${jobId}/map`, mapping).then((r) => r.data);
}
export function confirmImport(jobId: string, overwrite?: boolean) {
  return api.post<ImportResult>(`/imports/${jobId}/confirm`, { overwrite_existing: overwrite || false }).then((r) => r.data);
}
export function getImportJobs(params: Record<string, unknown>) {
  return api.get<PaginatedResponse<ImportJobOut>>('/imports/', { params }).then((r) => r.data);
}
export function getImportJob(jobId: string) {
  return api.get<ImportJobDetail>(`/imports/${jobId}`).then((r) => r.data);
}
export function getImportErrors(jobId: string) {
  return api.get<ImportErrorOut[]>(`/imports/${jobId}/errors`).then((r) => r.data);
}

// Geo
export function geocodeAddress(data: GeocodeRequest) {
  return api.post<GeocodeResult[]>('/geo/geocode', data).then((r) => r.data);
}
export function triggerGeocodeBackfill() {
  return api.post<{ total_no_gps: number; geocoded: number; skipped: number; errors: number }>('/geo/backfill').then((r) => r.data);
}

// Transit (Phase 4)
export function computeRouteMatrix(data: RouteMatrixRequest) {
  return api.post<RouteMatrixResponse>('/transit/route-matrix', data).then((r) => r.data);
}

// Leads
export function getLeads(params: LeadFilter) {
  return api.get<PaginatedResponse<LeadOut>>('/leads/', { params }).then((r) => r.data);
}
export function getLead(id: string) {
  return api.get<LeadOut>(`/leads/${id}`).then((r) => r.data);
}
export function createLead(data: LeadCreate) {
  return api.post<LeadOut>('/leads/', data).then((r) => r.data);
}
export function updateLead(id: string, data: LeadUpdate) {
  return api.put<LeadOut>(`/leads/${id}`, data).then((r) => r.data);
}
export function parseLeadNeeds(leadId: string) {
  return api.post<LeadOut>(`/leads/${leadId}/parse`).then((r) => r.data);
}

// AI
export function aiParseLead(data: ParseLeadRequest) {
  return api.post<ParseLeadResponse>('/ai/parse-lead', data).then((r) => r.data);
}
export function aiGenerateTags(data: GenerateTagsRequest) {
  return api.post<GenerateTagsResponse>('/ai/generate-tags', data).then((r) => r.data);
}
export function aiGenerateMessage(data: GenerateMessageRequest) {
  return api.post<GenerateMessageResponse>('/ai/generate-message', data).then((r) => r.data);
}
export function aiCleanData(data: CleanDataRequest) {
  return api.post<CleanDataResponse>('/ai/clean-data', data).then((r) => r.data);
}

// Recommendations
export function searchRecommendations(data: RecommendationSearchRequest) {
  return api.post<RecommendationSearchResponse>('/recommendations/search', data).then((r) => r.data);
}
export function getLeadRecommendations(leadId: string) {
  return api.get<RecommendationOut[]>(`/recommendations/by-lead/${leadId}`).then((r) => r.data);
}
export function saveRecommendationMessage(id: string, data: SaveMessageRequest) {
  return api.post<RecommendationOut>(`/recommendations/${id}/save-message`, data).then((r) => r.data);
}
export function markRecommendationSent(id: string) {
  return api.post<MarkSentResponse>(`/recommendations/${id}/mark-sent`).then((r) => r.data);
}

// LINE
export function getLineConversations(params: { page?: number; page_size?: number; status?: string }) {
  return api.get<{ items: LineConversationSummary[]; total: number; page: number; page_size: number; total_pages: number }>('/line/conversations', { params }).then((r) => r.data);
}
export function getLineConversation(lineUserId: string) {
  return api.get<LineConversationOut>(`/line/conversations/${lineUserId}`).then((r) => r.data);
}
export function getLineAIReply(lineUserId: string) {
  return api.post<LineAIReplyResponse>(`/line/conversations/${lineUserId}/ai-reply`).then((r) => r.data);
}
export function pushLineMessage(data: LinePushRequest) {
  return api.post<{ status: string; message_id?: string }>('/line/push', data).then((r) => r.data);
}
export function replyLineMessage(data: LineReplyRequest) {
  return api.post<{ status: string; message_id?: string }>('/line/reply', data).then((r) => r.data);
}

// LINE Settings (Rich Menu + Auto-reply)
import type { AutoReplyStatus, RichMenuOut } from '@/types/report';
export function getAutoReplySetting() {
  return api.get<AutoReplyStatus>('/line/settings/auto-reply').then((r) => r.data);
}
export function setAutoReplySetting(enabled: boolean) {
  return api.put<AutoReplyStatus>('/line/settings/auto-reply', { enabled }).then((r) => r.data);
}
export function getRichMenus() {
  return api.get<RichMenuOut[]>('/line/settings/rich-menus').then((r) => r.data);
}
export function createRichMenu(data: Record<string, unknown>) {
  return api.post<RichMenuOut>('/line/settings/rich-menus', data).then((r) => r.data);
}
export function setDefaultRichMenu(richMenuId: string) {
  return api.post(`/line/settings/rich-menus/${richMenuId}/set-default`).then((r) => r.data);
}
export function deleteRichMenu(richMenuId: string) {
  return api.delete(`/line/settings/rich-menus/${richMenuId}`).then((r) => r.data);
}
export function uploadRichMenuImage(richMenuId: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  return api.post(`/line/settings/rich-menus/${richMenuId}/image`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
}

// Reports
import type { PropertyStats, LeadFunnel, RecommendationStats } from '@/types/report';
export function getPropertyStats() {
  return api.get<PropertyStats>('/reports/properties').then((r) => r.data);
}
export function getLeadFunnel(days?: number) {
  return api.get<LeadFunnel>('/reports/leads', { params: { days } }).then((r) => r.data);
}
export function getRecommendationStats(days?: number) {
  return api.get<RecommendationStats>('/reports/recommendations', { params: { days } }).then((r) => r.data);
}

// API Settings (Admin)
export function getApiSettings() {
  return api.get<Record<string, Array<{ id: string; provider: string; key_name: string; value: string | null; has_value: boolean; config_json: Record<string, unknown> | null; is_active: boolean }>>>('/admin/settings/').then((r) => r.data);
}
export function upsertApiSetting(data: { provider: string; key_name: string; value?: string; config_json?: Record<string, unknown>; is_active?: boolean }) {
  return api.put('/admin/settings/', data).then((r) => r.data);
}
export function toggleApiSetting(id: string, isActive: boolean) {
  return api.patch<{ id: string; provider: string; key_name: string; value: string | null; has_value: boolean; config_json: Record<string, unknown> | null; is_active: boolean }>(`/admin/settings/${id}`, { is_active: isActive }).then((r) => r.data);
}
export function deleteApiSetting(id: string) {
  return api.delete(`/admin/settings/${id}`).then((r) => r.data);
}
export function testApiConnection(provider: string) {
  return api.post<{ success: boolean; message: string }>(`/admin/settings/test-connection/${provider}`).then((r) => r.data);
}

export default api;

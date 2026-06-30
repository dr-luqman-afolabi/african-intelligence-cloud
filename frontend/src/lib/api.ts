import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MacroDataPoint {
  indicator_code: string;
  indicator_name: string;
  year: number;
  value: number;
  unit: string;
}

export interface MacroDataResponse {
  country_iso3: string;
  country_name: string;
  data: MacroDataPoint[];
}

export interface Country {
  iso3: string;
  iso2: string;
  name: string;
  region: string;
}

export interface Indicator {
  code: string;
  name: string;
  unit: string;
  category: string;
}

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("aic_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("aic_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export async function fetchMacroData(country: string): Promise<MacroDataResponse> {
  const { data } = await api.get<MacroDataResponse>(`/macro-data?country=${country}`);
  return data;
}

export async function fetchCountries() {
  const { data } = await api.get("/countries");
  return data;
}

export async function fetchIndicators() {
  const { data } = await api.get("/indicators");
  return data;
}

// ── Dataset types ─────────────────────────────────────────────────────────────

export type DatasetPrivacy = "private" | "organization" | "public";
export type DatasetStatus = "uploaded" | "profiling" | "profiled" | "failed";

export interface DatasetListItem {
  id: string;
  name: string;
  description: string | null;
  original_filename: string;
  file_extension: string;
  file_size_bytes: number;
  privacy: DatasetPrivacy;
  status: DatasetStatus;
  tags: string[];
  row_count: number | null;
  column_count: number | null;
  uploaded_by: string;
  created_at: string;
}

export interface DatasetColumn {
  column_name: string;
  data_type: string;
  null_count: number;
  null_pct: number;
  unique_count: number | null;
  min_value: string | null;
  max_value: string | null;
  mean_value: number | null;
  std_value: number | null;
  sample_values: string[];
}

export interface DatasetProfile {
  row_count: number;
  column_count: number;
  missing_cells: number;
  missing_cells_pct: number;
  duplicate_rows: number;
  numeric_columns: number;
  categorical_columns: number;
  datetime_columns: number;
  profiling_duration_ms: number;
  created_at: string;
}

export interface DatasetDetail extends DatasetListItem {
  storage_path: string;
  columns: DatasetColumn[];
  profile: DatasetProfile | null;
}

export interface DatasetListResponse {
  items: DatasetListItem[];
  total: number;
  page: number;
  page_size: number;
}

// ── Dataset API functions ─────────────────────────────────────────────────────

export async function fetchDatasets(page = 1, pageSize = 20): Promise<DatasetListResponse> {
  const { data } = await api.get<DatasetListResponse>(
    `/datasets?page=${page}&page_size=${pageSize}`
  );
  return data;
}

export async function fetchDataset(id: string): Promise<DatasetDetail> {
  const { data } = await api.get<DatasetDetail>(`/datasets/${id}`);
  return data;
}

export async function uploadDataset(formData: FormData): Promise<DatasetListItem> {
  const { data } = await api.post<DatasetListItem>("/datasets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function triggerProfiling(id: string) {
  const { data } = await api.post(`/datasets/${id}/profile`);
  return data;
}

export async function deleteDataset(id: string): Promise<void> {
  await api.delete(`/datasets/${id}`);
}

// ── Connector types ───────────────────────────────────────────────────────────

export interface ConnectorMetadata {
  source_id: string;
  source_name: string;
  description: string;
  base_url: string;
  license_category: string;
  update_frequency: string;
  supported_indicators: string[];
  supported_countries: string[];
}

export interface ConnectorHealth {
  source_id: string;
  healthy: boolean;
  latency_ms: number | null;
  message: string | null;
  checked_at: string;
}

export interface SyncJob {
  id: string;
  source_id: string;
  status: "running" | "success" | "failed" | "partial";
  records_fetched: number | null;
  records_written: number | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

// ── Connector API functions ───────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function fetchConnectors(): Promise<any[]> {
  const { data } = await api.get<any[]>("/connectors");
  return data;
}

export async function fetchConnectorHealth(sourceId: string): Promise<ConnectorHealth> {
  const { data } = await api.get<ConnectorHealth>(`/connectors/${sourceId}/health`);
  return data;
}

export async function triggerConnectorSync(sourceId: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>(`/connectors/${sourceId}/sync`);
  return data;
}

export async function fetchSyncHistory(sourceId: string): Promise<SyncJob[]> {
  const { data } = await api.get<SyncJob[]>(`/connectors/${sourceId}/sync/history`);
  return data;
}

// ── Health sources types ───────────────────────────────────────────────────────

export interface SourceHealthEntry {
  source_id: string;
  source_name: string;
  license_category: string | null;
  update_frequency: string | null;
  healthy: boolean | null;
  latency_ms: number | null;
  message: string | null;
  checked_at: string | null;
  last_synced_at: string | null;
  records_synced: string | null;
}

export interface HealthSourcesResponse {
  total_sources: number;
  page: { skip: number; limit: number; returned: number };
  summary: { healthy: number; unhealthy: number };
  sources: SourceHealthEntry[];
}

// ── Health sources API functions ──────────────────────────────────────────────

export async function fetchSourcesHealth(params?: {
  limit?: number;
  skip?: number;
  healthy_only?: boolean;
}): Promise<HealthSourcesResponse> {
  const { data } = await api.get<HealthSourcesResponse>("/health/sources", { params });
  return data;
}

export async function fetchSingleSourceHealth(sourceId: string): Promise<SourceHealthEntry> {
  const { data } = await api.get<SourceHealthEntry>(`/health/sources/${sourceId}`);
  return data;
}

// ── Auth types ────────────────────────────────────────────────────────────────

export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; full_name: string }
export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}
export interface TokenResponse { access_token: string; token_type: string }

export async function login(req: LoginRequest): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", req);
  return data;
}

export async function register(req: RegisterRequest): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>("/auth/register", req);
  return data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/profile");
  return data;
}

// ── RAG / AI Research types ───────────────────────────────────────────────────

export interface ChatMessage { role: "user" | "assistant"; content: string }
export interface RAGSource {
  source_id: string;
  title: string;
  score: number;
  excerpt: string;
}
export interface RAGResponse {
  answer: string;
  sources: RAGSource[];
  query_id: string;
}

export async function askResearchAssistant(
  query: string,
  history: ChatMessage[] = []
): Promise<RAGResponse> {
  const { data } = await api.post<RAGResponse>("/rag/query", { query, history });
  return data;
}

export async function ragQuery(req: {
  query: string;
  history?: ChatMessage[];
}): Promise<RAGResponse> {
  return askResearchAssistant(req.query, req.history ?? []);
}

// ── Semantic search ───────────────────────────────────────────────────────────

export interface SemanticSearchResult {
  dataset_id: string;
  title: string;
  description: string;
  score: number;
  source_id: string;
  tags: string[];
  record_count: number;
}
export type SearchResult = SemanticSearchResult;

export async function semanticSearch(query: string, limit = 10): Promise<SemanticSearchResult[]> {
  const { data } = await api.get<SemanticSearchResult[]>("/search/semantic", {
    params: { q: query, limit },
  });
  return data;
}

// ── SDG analytics ────────────────────────────────────────────────────────────

export interface SDGGoal {
  goal_number: number;
  title: string;
  description: string;
  indicators: SDGIndicatorMapping[];
}

export interface SDGIndicatorMapping {
  sdg_target: string;
  indicator_code: string;
  indicator_name: string;
  available_countries: number;
  latest_year: number | null;
}

export async function fetchSDGGoals(): Promise<SDGGoal[]> {
  const { data } = await api.get<SDGGoal[]>("/sdg/goals");
  return data;
}

export async function fetchSDGData(goal: number, country?: string) {
  const { data } = await api.get(`/sdg/data`, { params: { goal, country } });
  return data;
}

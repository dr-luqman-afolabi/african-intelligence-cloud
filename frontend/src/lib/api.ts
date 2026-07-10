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

export async function fetchCountries(): Promise<CountryEntry[]> {
  const { data } = await api.get<CountryEntry[]>("/countries");
  return data;
}

export async function fetchIndicators(): Promise<IndicatorEntry[]> {
  const { data } = await api.get<IndicatorEntry[]>("/indicators");
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
  is_verified: boolean;
  created_at?: string | null;
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

export async function fetchPendingUsers(): Promise<AuthUser[]> {
  const { data } = await api.get<AuthUser[]>("/auth/pending");
  return data;
}

export async function approveUser(userId: string): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>(`/auth/approve/${userId}`);
  return data;
}

export async function fetchAllUsers(): Promise<AuthUser[]> {
  const { data } = await api.get<AuthUser[]>("/auth/users");
  return data;
}

export async function rejectUser(userId: string): Promise<void> {
  await api.delete(`/auth/reject/${userId}`);
}

export async function setUserActive(userId: string, active: boolean): Promise<AuthUser> {
  const { data } = await api.post<AuthUser>(
    `/auth/users/${userId}/${active ? "activate" : "deactivate"}`
  );
  return data;
}

export async function setUserRole(userId: string, role: string): Promise<AuthUser> {
  const { data } = await api.patch<AuthUser>(`/auth/users/${userId}/role`, { role });
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

// ── Research types ────────────────────────────────────────────────────────────

export interface ResearchSource {
  source_id: string;
  name: string;
  type: string;
  api_url: string;
  license: string;
  african_relevance_score: number;
  full_text_allowed: boolean;
  rate_limit: string;
  description: string;
}

export interface PaperResult {
  external_id: string;
  title: string;
  abstract: string | null;
  doi: string | null;
  published_year: number | null;
  journal: string | null;
  authors: string[];
  topics: string[];
  open_access_url: string | null;
  is_open_access: boolean;
  citation_count: number;
  source_id: string;
}

export interface PaperSearchResponse {
  query: string;
  source: string;
  total: number;
  results: PaperResult[];
}

export interface TheoryRecommendation {
  name: string;
  description: string;
  relevance_score: number;
  african_relevance: number;
}

export interface MethodRecommendation {
  method: string;
  description: string;
  software: string[];
  relevance_score: number;
}

export interface VariableRecommendation {
  variable: string;
  recommended_sources: string[];
  relevance_score: number;
}

export interface AfricanDataset {
  name: string;
  url: string;
  coverage: string;
  variables: string;
  license: string;
}

export interface LiteratureMatrixRow {
  title: string;
  authors: string[];
  year: number | null;
  journal: string | null;
  doi: string | null;
  is_open_access: boolean;
  citation_count: number;
  topics: string[];
  theories_used: string[];
  methods_used: string[];
}

export interface LiteratureReviewResponse {
  topic: string;
  total_papers: number;
  matrix: LiteratureMatrixRow[];
  research_gaps: string[];
  recommended_theories: TheoryRecommendation[];
  recommended_methods: MethodRecommendation[];
}

export interface ConceptualFramework {
  title: string;
  theoretical_foundation: string[];
  independent_variables: string[];
  dependent_variable: string;
  moderating_factors: string[];
  control_variables: string[];
  proposed_relationships: string[];
}

export interface VariableRecommendationResponse {
  topic: string;
  recommended_variables: VariableRecommendation[];
  african_datasets: AfricanDataset[];
  conceptual_framework: ConceptualFramework;
  hypotheses: string[];
}

export interface StoredPaper {
  id: string;
  doi: string | null;
  title: string;
  abstract: string | null;
  published_year: number | null;
  journal: string | null;
  is_open_access: boolean;
  open_access_url: string | null;
  citation_count: number;
  authors: { full_name: string; affiliation: string | null }[];
  topics: string[];
  methods: string[];
  theories: string[];
  policy_areas: string[];
  citations: { doi: string | null; title: string | null; year: number | null }[];
}

// ── Research API functions ────────────────────────────────────────────────────

export async function fetchResearchSources(): Promise<ResearchSource[]> {
  const { data } = await api.get<ResearchSource[]>("/research/sources");
  return data;
}

export async function searchResearchPapers(params: {
  q: string;
  source?: string;
  max_results?: number;
  year_from?: number;
  year_to?: number;
}): Promise<PaperSearchResponse> {
  const { data } = await api.get<PaperSearchResponse>("/research/search", { params });
  return data;
}

export async function fetchResearchPaper(paperId: string): Promise<StoredPaper> {
  const { data } = await api.get<StoredPaper>(`/research/paper/${paperId}`);
  return data;
}

export async function generateLiteratureReview(req: {
  topic: string;
  year_from?: number;
  year_to?: number;
  max_results?: number;
}): Promise<LiteratureReviewResponse> {
  const { data } = await api.post<LiteratureReviewResponse>("/research/literature-review", req);
  return data;
}

export async function recommendResearchTheories(req: {
  topic: string;
  context?: string;
}): Promise<{ topic: string; recommended_theories: TheoryRecommendation[] }> {
  const { data } = await api.post("/research/theory-recommendation", req);
  return data;
}

export async function recommendResearchMethods(req: {
  topic: string;
  context?: string;
}): Promise<{ topic: string; recommended_methods: MethodRecommendation[] }> {
  const { data } = await api.post("/research/method-recommendation", req);
  return data;
}

export async function recommendResearchVariables(req: {
  topic: string;
  context?: string;
}): Promise<VariableRecommendationResponse> {
  const { data } = await api.post("/research/variable-recommendation", req);
  return data;
}

export async function exportResearchPapers(req: {
  papers: LiteratureMatrixRow[];
  format: "bibtex" | "ris" | "excel" | "csv";
}): Promise<Blob> {
  const { data } = await api.post("/research/export", req, { responseType: "blob" });
  return data as Blob;
}

export interface SurveyEntry {
  survey_id: string;
  title: string;
  series: string;
  source_id: string;
  country_iso3: string | null;
  primary_topic: string;
  requires_approval: boolean;
  redistribution_allowed: boolean;
  microdata_available: boolean;
  access_url: string | null;
  documentation_url: string | null;
  tags: string[];
}

export async function fetchSurveys(): Promise<SurveyEntry[]> {
  const { data } = await api.get<SurveyEntry[]>("/surveys");
  return data;
}


export interface CountryEntry {
    iso3: string;
    iso2: string;
    name: string;
    region: string;
}

export interface IndicatorEntry {
    code: string;
    name: string;
    unit: string;
    category: string;
}

export interface MacroInterpretation {
    country_iso3: string;
    country_name: string;
    indicators: string[];
    narrative: string;
}

export async function fetchMacroInterpretation(country: string, indicators: string[]): Promise<MacroInterpretation> {
    const { data } = await api.get<MacroInterpretation>("/macro-data/interpret", {
          params: { country, indicators: indicators.join(",") },
    });
    return data;
}


export interface MicrodataDataset {
  id: string;
  project_id: string | null;
  name: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number | null;
  country_iso3: string | null;
  survey_series: string | null;
  year: number | null;
  row_count: number | null;
  column_count: number | null;
  missing_cells: number | null;
  access_status: string;
  uploaded_by: string;
  created_at: string;
}

export interface MicrodataDatasetListResponse {
  items: MicrodataDataset[];
  total: number;
}

export interface MicrodataVariable {
  id: string;
  variable_name: string;
  variable_label: string | null;
  value_labels: Record<string, unknown> | null;
  variable_index: number | null;
  inferred_dtype: string | null;
  missing_count: number | null;
}

export interface PovertyAnalysisRequest {
  dataset_id: string;
  welfare_variable: string;
  poverty_line: number;
  weight_variable?: string;
  group_by?: string[];
  geography_variable?: string;
}

export interface SpatialPovertyAnalysisRequest {
  dataset_id: string;
  geo_variable: string;
  welfare_variable: string;
  poverty_line: number;
  weight_variable?: string;
  geojson_boundary_file?: string;
}

export interface AnalysisResultResponse {
  job_id: string;
  status: string;
  job_type: string;
  summary_stats?: Record<string, unknown>;
  tables?: Record<string, unknown>;
  charts?: Record<string, unknown>;
  geojson?: Record<string, unknown>;
  interpretation_text?: string;
  error_message?: string;
}

export async function uploadMicrodata(formData: FormData): Promise<MicrodataDataset> {
  const { data } = await api.post<MicrodataDataset>("/microdata/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchMicrodataDatasets(skip = 0, limit = 50): Promise<MicrodataDatasetListResponse> {
  const { data } = await api.get<MicrodataDatasetListResponse>("/microdata/datasets", {
    params: { skip, limit },
  });
  return data;
}

export async function fetchMicrodataVariables(datasetId: string): Promise<MicrodataVariable[]> {
  const { data } = await api.get<MicrodataVariable[]>(`/microdata/datasets/${datasetId}/variables`);
  return data;
}

export async function runPovertyAnalysis(payload: PovertyAnalysisRequest): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>("/microdata/analyze/poverty", payload);
  return data;
}

export async function runSpatialPovertyAnalysis(payload: SpatialPovertyAnalysisRequest): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>("/microdata/analyze/spatial-poverty", payload);
  return data;
}

// ── LSMS Analytics Engine: variable mapping ─────────────────────────────────

export interface VariableMappingEntry {
  standard_concept: string;
  raw_variable_name: string;
  confidence?: number | null;
}

export interface VariableMappingRecord extends VariableMappingEntry {
  id: string;
  dataset_id: string;
  auto_detected: boolean;
}

export async function fetchMicrodataDataset(datasetId: string): Promise<MicrodataDataset> {
  const { data } = await api.get<MicrodataDataset>(`/microdata/datasets/${datasetId}`);
  return data;
}

export async function suggestVariableMapping(datasetId: string): Promise<{ dataset_id: string; suggestions: VariableMappingEntry[] }> {
  const { data } = await api.get(`/microdata/datasets/${datasetId}/mapping/suggest`);
  return data;
}

export async function fetchVariableMapping(datasetId: string): Promise<VariableMappingRecord[]> {
  const { data } = await api.get<VariableMappingRecord[]>(`/microdata/datasets/${datasetId}/mapping`);
  return data;
}

export async function saveVariableMapping(datasetId: string, mappings: VariableMappingEntry[]): Promise<VariableMappingRecord[]> {
  const { data } = await api.post<VariableMappingRecord[]>("/microdata/mapping", {
    dataset_id: datasetId,
    mappings,
  });
  return data;
}

// ── LSMS Analytics Engine: agriculture & diversification ────────────────────

export interface AgricultureAnalysisRequest {
  dataset_id: string;
  weight_variable?: string;
  group_by?: string[];
  geography_variable?: string;
  variable_overrides?: Record<string, string>;
}

export interface DiversificationAnalysisRequest {
  dataset_id: string;
  crop_columns?: string[];
  income_columns?: string[];
  livelihood_columns?: string[];
  livestock_columns?: string[];
  weight_variable?: string;
  group_by?: string[];
}

export async function runAgricultureAnalysis(payload: AgricultureAnalysisRequest): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>("/microdata/analyze/agriculture", payload);
  return data;
}

export async function runDiversificationAnalysis(payload: DiversificationAnalysisRequest): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>("/microdata/analyze/diversification", payload);
  return data;
}

export async function fetchAnalysisResult(jobId: string): Promise<AnalysisResultResponse> {
  const { data } = await api.get<AnalysisResultResponse>(`/microdata/results/${jobId}`);
  return data;
}

export async function generateAIInterpretation(jobId: string, focus?: string): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>("/microdata/ai-interpret", { job_id: jobId, focus });
  return data;
}

// ── Interactive Spatial Explorer: sessions ──────────────────────────────────

export type ExplorerLayer = "poverty" | "agriculture" | "diversification";

export interface ExplorerFilter {
  variable: string;
  op: string; // eq | ne | in | not_in | gt | gte | lt | lte | between | contains
  value: unknown;
}

export interface ExplorerSessionState {
  geo_variable?: string;
  welfare_variable?: string;
  poverty_line?: number;
  weight_variable?: string;
  filters?: ExplorerFilter[];
  variable_overrides?: Record<string, string>;
  crop_columns?: string[];
  income_columns?: string[];
  livelihood_columns?: string[];
  livestock_columns?: string[];
  geojson_boundary_file?: string;
  map_view?: Record<string, unknown>;
  last_job_ids?: Record<string, string>;
  [key: string]: unknown;
}

export interface ExplorerSession {
  id: string;
  name: string;
  owner_id: string;
  dataset_id: string | null;
  country_iso3: string | null;
  admin_level: string | null;
  active_layer: ExplorerLayer;
  state: ExplorerSessionState | null;
  last_result_job_id: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ExplorerSessionCreate {
  name?: string;
  dataset_id?: string | null;
  country_iso3?: string | null;
  admin_level?: string | null;
  active_layer?: ExplorerLayer;
  state?: ExplorerSessionState;
}

export async function createExplorerSession(payload: ExplorerSessionCreate): Promise<ExplorerSession> {
  const { data } = await api.post<ExplorerSession>("/microdata/sessions", payload);
  return data;
}

export async function listExplorerSessions(): Promise<ExplorerSession[]> {
  const { data } = await api.get<ExplorerSession[]>("/microdata/sessions");
  return data;
}

export async function getExplorerSession(sessionId: string): Promise<ExplorerSession> {
  const { data } = await api.get<ExplorerSession>(`/microdata/sessions/${sessionId}`);
  return data;
}

export async function updateExplorerSession(
  sessionId: string,
  patch: Partial<ExplorerSessionCreate>,
): Promise<ExplorerSession> {
  const { data } = await api.patch<ExplorerSession>(`/microdata/sessions/${sessionId}`, patch);
  return data;
}

export async function deleteExplorerSession(sessionId: string): Promise<void> {
  await api.delete(`/microdata/sessions/${sessionId}`);
}

export async function runExplorerSession(
  sessionId: string,
  overrides?: { active_layer?: ExplorerLayer; state?: ExplorerSessionState },
): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>(
    `/microdata/sessions/${sessionId}/run`,
    overrides ?? {},
  );
  return data;
}

export async function fetchExplorerSessionResult(sessionId: string): Promise<AnalysisResultResponse> {
  const { data } = await api.get<AnalysisResultResponse>(`/microdata/sessions/${sessionId}/result`);
  return data;
}

// ── AI Policy Brief ─────────────────────────────────────────────────────────

export interface PolicyBriefQA {
  question: string;
  answer: string;
}

export interface PolicyBriefSection {
  heading: string;
  body: string;
}

export interface PolicyBrief {
  job_id: string;
  title: string;
  audience: string;
  domain: string;
  generated_at: string;
  summary: string;
  key_findings: string[];
  recommendations: string[];
  qa: PolicyBriefQA[];
  sections: PolicyBriefSection[];
  markdown: string;
}

export interface PolicyBriefRequest {
  job_id: string;
  title?: string;
  audience?: string;
  questions?: string[];
}

export async function generatePolicyBrief(payload: PolicyBriefRequest): Promise<PolicyBrief> {
  const { data } = await api.post<PolicyBrief>("/microdata/policy-brief", payload);
  return data;
}

// ── AIC Intelligence: conversational, automated analysis ────────────────────

export interface IntelligenceCleaningStep {
  kind: string;
  label: string;
  columns?: string[];
  column?: string;
  strategy?: string;
  lower?: number;
  upper?: number;
  op?: string;
  value?: number;
}

export interface IntelligencePlan {
  analysis: string;
  analysis_label: string;
  endpoint: string;
  parameters: Record<string, unknown>;
  cleaning_steps: IntelligenceCleaningStep[];
  rationale: string;
  warnings: string[];
  engine: string;
  needs_clarification: boolean;
  clarification?: string | null;
}

export interface IntelligenceCleanResponse {
  cleaned_dataset_id: string;
  cleaned_dataset_name: string;
  report: string[];
  row_count: number;
  column_count: number;
}

export async function planIntelligence(datasetId: string, question: string): Promise<IntelligencePlan> {
  const { data } = await api.post<IntelligencePlan>("/intelligence/plan", {
    dataset_id: datasetId,
    question,
  });
  return data;
}

export async function cleanIntelligence(
  datasetId: string,
  cleaningSteps: IntelligenceCleaningStep[],
): Promise<IntelligenceCleanResponse> {
  const { data } = await api.post<IntelligenceCleanResponse>("/intelligence/clean", {
    dataset_id: datasetId,
    cleaning_steps: cleaningSteps,
  });
  return data;
}

// Generic runner so all six analyses (plain + spatial) work uniformly.
export async function runIntelligenceAnalysis(
  endpoint: string,
  datasetId: string,
  parameters: Record<string, unknown>,
): Promise<AnalysisResultResponse> {
  const { data } = await api.post<AnalysisResultResponse>(`/microdata/analyze/${endpoint}`, {
    dataset_id: datasetId,
    ...parameters,
  });
  return data;
}

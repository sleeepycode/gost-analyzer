import { getAccessToken } from '@/api/authStorage';

export type DownloadFormat = 'pdf' | 'docx';

export type AuthResponse = {
  user_id: string;
  email: string;
  display_name?: string | null;
  access_token: string;
  token_type?: string;
};

/**
 * База REST API без завершающего слэша.
 * По умолчанию — тот же origin (backend :8002 раздаёт и API, и статику фронта).
 * Для отдельного dev-сервера задайте VITE_API_BASE_URL в .env.
 */
export function getApiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL?.trim();
  if (raw) return raw.replace(/\/+$/, '');
  return '';
}

async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(init?.headers);
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  try {
    return await fetch(input, { ...init, headers });
  } catch (e) {
    if (e instanceof TypeError) {
      throw new Error('Не удалось выполнить запрос. Попробуйте позже.');
    }
    throw e;
  }
}

export async function authLogin(email: string, password: string): Promise<AuthResponse> {
  const res = await apiFetch(`${getApiBase()}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
  });
  return parseJsonOrThrow(res) as Promise<AuthResponse>;
}

export async function authRegister(email: string, password: string): Promise<AuthResponse> {
  const res = await apiFetch(`${getApiBase()}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
  });
  return parseJsonOrThrow(res) as Promise<AuthResponse>;
}

export async function authMe(): Promise<AuthResponse> {
  const res = await apiFetch(`${getApiBase()}/auth/me`);
  const data = (await parseJsonOrThrow(res)) as {
    user_id: string;
    email: string;
    display_name?: string | null;
  };
  const token = getAccessToken();
  if (!token) throw new Error('Сессия не найдена');
  return {
    user_id: data.user_id,
    email: data.email,
    display_name: data.display_name,
    access_token: token,
  };
}

export type ExtractResponse = {
  paragraphs: string[];
  tables: string[][][];
  images: string[];
};

export type DraftBlockType = 'paragraph' | 'heading' | 'image' | 'table' | 'page_break';

export type DraftBlock = {
  id: string;
  type: DraftBlockType;
  text?: string | null;
  image_id?: string | null;
  caption?: string | null;
  rows?: string[][] | null;
};

export type DraftSection = {
  id: string;
  title: string;
  blocks: DraftBlock[];
};

export type DraftTitlePage = {
  faculty: string;
  department: string;
  student_group: string;
  lab_title: string;
  lab_number: string;
  student_name: string;
  reviewer_name: string;
  discipline: string;
};

export type DocumentDraft = {
  schema_version: number;
  project_id: string;
  source_type: 'blank' | 'docx';
  title_page: DraftTitlePage;
  sections: DraftSection[];
  bibliography: string[];
  images: Array<Record<string, unknown>>;
  settings: Record<string, unknown>;
  version: number;
};

export type BlankProjectResponse = {
  project_id: string;
  user_id: string;
  source_type: 'blank';
  status: string;
  title: string;
};

export type ProjectDraftResponse = {
  project_id: string;
  source_type: 'blank' | 'docx';
  version: number;
  draft: DocumentDraft;
};

export type ProjectUploadResponse = {
  project_id: string;
  status: string;
  source_filename: string;
};

export type ProjectProcessResponse = {
  project_id: string;
  task_id: string;
  status: string;
  report: Record<string, unknown>;
};

export type ProjectStatusResponse = {
  project_id: string;
  user_id?: string | null;
  status: string;
  source_type: 'blank' | 'docx';
  source_filename?: string | null;
  created_at: string;
  updated_at: string;
};

export type ImageSuggestion = {
  id: string;
  image_name: string;
  image_type: string;
  ocr_text: string;
  ocr_status?: string;
  ocr_error?: string;
  keywords: string[];
  suggested_insertion: string;
  caption: string;
  applied?: boolean;
};

export type ProjectSuggestionsResponse = {
  project_id: string;
  status: string;
  suggestions: ImageSuggestion[];
};

export type ProjectAnalysisResponse = {
  project_id: string;
  status: string;
  analysis: Record<string, unknown>;
};

export type ApiHealthResponse = {
  status: string;
};

export async function getApiHealth(signal?: AbortSignal): Promise<ApiHealthResponse> {
  const res = await apiFetch(`${getApiBase()}/health`, { signal });
  return parseJsonOrThrow(res) as Promise<ApiHealthResponse>;
}

export async function createBlankProject(userId: string, title: string): Promise<BlankProjectResponse> {
  const res = await apiFetch(`${getApiBase()}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, title: title.trim() }),
  });
  return parseJsonOrThrow(res) as Promise<BlankProjectResponse>;
}

export async function getProjectDraft(projectId: string, userId: string): Promise<ProjectDraftResponse> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/draft?${q}`);
  return parseJsonOrThrow(res) as Promise<ProjectDraftResponse>;
}

export async function updateProjectDraft(
  projectId: string,
  userId: string,
  version: number,
  draft: DocumentDraft,
): Promise<ProjectDraftResponse> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/draft?${q}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version, draft }),
  });
  return parseJsonOrThrow(res) as Promise<ProjectDraftResponse>;
}

async function parseJsonOrThrow(res: Response): Promise<unknown> {
  const text = await res.text();
  let body: unknown;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { message: text };
  }
  if (!res.ok) {
    const o = typeof body === 'object' && body !== null ? (body as Record<string, unknown>) : null;
    let msg = 'Не удалось выполнить запрос. Попробуйте ещё раз.';
    if (o && 'message' in o && o.message != null) msg = String(o.message);
    else if (o && typeof o.detail === 'string') msg = o.detail;
    else if (Array.isArray(o?.detail) && o.detail.length > 0) {
      const first = o.detail[0] as { msg?: string };
      if (first?.msg) msg = first.msg;
    }
    throw new Error(msg);
  }
  return body;
}

export async function uploadProject(
  file: File,
  userId: string | undefined,
): Promise<ProjectUploadResponse> {
  const fd = new FormData();
  fd.append('file', file);
  if (userId) fd.append('user_id', userId);
  const res = await apiFetch(`${getApiBase()}/projects/upload`, {
    method: 'POST',
    body: fd,
  });
  return parseJsonOrThrow(res) as Promise<ProjectUploadResponse>;
}

export async function getProject(projectId: string): Promise<ProjectStatusResponse> {
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}`);
  return parseJsonOrThrow(res) as Promise<ProjectStatusResponse>;
}

export async function uploadProjectFile(
  projectId: string,
  file: File,
  userId: string,
): Promise<{ project_id?: string; status?: string; file_path: string; file_type: string }> {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('user_id', userId);
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/files`, {
    method: 'POST',
    body: fd,
  });
  return parseJsonOrThrow(res) as Promise<{
    project_id?: string;
    status?: string;
    file_path: string;
    file_type: string;
  }>;
}

export type ProcessPayload = {
  faculty: string;
  department: string;
  student_group: string;
  lab_title: string;
  lab_number: string;
  student_name: string;
  reviewer_name: string;
  discipline: string;
};

export async function processProject(
  projectId: string,
  userId: string,
  payload: ProcessPayload,
): Promise<ProjectProcessResponse> {
  const fd = new FormData();
  fd.append('user_id', userId);
  fd.append('faculty', payload.faculty);
  fd.append('department', payload.department);
  fd.append('student_group', payload.student_group);
  fd.append('lab_title', payload.lab_title);
  fd.append('lab_number', payload.lab_number);
  fd.append('student_name', payload.student_name);
  fd.append('reviewer_name', payload.reviewer_name);
  fd.append('discipline', payload.discipline);
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/process`, {
    method: 'POST',
    body: fd,
  });
  return parseJsonOrThrow(res) as Promise<ProjectProcessResponse>;
}

export async function getSuggestions(
  projectId: string,
  userId: string,
): Promise<ProjectSuggestionsResponse> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/suggestions?${q}`);
  return parseJsonOrThrow(res) as Promise<ProjectSuggestionsResponse>;
}

export async function applySuggestions(
  projectId: string,
  userId: string,
  suggestionIds: string[],
): Promise<{ applied_ids: string[] }> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/suggestions/apply?${q}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ suggestion_ids: suggestionIds }),
  });
  return parseJsonOrThrow(res) as Promise<{ applied_ids: string[] }>;
}

export async function getProjectAnalysis(
  projectId: string,
  userId: string,
): Promise<ProjectAnalysisResponse> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/analysis?${q}`);
  return parseJsonOrThrow(res) as Promise<ProjectAnalysisResponse>;
}

export async function extractDocx(file: File, userId: string | undefined): Promise<ExtractResponse> {
  const fd = new FormData();
  fd.append('file', file);
  if (userId) fd.append('user_id', userId);
  const res = await apiFetch(`${getApiBase()}/tasks/extract`, { method: 'POST', body: fd });
  return parseJsonOrThrow(res) as Promise<ExtractResponse>;
}

export async function fetchTaskReportJson(
  taskId: string,
  userId: string,
): Promise<Record<string, unknown>> {
  const q = new URLSearchParams({ user_id: userId });
  const res = await apiFetch(`${getApiBase()}/tasks/${taskId}/report?${q}`);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json() as Promise<Record<string, unknown>>;
}

export async function downloadProjectBlob(
  projectId: string,
  userId: string,
  format: DownloadFormat,
): Promise<{ blob: Blob; filename: string }> {
  const q = new URLSearchParams({ user_id: userId, format });
  const res = await apiFetch(`${getApiBase()}/projects/${projectId}/download?${q}`);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  const cd = res.headers.get('Content-Disposition');
  let filename = `${projectId}_result.${format}`;
  const m = cd?.match(/filename="?([^";]+)"?/i);
  if (m) filename = m[1];
  const blob = await res.blob();
  return { blob, filename };
}

export async function listTasks(userId: string, limit = 10) {
  const q = new URLSearchParams({ user_id: userId, limit: String(limit) });
  const res = await apiFetch(`${getApiBase()}/tasks?${q}`);
  return parseJsonOrThrow(res) as Promise<{
    items: Array<{
      task_id: string;
      status: string;
      original_filename: string;
      created_at: string;
      has_output: boolean;
    }>;
  }>;
}

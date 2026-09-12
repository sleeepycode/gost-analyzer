import type { ExtractResponse, ProcessPayload } from '@/api/client';

const STORAGE_KEY = 'oform_wizard_session_v1';

export type WizardSession = {
  userId: string;
  projectId: string;
  sourceFilename: string;
  step: number;
  maxReachedStep: number;
  payload: ProcessPayload;
  extracted: ExtractResponse | null;
  selectedIds: string[];
  report: Record<string, unknown> | null;
  processingStarted: boolean;
};

export function loadWizardSession(userId: string): WizardSession | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as WizardSession;
    if (parsed.userId !== userId) return null;
    if (typeof parsed.projectId !== 'string' || !parsed.projectId) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveWizardSession(session: WizardSession) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearWizardSession(userId?: string) {
  if (!userId) {
    sessionStorage.removeItem(STORAGE_KEY);
    return;
  }
  const current = loadWizardSession(userId);
  if (!current || current.userId === userId) {
    sessionStorage.removeItem(STORAGE_KEY);
  }
}

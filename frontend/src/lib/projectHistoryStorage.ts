const STORAGE_KEY = 'oform_project_history_v1';
const MAX_ENTRIES = 40;

export type ProjectHistoryEntry = {
  projectId: string;
  userId: string;
  title: string;
  filename: string;
  status: 'completed';
  updatedAt: string;
};

function loadAll(): ProjectHistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (e): e is ProjectHistoryEntry =>
        typeof e === 'object' &&
        e !== null &&
        typeof (e as ProjectHistoryEntry).projectId === 'string' &&
        typeof (e as ProjectHistoryEntry).userId === 'string' &&
        typeof (e as ProjectHistoryEntry).title === 'string' &&
        typeof (e as ProjectHistoryEntry).filename === 'string' &&
        (e as ProjectHistoryEntry).status === 'completed' &&
        typeof (e as ProjectHistoryEntry).updatedAt === 'string',
    );
  } catch {
    return [];
  }
}

function saveAll(entries: ProjectHistoryEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function listProjectHistory(userId: string): ProjectHistoryEntry[] {
  return loadAll()
    .filter((e) => e.userId === userId)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function upsertProjectHistory(entry: Omit<ProjectHistoryEntry, 'updatedAt'> & { updatedAt?: string }) {
  const next: ProjectHistoryEntry = {
    ...entry,
    updatedAt: entry.updatedAt ?? new Date().toISOString(),
  };
  const rest = loadAll().filter((e) => !(e.projectId === next.projectId && e.userId === next.userId));
  const merged = [next, ...rest].slice(0, MAX_ENTRIES);
  saveAll(merged);
}

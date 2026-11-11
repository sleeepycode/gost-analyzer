import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  createBlankProject,
  getProjectDraft,
  updateProjectDraft,
  type DocumentDraft,
} from '@/api/client';
import { ReportEditor } from '@/components/ReportEditor';
import { useAuth } from '@/context/AuthContext';

export function BlankReportPage() {
  const { user } = useAuth();
  const [title, setTitle] = useState('');
  const [projectId, setProjectId] = useState<string | null>(null);
  const [draft, setDraft] = useState<DocumentDraft | null>(null);
  const [version, setVersion] = useState(1);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function startProject() {
    if (!user || !title.trim()) {
      setError('Введите название работы.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const created = await createBlankProject(user.userId, title);
      const loaded = await getProjectDraft(created.project_id, user.userId);
      setProjectId(created.project_id);
      setDraft(loaded.draft);
      setVersion(loaded.version);
      setMessage('Черновик создан.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать проект.');
    } finally {
      setBusy(false);
    }
  }

  async function saveDraft() {
    if (!user || !projectId || !draft) return;
    setBusy(true);
    setError('');
    try {
      const saved = await updateProjectDraft(projectId, user.userId, version, draft);
      setDraft(saved.draft);
      setVersion(saved.version);
      setMessage('Черновик сохранён.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить черновик.');
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className="card-panel mx-auto max-w-lg p-8 text-center">
        <p className="text-zinc-600">Войдите в аккаунт, чтобы создать отчёт.</p>
        <Link className="mt-4 inline-block font-medium text-brand" to="/login">
          Перейти к авторизации
        </Link>
      </div>
    );
  }

  if (!projectId || !draft) {
    return (
      <div className="card-panel mx-auto max-w-2xl p-6 md:p-8">
        <Link to="/" className="text-sm font-medium text-zinc-500 hover:text-brand">
          ← Главная
        </Link>
        <h1 className="mt-5 text-2xl font-bold text-zinc-900">Создать отчёт с нуля</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Начните с названия работы. Файл DOCX для этого режима не требуется.
        </p>
        <label className="mt-6 block text-sm font-medium text-zinc-700">
          Название работы
          <input
            className="input-field mt-2"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Например: Исследование алгоритмов сортировки"
            disabled={busy}
          />
        </label>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <button type="button" className="btn-primary mt-6" onClick={() => void startProject()} disabled={busy}>
          {busy ? 'Создание…' : 'Начать редактирование'}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/" className="text-sm font-medium text-zinc-500 hover:text-brand">
            ← Главная
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-zinc-900">Редактор отчёта</h1>
          <p className="mt-1 text-sm text-zinc-500">Проект: {projectId}</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => void saveDraft()} disabled={busy}>
          {busy ? 'Сохранение…' : 'Сохранить черновик'}
        </button>
      </div>

      {message && <div className="card-panel-muted text-emerald-700">{message}</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="card-panel p-6 md:p-8">
        <ReportEditor draft={draft} projectId={projectId} userId={user.userId} onChange={setDraft} />
      </div>

      <p className="text-sm text-zinc-500">
        Сборка DOCX/PDF будет подключена на следующем этапе через Doc Service.
      </p>
    </div>
  );
}

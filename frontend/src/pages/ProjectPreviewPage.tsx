import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { downloadProjectBlob } from '@/api/client';
import { DocxPreview } from '@/components/DocxPreview';
import { useAuth } from '@/context/AuthContext';
import { listProjectHistory } from '@/lib/projectHistoryStorage';

export function ProjectPreviewPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useAuth();
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const meta = user && projectId ? listProjectHistory(user.userId).find((e) => e.projectId === projectId) : undefined;

  useEffect(() => {
    if (!user?.userId || !projectId) {
      setPreviewBlob(null);
      return;
    }
    let cancelled = false;
    setErr('');
    setBusy(true);
    void downloadProjectBlob(projectId, user.userId, 'docx')
      .then(({ blob }) => {
        if (!cancelled) setPreviewBlob(blob);
      })
      .catch((e) => {
        if (!cancelled) {
          setPreviewBlob(null);
          setErr(e instanceof Error ? e.message : 'Не удалось загрузить документ');
        }
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user, projectId]);

  if (!user) {
    return (
      <div className="card-panel mx-auto max-w-lg p-8 text-center">
        <p className="text-zinc-600">Войдите в аккаунт, чтобы открыть проект.</p>
        <Link className="mt-4 inline-block font-medium text-brand" to="/login">
          Перейти к авторизации
        </Link>
      </div>
    );
  }

  if (!projectId) {
    return (
      <div className="card-panel mx-auto max-w-lg p-8 text-center">
        <p className="text-zinc-600">Проект не указан.</p>
        <Link className="mt-4 inline-block font-medium text-brand" to="/">
          На главную
        </Link>
      </div>
    );
  }

  const heading = meta?.title.trim() || meta?.filename || 'Проект';

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <Link to="/" className="text-sm font-medium text-zinc-500 hover:text-brand">
          ← Главная
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-zinc-900">{heading}</h1>
      </div>

      <div className="card-panel p-6 md:p-8">
        {err && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{err}</div>
        )}
        {busy && <p className="mb-4 text-sm text-zinc-500">Загрузка документа…</p>}
        <h2 className="mb-4 text-lg font-semibold text-zinc-900">Предпросмотр</h2>
        <DocxPreview blob={previewBlob} />
      </div>
    </div>
  );
}

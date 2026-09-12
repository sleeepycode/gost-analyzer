import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { listProjectHistory, type ProjectHistoryEntry } from '@/lib/projectHistoryStorage';

const itemCls = ({ isActive }: { isActive: boolean }) =>
  `block truncate rounded-lg px-2 py-1.5 text-left text-xs transition ${
    isActive ? 'bg-violet-100 font-medium text-brand-dark' : 'text-zinc-600 hover:bg-white/80 hover:text-zinc-900'
  }`;

type HistoryToggleProps = {
  open: boolean;
  onToggle: () => void;
};

export function HistoryToggleButton({ open, onToggle }: HistoryToggleProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      title="История"
      aria-expanded={open}
      aria-label="История"
      className={`flex items-center rounded-xl transition-all ${
        open
          ? 'w-full gap-2 bg-brand px-3 py-2 text-white shadow-md shadow-brand/30'
          : 'h-11 w-11 justify-center text-zinc-500 hover:bg-white/80 hover:text-brand-dark'
      }`}
    >
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path d="M12 8v4l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      {open && <span className="truncate text-xs font-semibold">История</span>}
    </button>
  );
}

type HistoryPanelProps = {
  open: boolean;
};

export function ProjectHistoryPanel({ open }: HistoryPanelProps) {
  const { user } = useAuth();
  const [items, setItems] = useState<ProjectHistoryEntry[]>([]);

  useEffect(() => {
    if (!user) {
      setItems([]);
      return;
    }
    const refresh = () => setItems(listProjectHistory(user.userId));
    refresh();
    window.addEventListener('oform:project-history', refresh);
    return () => window.removeEventListener('oform:project-history', refresh);
  }, [user]);

  if (!user || !open) return null;

  return (
    <nav
      className="mt-2 w-full flex-col gap-1 border-t border-violet-100/80 pt-3 md:flex"
      aria-label="История проектов"
    >
      <p className="px-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-400">История</p>
      {items.length === 0 ? (
        <p className="px-2 py-2 text-xs leading-relaxed text-zinc-500">Тут пока пусто</p>
      ) : (
        <ul className="max-h-[min(50vh,320px)] space-y-0.5 overflow-y-auto">
          {items.map((e) => (
            <li key={e.projectId}>
              <NavLink to={`/project/${e.projectId}`} className={itemCls} title={e.title || e.filename}>
                {e.title.trim() || e.filename}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}

export function notifyProjectHistoryChanged() {
  window.dispatchEvent(new Event('oform:project-history'));
}

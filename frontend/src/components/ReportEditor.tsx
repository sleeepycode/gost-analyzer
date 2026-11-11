import { useState } from 'react';
import { uploadProjectFile, type DocumentDraft, type DraftBlock, type DraftSection } from '@/api/client';

type ReportEditorProps = {
  draft: DocumentDraft;
  projectId: string;
  userId: string;
  onChange: (draft: DocumentDraft) => void;
};

function makeBlockId(sectionId: string) {
  return `${sectionId}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function updateSection(draft: DocumentDraft, sectionId: string, update: (section: DraftSection) => DraftSection) {
  return {
    ...draft,
    sections: draft.sections.map((section) => (section.id === sectionId ? update(section) : section)),
  };
}

export function ReportEditor({ draft, projectId, userId, onChange }: ReportEditorProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  function updateTitle(value: string) {
    onChange({
      ...draft,
      title_page: { ...draft.title_page, lab_title: value },
    });
  }

  function updateSectionTitle(sectionId: string, value: string) {
    onChange(updateSection(draft, sectionId, (section) => ({ ...section, title: value })));
  }

  function updateBlock(sectionId: string, blockId: string, value: string) {
    onChange(
      updateSection(draft, sectionId, (section) => ({
        ...section,
        blocks: section.blocks.map((block) => (block.id === blockId ? { ...block, text: value } : block)),
      })),
    );
  }

  function addParagraph(sectionId: string) {
    const nextBlock: DraftBlock = {
      id: makeBlockId(sectionId),
      type: 'paragraph',
      text: '',
    };
    onChange(updateSection(draft, sectionId, (section) => ({ ...section, blocks: [...section.blocks, nextBlock] })));
  }

  function addHeading(sectionId: string) {
    const nextBlock: DraftBlock = {
      id: makeBlockId(sectionId),
      type: 'heading',
      text: '',
    };
    onChange(updateSection(draft, sectionId, (section) => ({ ...section, blocks: [...section.blocks, nextBlock] })));
  }

  function addTable(sectionId: string) {
    const nextBlock: DraftBlock = {
      id: makeBlockId(sectionId),
      type: 'table',
      rows: [ ['', ''], ['', ''] ],
    };
    onChange(updateSection(draft, sectionId, (section) => ({ ...section, blocks: [...section.blocks, nextBlock] })));
  }

  function updateTableCell(sectionId: string, blockId: string, rowIndex: number, cellIndex: number, value: string) {
    onChange(
      updateSection(draft, sectionId, (section) => ({
        ...section,
        blocks: section.blocks.map((block) => {
          if (block.id !== blockId || block.type !== 'table') return block;
          const rows = (block.rows ?? []).map((row) => [...row]);
          if (!rows[rowIndex]) rows[rowIndex] = [];
          rows[rowIndex][cellIndex] = value;
          return { ...block, rows };
        }),
      })),
    );
  }

  async function uploadImage(sectionId: string, file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setUploadError('');
    try {
      const uploaded = await uploadProjectFile(projectId, file, userId);
      const imageId = `${file.name}-${Date.now()}`;
      const imageBlock: DraftBlock = {
        id: makeBlockId(sectionId),
        type: 'image',
        image_id: imageId,
        caption: file.name,
      };
      onChange(
        updateSection(
          {
            ...draft,
            images: [
              ...draft.images,
              { image_id: imageId, filename: file.name, path: uploaded.file_path, source: 'editor_upload' },
            ],
          },
          sectionId,
          (section) => ({ ...section, blocks: [...section.blocks, imageBlock] }),
        ),
      );
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Не удалось загрузить изображение.');
    } finally {
      setUploading(false);
    }
  }

  function removeBlock(sectionId: string, blockId: string) {
    onChange(
      updateSection(draft, sectionId, (section) => ({
        ...section,
        blocks: section.blocks.filter((block) => block.id !== blockId),
      })),
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700">Название работы</label>
        <input
          className="input-field"
          value={draft.title_page.lab_title}
          onChange={(event) => updateTitle(event.target.value)}
          placeholder="Например: Исследование алгоритмов сортировки"
        />
      </div>

      <div className="space-y-5">
        {draft.sections.map((section) => (
          <section key={section.id} className="rounded-2xl border border-violet-100 bg-white/70 p-5">
            <input
              className="mb-4 w-full border-0 bg-transparent text-lg font-semibold text-zinc-900 outline-none focus:ring-0"
              value={section.title}
              onChange={(event) => updateSectionTitle(section.id, event.target.value)}
              aria-label={`Название раздела ${section.id}`}
            />

            <div className="space-y-3">
              {section.blocks.length === 0 && (
                <p className="rounded-xl bg-violet-50/70 px-4 py-3 text-sm text-zinc-500">
                  В этом разделе пока нет текста.
                </p>
              )}
              {section.blocks.map((block) => (
                <div key={block.id} className="flex gap-2">
                  {block.type === 'table' ? (
                    <div className="min-w-0 flex-1 overflow-x-auto rounded-xl border border-zinc-200 p-3">
                      <table className="w-full border-collapse text-sm">
                        <tbody>
                          {(block.rows ?? []).map((row, rowIndex) => (
                            <tr key={`${block.id}-${rowIndex}`}>
                              {row.map((cell, cellIndex) => (
                                <td key={`${block.id}-${rowIndex}-${cellIndex}`} className="border border-zinc-200 p-1">
                                  <input
                                    className="w-full px-2 py-1 outline-none focus:ring-1 focus:ring-brand/30"
                                    value={cell}
                                    onChange={(event) =>
                                      updateTableCell(section.id, block.id, rowIndex, cellIndex, event.target.value)
                                    }
                                    placeholder="Ячейка"
                                  />
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : block.type === 'image' ? (
                    <div className="min-w-0 flex-1 rounded-xl border border-violet-100 bg-violet-50/50 px-4 py-3 text-sm">
                      <p className="font-medium text-zinc-800">Изображение добавлено</p>
                      <p className="mt-1 text-xs text-zinc-500">{block.caption || block.image_id}</p>
                    </div>
                  ) : (
                    <textarea
                      className={`input-field min-h-28 resize-y ${block.type === 'heading' ? 'min-h-16 font-semibold' : ''}`}
                      value={block.text ?? ''}
                      onChange={(event) => updateBlock(section.id, block.id, event.target.value)}
                      placeholder={block.type === 'heading' ? 'Введите заголовок' : 'Введите текст абзаца'}
                    />
                  )}
                  <button
                    type="button"
                    className="self-start rounded-lg px-2 py-2 text-sm text-zinc-400 hover:bg-red-50 hover:text-red-600"
                    onClick={() => removeBlock(section.id, block.id)}
                    aria-label="Удалить абзац"
                    title="Удалить абзац"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" className="btn-secondary px-4 py-2" onClick={() => addParagraph(section.id)}>
                + Абзац
              </button>
              <button type="button" className="btn-secondary px-4 py-2" onClick={() => addHeading(section.id)}>
                + Заголовок
              </button>
              <button type="button" className="btn-secondary px-4 py-2" onClick={() => addTable(section.id)}>
                + Таблица
              </button>
              <label className={`btn-secondary cursor-pointer px-4 py-2 ${uploading ? 'pointer-events-none opacity-50' : ''}`}>
                {uploading ? 'Загрузка…' : '+ Изображение'}
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg"
                  className="hidden"
                  disabled={uploading}
                  onChange={(event) => {
                    void uploadImage(section.id, event.target.files?.[0]);
                    event.currentTarget.value = '';
                  }}
                />
              </label>
            </div>
          </section>
        ))}
      </div>
      {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}
    </div>
  );
}

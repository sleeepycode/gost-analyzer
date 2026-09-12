const PREVIEW_TEXT_COLOR = '#18181b';

const THEME_COLOR_VARS = [
  'accent1',
  'accent2',
  'accent3',
  'accent4',
  'accent5',
  'accent6',
  'dark1',
  'dark2',
  'light1',
  'light2',
  'hyperlink',
  'followedHyperlink',
  'text1',
  'text2',
  'background1',
  'background2',
] as const;

const SKIP_TAGS = new Set(['IMG', 'SVG', 'STYLE', 'META', 'LINK']);

function patchStyleTags(host: HTMLElement) {
  host.querySelectorAll('style').forEach((styleEl) => {
    if (styleEl.dataset.oformDocxOverride === '1') return;
    const css = styleEl.textContent;
    if (!css) return;

    let next = css
      .replace(/background:\s*gray/gi, 'background: white')
      .replace(/box-shadow:\s*0\s+0\s+10px[^;]+;/gi, 'box-shadow: none;')
      .replace(/margin-bottom:\s*30px/gi, 'margin-bottom: 0')
      .replace(/padding:\s*30px/gi, 'padding: 0')
      .replace(/padding-bottom:\s*0px/gi, 'padding-bottom: 0');

    // Word/docx-preview: color через theme vars и стили абзацев
    next = next.replace(/\bcolor\s*:\s*[^;]+;/gi, `color: ${PREVIEW_TEXT_COLOR};`);

    styleEl.textContent = next;
  });
}

function overrideThemeVariables(el: HTMLElement) {
  for (const name of THEME_COLOR_VARS) {
    el.style.setProperty(`--docx-${name}-color`, PREVIEW_TEXT_COLOR);
  }
}

function forceTextColor(host: HTMLElement) {
  host.querySelectorAll<HTMLElement>('.docx-wrapper, .docx-wrapper *').forEach((el) => {
    if (SKIP_TAGS.has(el.tagName)) return;
    el.style.setProperty('color', PREVIEW_TEXT_COLOR, 'important');
  });
}

function appendOverrideStyle(host: HTMLElement) {
  host.querySelectorAll('style[data-oform-docx-override="1"]').forEach((el) => el.remove());

  const override = document.createElement('style');
  override.dataset.oformDocxOverride = '1';
  override.textContent = `
    .docx-preview-host .docx-wrapper {
      background: #fff !important;
      padding: 0 !important;
      display: block !important;
      color: ${PREVIEW_TEXT_COLOR} !important;
    }
    .docx-preview-host .docx-wrapper > section.docx {
      box-shadow: none !important;
      margin-bottom: 0 !important;
    }
    .docx-preview-host .docx-wrapper,
    .docx-preview-host .docx-wrapper *:not(img):not(svg):not(svg *) {
      color: ${PREVIEW_TEXT_COLOR} !important;
      -webkit-text-fill-color: ${PREVIEW_TEXT_COLOR} !important;
    }
    .docx-preview-host .docx-wrapper a,
    .docx-preview-host .docx-wrapper a:visited,
    .docx-preview-host .docx-wrapper a:hover {
      color: ${PREVIEW_TEXT_COLOR} !important;
      text-decoration: none !important;
    }
  `;
  host.appendChild(override);
}

/** Убирает серые поля, тени между страницами и синие цвета из Word в docx-preview. */
export function normalizeDocxPreview(host: HTMLElement) {
  patchStyleTags(host);

  host.querySelectorAll<HTMLElement>('.docx, .docx-wrapper, section.docx').forEach((el) => {
    overrideThemeVariables(el);
    el.style.setProperty('background', '#fff', 'important');
  });

  host.querySelectorAll<HTMLElement>('.docx-wrapper').forEach((wrapper) => {
    wrapper.style.setProperty('padding', '0', 'important');
    wrapper.style.setProperty('display', 'block', 'important');
  });

  host.querySelectorAll<HTMLElement>('section.docx').forEach((section) => {
    section.style.setProperty('box-shadow', 'none', 'important');
    section.style.setProperty('margin-bottom', '0', 'important');
  });

  appendOverrideStyle(host);
  forceTextColor(host);
}

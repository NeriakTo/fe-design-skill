// tweaks_panel.mjs — 即時設計變體切換面板
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.4)

const PANEL_STYLES = `
.tweaks-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 280px;
  height: 100vh;
  background: var(--tweaks-bg, #1e293b);
  color: var(--tweaks-text, #e2e8f0);
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 12px;
  padding: 16px;
  overflow-y: auto;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 9999;
  box-shadow: -4px 0 20px rgba(0,0,0,0.3);
}
.tweaks-panel.open { transform: translateX(0); }
.tweaks-toggle {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 10000;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--tweaks-border, #475569);
  background: var(--tweaks-bg, #1e293b);
  color: var(--tweaks-text, #e2e8f0);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: opacity 0.2s;
}
.tweaks-toggle:hover { opacity: 0.8; }
.tweaks-panel.open ~ .tweaks-toggle { right: 292px; }
.tweaks-section { margin-bottom: 16px; }
.tweaks-section-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--tweaks-muted, #94a3b8);
  margin-bottom: 8px;
}
.tweaks-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.tweaks-label { flex: 1; }
.tweaks-input {
  width: 120px;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--tweaks-border, #475569);
  background: var(--tweaks-input-bg, #0f172a);
  color: var(--tweaks-text, #e2e8f0);
  font-family: inherit;
  font-size: 12px;
}
.tweaks-input[type="color"] {
  width: 36px;
  height: 28px;
  padding: 2px;
  cursor: pointer;
}
.tweaks-input[type="range"] { width: 100px; }
.tweaks-select {
  width: 120px;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--tweaks-border, #475569);
  background: var(--tweaks-input-bg, #0f172a);
  color: var(--tweaks-text, #e2e8f0);
  font-family: inherit;
  font-size: 12px;
}
.tweaks-reset {
  width: 100%;
  padding: 8px;
  margin-top: 12px;
  border-radius: 6px;
  border: 1px solid var(--tweaks-border, #475569);
  background: transparent;
  color: var(--tweaks-muted, #94a3b8);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  transition: color 0.2s, border-color 0.2s;
}
.tweaks-reset:hover { color: #ef4444; border-color: #ef4444; }
@media print { .tweaks-panel, .tweaks-toggle { display: none !important; } }
`;

const STORAGE_KEY = 'design-tweaks';

export function TweaksPanel({ tweakDefs, storageKey = STORAGE_KEY }) {
  const id = `tweaks-${Date.now()}`;

  const sections = {};
  for (const def of tweakDefs) {
    const section = def.section || 'General';
    if (!sections[section]) sections[section] = [];
    sections[section].push(def);
  }

  const renderInput = (def) => {
    const val = `\${tweaks['${def.key}']}`;
    switch (def.type) {
      case 'color':
        return `<input type="color" class="tweaks-input" data-tweak="${def.key}" value="${val}">`;
      case 'range':
        return `<input type="range" class="tweaks-input" data-tweak="${def.key}" min="${def.min || 0}" max="${def.max || 100}" step="${def.step || 1}" value="${val}">`;
      case 'select':
        const opts = (def.options || []).map(o =>
          `<option value="${o.value}">${o.label}</option>`
        ).join('');
        return `<select class="tweaks-select" data-tweak="${def.key}">${opts}</select>`;
      case 'boolean':
        return `<input type="checkbox" class="tweaks-input" data-tweak="${def.key}">`;
      default:
        return `<input type="text" class="tweaks-input" data-tweak="${def.key}" value="${val}">`;
    }
  };

  const sectionHTML = Object.entries(sections).map(([name, defs]) => `
    <div class="tweaks-section">
      <div class="tweaks-section-title">${name}</div>
      ${defs.map(def => `
        <div class="tweaks-row">
          <span class="tweaks-label">${def.label}</span>
          ${renderInput(def)}
        </div>
      `).join('')}
    </div>
  `).join('');

  return { html: `
<style>${PANEL_STYLES}</style>
<button class="tweaks-toggle" aria-label="Toggle tweaks panel" onclick="document.getElementById('${id}').classList.toggle('open')">T</button>
<div id="${id}" class="tweaks-panel">
  <div style="font-size:14px;font-weight:600;margin-bottom:16px;">Tweaks</div>
  ${sectionHTML}
  <button class="tweaks-reset" onclick="tweaksReset()">Reset All</button>
</div>
`, script: `
(function() {
  const STORAGE_KEY = '${storageKey}';
  const DEFAULTS = ${JSON.stringify(Object.fromEntries(tweakDefs.map(d => [d.key, d.default])))};
  let tweaks;

  function load() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      tweaks = stored ? { ...DEFAULTS, ...JSON.parse(stored) } : { ...DEFAULTS };
    } catch { tweaks = { ...DEFAULTS }; }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tweaks));
  }

  function apply() {
    for (const [key, value] of Object.entries(tweaks)) {
      document.documentElement.style.setProperty('--tweak-' + key, String(value));
    }
    document.querySelectorAll('[data-tweak]').forEach(el => {
      const key = el.dataset.tweak;
      if (el.type === 'checkbox') el.checked = !!tweaks[key];
      else el.value = tweaks[key];
    });
  }

  function init() {
    load();
    apply();
    document.querySelectorAll('[data-tweak]').forEach(el => {
      const key = el.dataset.tweak;
      const handler = () => {
        tweaks[key] = el.type === 'checkbox' ? el.checked : el.type === 'range' ? Number(el.value) : el.value;
        save();
        apply();
      };
      el.addEventListener('input', handler);
      el.addEventListener('change', handler);
    });
  }

  window.tweaksReset = function() {
    tweaks = { ...DEFAULTS };
    save();
    apply();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
` };
}

export default TweaksPanel;

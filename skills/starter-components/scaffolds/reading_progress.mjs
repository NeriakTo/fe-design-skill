/* ============================================================
 * reading_progress.mjs — fe-design v1.4-short §24.8 P6.7
 *
 * Reading progress bar 標準化（page mode）
 *
 * 用途：page mode 頁面頂端固定 3px 高的閱讀進度條，依 scroll
 *      位置動態更新寬度（0~100%）。
 *
 * 設計原則：
 * - 純 vanilla HTML string（無 React / Vue 依賴）
 * - 樣式引用 design tokens：--color-accent（fallback #0ea5e9）
 * - 整個 component 自包含（HTML + script + style 一併輸出）
 *
 * 使用方式：
 *   import { readingProgressHTML } from '.../scaffolds/reading_progress.mjs';
 *   // 注入到 page mode HTML <body> 開頭：
 *   `<body>${readingProgressHTML}<main>...</main></body>`
 *
 * 依賴：design-tokens-presets/* 任一 preset（提供 --color-accent）
 *      若未引 preset，自動 fallback 到 #0ea5e9（sky-500）
 *
 * 相關規格：fe-design.md §[2/7] page mode、IV22
 * ============================================================ */

export const readingProgressHTML = `
  <div class="reading-progress" id="reading-progress" role="progressbar" aria-label="閱讀進度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"></div>
  <script>
    (function() {
      // F4 fix: singleton guard — 避免重複注入累加 listener
      if (window.__readingProgressBound) return;
      window.__readingProgressBound = true;
      const bar = document.getElementById('reading-progress');
      if (!bar) return;
      const update = () => {
        const h = document.documentElement;
        const max = (h.scrollHeight - h.clientHeight) || 1;
        const pct = Math.max(0, Math.min(100, (h.scrollTop / max) * 100));
        bar.style.width = pct + '%';
        bar.setAttribute('aria-valuenow', String(Math.round(pct)));
      };
      window.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update, { passive: true });
      update();
    })();
  </script>
  <style>
    .reading-progress {
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      width: 0%;
      background: var(--color-accent, #0ea5e9);
      transition: width 0.1s linear;
      z-index: 100;
      pointer-events: none;
    }
    @media (prefers-reduced-motion: reduce) {
      .reading-progress { transition: none; }
    }
    @media print {
      .reading-progress { display: none !important; }
    }
  </style>
`;

export default readingProgressHTML;

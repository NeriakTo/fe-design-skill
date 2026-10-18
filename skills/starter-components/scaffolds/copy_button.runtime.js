/* ============================================================
 * copy_button.runtime.js — fe-design v1.4-short §24.6 P6.5
 *
 * 互動 prompt copy button — runtime
 *
 * 用途：page mode 在 layout 層 `<script src="copy_button.runtime.js" defer></script>`
 *      注入一次。runtime 啟動時掃 .copy-btn 加 click listener。
 *
 * Contract（重要）：
 * - 預設只在 DOMContentLoaded（或 readyState !== 'loading'）時掃描一次
 * - **Static page mode 主用途**：所有 .copy-btn 在 HTML 載入時就存在
 * - **動態插入支援**：透過 `window.initCopyButtons(root)` 顯式呼叫（root 預設 document）
 *   - 例：SPA route 切換、AJAX 載入新內容後 → 呼叫 `window.initCopyButtons(newSection)` 重綁
 *   - 不採用 MutationObserver 自動偵測（避免效能成本與行為不可預期）
 *
 * 防重複機制：
 * - `dataset.bound` flag 雙保險（即使 runtime 或 initCopyButtons() 重複執行也只綁一次）
 *
 * 取文邏輯（兩種模式）：
 * - 首選 `data-text`（spec §24.6 設計）：直接讀屬性內容
 * - 備援 `data-target`（v1.x backward-compat）：讀 #target 元素的 textContent.trim()
 *
 * Empty / missing source 處理：
 * - text === '' 或 target 找不到 / target.textContent.trim() === '' → **直接走 error UX**
 *   不寫入 clipboard（避免清空使用者既有剪貼簿內容卻顯示「已複製」假成功）
 *
 * Success label 邏輯：
 * - `data-success-label` 屬性（首選）；fallback：'✓ 已複製'
 *
 * Reset 時間：1800ms（與 v1.x case 對齊）
 *
 * 相關規格：fe-design.md §[4/7] page mode、IV20
 * ============================================================ */

(function () {
  'use strict';

  function getCopyText(btn) {
    if (btn.dataset.text != null && btn.dataset.text !== '') return btn.dataset.text;
    if (btn.dataset.target) {
      const t = document.getElementById(btn.dataset.target);
      if (t) {
        const trimmed = t.textContent.trim();
        if (trimmed !== '') return trimmed;
      }
    }
    return '';
  }

  function setLabel(btn, lbl, value) {
    if (lbl) lbl.textContent = value;
    else btn.textContent = value;
  }

  function bindButton(btn) {
    if (btn.dataset.bound === 'true') return;
    btn.dataset.bound = 'true';

    btn.addEventListener('click', async function () {
      const text = getCopyText(btn);
      const lbl = btn.querySelector('.copy-btn-label');
      const successLabel = btn.dataset.successLabel || '✓ 已複製';
      const original = lbl ? lbl.textContent : btn.textContent;

      // F2 fix: empty / missing source → 走 error UX，不呼叫 writeText('')
      if (!text) {
        if (typeof console !== 'undefined' && console.warn) {
          console.warn('[copy-btn] No text to copy (data-text empty / data-target missing or empty)', btn);
        }
        setLabel(btn, lbl, '無內容可複製');
        btn.classList.add('copy-error');
        setTimeout(function () {
          setLabel(btn, lbl, original);
          btn.classList.remove('copy-error');
        }, 1800);
        return;
      }

      try {
        await navigator.clipboard.writeText(text);
        setLabel(btn, lbl, successLabel);
        btn.classList.add('copied');
      } catch (e) {
        setLabel(btn, lbl, '請手動複製');
        btn.classList.add('copy-error');
      }

      setTimeout(function () {
        setLabel(btn, lbl, original);
        btn.classList.remove('copied');
        btn.classList.remove('copy-error');
      }, 1800);
    });
  }

  function initCopyButtons(root) {
    const scope = root || document;
    const buttons = scope.querySelectorAll('.copy-btn');
    buttons.forEach(bindButton);
  }

  // F3 fix: expose explicit re-init API for dynamic content
  if (typeof window !== 'undefined') {
    window.initCopyButtons = initCopyButtons;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initCopyButtons(); }, { once: true });
  } else {
    initCopyButtons();
  }
})();

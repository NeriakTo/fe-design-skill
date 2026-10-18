/* ============================================================
 * copy_button.mjs — fe-design v1.4-short §24.6 P6.5
 *
 * 互動 prompt copy button — component template
 *
 * 用途：page mode 內可重複呼叫產出多顆 .copy-btn HTML 字串。runtime
 *      singleton（copy_button.runtime.js）每頁僅注入一次，掃描所有
 *      .copy-btn 並掛上 click listener（dataset.bound 雙保險防重複）。
 *
 * 設計原則：
 * - escapeHtml 顯式定義（避免 ReferenceError）
 * - successLabel 走 data-success-label 屬性（避免 string template 引號逃逸）
 * - component 與 runtime 分檔（template 可重複呼叫，runtime 僅一次）
 *
 * 使用方式：
 *   import { CopyButton } from '.../scaffolds/copy_button.mjs';
 *   const html = `<div class="prompt-box">
 *     ${CopyButton({ text: 'prompt 內容', label: '複製', successLabel: '✓ 已複製' })}
 *     <pre>${escapeHtml(text)}</pre>
 *   </div>`;
 *   // 並在 layout 層 <body> 結尾加：
 *   //   <script src="copy_button.runtime.js" defer></script>
 *
 * 依賴：copy_button.runtime.js（必須注入一次）+ copy_button.css（樣式）
 * 相關規格：fe-design.md §[4/7] page mode、IV20
 * ============================================================ */

export function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function CopyButton({ text, label = '複製', successLabel = '✓ 已複製' } = {}) {
  if (text == null) {
    throw new Error('CopyButton: text is required');
  }
  return `<button class="copy-btn" type="button" data-text="${escapeHtml(text)}" data-success-label="${escapeHtml(successLabel)}" aria-label="${escapeHtml(label)}">
    <span class="copy-btn-label">${escapeHtml(label)}</span>
  </button>`;
}

export default CopyButton;

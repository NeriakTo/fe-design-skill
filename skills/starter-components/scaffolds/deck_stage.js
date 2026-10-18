// deck_stage.js — slide-deck web component
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.2)
//
// Usage:
//   <link rel="stylesheet" href="path/to/your/design-tokens.css">
//   <script type="module" src="path/to/deck_stage.js"></script>
//   <deck-stage>
//     <section class="slide" data-notes="Speaker note for slide 1">Slide 1</section>
//     <section class="slide">Slide 2</section>
//   </deck-stage>
//
// Attributes:
//   width             固定畫布寬（default 1920）
//   height            固定畫布高（default 1080）
//   start-index       初始 slide 索引（default 0；localStorage 會覆寫）
//   no-persist        關閉 localStorage 持久化（boolean attribute）
//   storage-key       自訂 localStorage key（default 「deck-stage:current」）
//   notes-target      Speaker notes window 的 postMessage targetOrigin（default 同源 window.location.origin；
//                      若需跨 origin 須明確 opt-in 為其他 origin 或 「*」）
//
// Keyboard shortcuts:
//   ← / PageUp        上一張
//   → / Space / PageDown  下一張
//   Home / End        第一/最後一張
//   B                 黑屏 toggle
//   P                 列印模式 toggle
//   N                 開啟 speaker notes 視窗
//   數字 + Enter      跳到指定 slide（例：5 Enter）
//
// Public API（fork verifier 友善）:
//   window.__deck.slideCount   → number
//   window.__deck.current      → number (0-based)
//   window.__deck.next()
//   window.__deck.prev()
//   window.__deck.goto(n)
//   window.__deck.togglePrint()
//   window.__deck.toggleBlackout()
//   window.__deck.openNotes()
//
// CSS custom properties（可被 design-tokens.css 覆寫）:
//   --deck-bg          整體背景色（default #0b1326）
//   --deck-canvas-bg   畫布背景色（default #ffffff）
//   --deck-font        字型 family（default system-ui）
//   --deck-counter-bg  右下角計數器背景（default rgba(0,0,0,0.5)）
//   --deck-counter-fg  右下角計數器文字（default #ffffff）

const TAG_NAME = 'deck-stage';
const DEFAULT_STORAGE_KEY = 'deck-stage:current';
const DEFAULT_WIDTH = 1920;
const DEFAULT_HEIGHT = 1080;

const TEMPLATE_HTML = `
  <style>
    :host {
      display: block;
      position: fixed;
      inset: 0;
      background: var(--deck-bg, #0b1326);
      font-family: var(--deck-font, system-ui, -apple-system, "Segoe UI", "Helvetica Neue", sans-serif);
      overflow: hidden;
    }
    .stage {
      position: absolute;
      top: 50%;
      left: 50%;
      width: var(--canvas-w, ${DEFAULT_WIDTH}px);
      height: var(--canvas-h, ${DEFAULT_HEIGHT}px);
      background: var(--deck-canvas-bg, #ffffff);
      transform-origin: center center;
      transform: translate(-50%, -50%) scale(var(--scale, 1));
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    }
    ::slotted(.slide) {
      display: none !important;
      width: 100%;
      height: 100%;
    }
    ::slotted(.slide.active) {
      display: block !important;
    }
    .counter {
      position: absolute;
      right: 16px;
      bottom: 12px;
      padding: 4px 12px;
      border-radius: 9999px;
      background: var(--deck-counter-bg, rgba(0, 0, 0, 0.5));
      color: var(--deck-counter-fg, #ffffff);
      font-size: 14px;
      font-variant-numeric: tabular-nums;
      letter-spacing: 0.04em;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }
    :host([blackout]) .stage,
    :host([blackout]) .counter {
      opacity: 0;
    }
    :host([blackout])::after {
      content: '';
      position: fixed;
      inset: 0;
      background: #000;
    }
    @media print {
      :host {
        position: static;
        background: transparent;
      }
      .stage {
        position: static;
        transform: none;
        width: 100%;
        height: auto;
        box-shadow: none;
        page-break-after: always;
      }
      ::slotted(.slide) {
        display: block !important;
        page-break-after: always;
      }
      .counter {
        display: none;
      }
    }
  </style>
  <div class="stage" part="stage">
    <slot></slot>
  </div>
  <div class="counter" part="counter" aria-live="polite"></div>
`;

class DeckStage extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' }).innerHTML = TEMPLATE_HTML;
    this._slides = [];
    this._current = 0;
    this._stage = null;
    this._counter = null;
    this._slotEl = null;
    this._notesWindow = null;
    this._numberBuffer = '';
    this._numberBufferTimer = null;
    this._resizeObserver = null;
    this._slotChangeHandler = this._collectSlides.bind(this);
    this._keyHandler = this._onKeydown.bind(this);
    this._resizeHandler = this._fitToViewport.bind(this);
  }

  static get observedAttributes() {
    return ['width', 'height'];
  }

  attributeChangedCallback(name) {
    if (name === 'width' || name === 'height') {
      this._applyCanvasSize();
      this._fitToViewport();
    }
  }

  connectedCallback() {
    this._stage = this.shadowRoot.querySelector('.stage');
    this._counter = this.shadowRoot.querySelector('.counter');
    this._slotEl = this.shadowRoot.querySelector('slot');
    this._slotEl.addEventListener('slotchange', this._slotChangeHandler);

    this._applyCanvasSize();
    /* TASK（2026-09-14）：_current 必須在 _collectSlides() 之前先讀好。
       _collectSlides() 在沒有任何 .active 的情況下會呼叫 goto(this._current)，
       而 goto() 會寫 localStorage——等於在還原之前就把記錄蓋成 0，
       接著 _restoreFromStorage() 讀到的是自己剛寫的 0，重載永遠回第一頁。
       實測的存取順序是 set 0 在 get 之前。 */
    this._current = this._initialIndex();
    this._collectSlides();
    this._restoreFromStorage();

    window.addEventListener('keydown', this._keyHandler);
    window.addEventListener('resize', this._resizeHandler);
    this._fitToViewport();
    this._exposeGlobalApi();
  }

  disconnectedCallback() {
    window.removeEventListener('keydown', this._keyHandler);
    window.removeEventListener('resize', this._resizeHandler);
    if (this._slotEl) {
      this._slotEl.removeEventListener('slotchange', this._slotChangeHandler);
      this._slotEl = null;
    }
    if (this._numberBufferTimer) {
      clearTimeout(this._numberBufferTimer);
      this._numberBufferTimer = null;
    }
    this._numberBuffer = '';
    if (window.__deck === this) {
      delete window.__deck;
    }
  }

  // ── Public API ──────────────────────────────────────────────

  get slideCount() {
    return this._slides.length;
  }

  get current() {
    return this._current;
  }

  next() {
    this.goto(this._current + 1);
  }

  prev() {
    this.goto(this._current - 1);
  }

  goto(index) {
    if (this._slides.length === 0) return;
    const clamped = Math.max(0, Math.min(this._slides.length - 1, index));
    if (clamped === this._current && this._slides[clamped].classList.contains('active')) {
      return;
    }
    this._slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === clamped);
    });
    this._current = clamped;
    this._renderCounter();
    this._persistToStorage();
    this._notifyNotesWindow();
    this.dispatchEvent(new CustomEvent('slidechange', {
      detail: { index: clamped, total: this._slides.length },
      bubbles: true,
    }));
  }

  togglePrint() {
    document.body.classList.toggle('deck-stage-print-mode');
    window.print();
  }

  toggleBlackout() {
    const isBlackout = this.hasAttribute('blackout');
    if (isBlackout) {
      this.removeAttribute('blackout');
    } else {
      this.setAttribute('blackout', '');
    }
    this.dispatchEvent(new CustomEvent('blackout', {
      detail: { enabled: !isBlackout },
      bubbles: true,
    }));
  }

  openNotes() {
    if (this._notesWindow && !this._notesWindow.closed) {
      this._notesWindow.focus();
      return this._notesWindow;
    }
    this._notesWindow = window.open(
      '',
      'deck-stage-notes',
      'width=560,height=420,resizable=yes',
    );
    if (!this._notesWindow) {
      console.warn('[deck-stage] notes window blocked by browser pop-up policy');
      return null;
    }
    this._notesWindow.document.title = 'Speaker Notes';
    this._notesWindow.document.body.style.cssText =
      'font-family: system-ui; padding: 24px; line-height: 1.6; background: #1a1a1a; color: #f0f0f0;';
    this._notesWindow.document.body.innerHTML = '<div id="notes"></div>';
    this._notifyNotesWindow();
    return this._notesWindow;
  }

  // ── Internals ────────────────────────────────────────────────

  _applyCanvasSize() {
    const w = parseInt(this.getAttribute('width') || DEFAULT_WIDTH, 10);
    const h = parseInt(this.getAttribute('height') || DEFAULT_HEIGHT, 10);
    this.style.setProperty('--canvas-w', `${w}px`);
    this.style.setProperty('--canvas-h', `${h}px`);
  }

  _fitToViewport() {
    if (!this._stage) return;
    const w = parseInt(this.getAttribute('width') || DEFAULT_WIDTH, 10);
    const h = parseInt(this.getAttribute('height') || DEFAULT_HEIGHT, 10);
    const scaleX = window.innerWidth / w;
    const scaleY = window.innerHeight / h;
    const scale = Math.min(scaleX, scaleY);
    this.style.setProperty('--scale', String(scale));
  }

  _collectSlides() {
    this._slides = Array.from(this.querySelectorAll(':scope > .slide'));
    if (this._slides.length === 0) return;
    const activeIndex = this._slides.findIndex((s) => s.classList.contains('active'));
    if (activeIndex >= 0) {
      this._current = activeIndex;
    } else {
      this.goto(this._current);
    }
    this._renderCounter();
  }

  _renderCounter() {
    if (!this._counter) return;
    const total = this._slides.length;
    if (total === 0) {
      this._counter.textContent = '';
      return;
    }
    this._counter.textContent = `${this._current + 1} / ${total}`;
  }

  /**
   * 初始頁碼：帶 no-persist 就用 start-index，否則優先用 localStorage 的記錄。
   * 只回傳數字，不呼叫 goto、不寫 localStorage——寫入的副作用正是 TASK 的成因。
   */
  _initialIndex() {
    const startIndex = parseInt(this.getAttribute('start-index') || '0', 10);
    const fallback = Number.isFinite(startIndex) ? startIndex : 0;
    if (this.hasAttribute('no-persist')) return fallback;
    try {
      const raw = localStorage.getItem(this._storageKey());
      if (raw !== null) {
        const idx = parseInt(raw, 10);
        if (Number.isFinite(idx)) return idx;
      }
    } catch (e) {
    }
    return fallback;
  }

  _restoreFromStorage() {
    if (this.hasAttribute('no-persist')) {
      const startIndex = parseInt(this.getAttribute('start-index') || '0', 10);
      this.goto(Number.isFinite(startIndex) ? startIndex : 0);
      return;
    }
    try {
      const key = this._storageKey();
      const raw = localStorage.getItem(key);
      if (raw !== null) {
        const idx = parseInt(raw, 10);
        if (Number.isFinite(idx)) {
          this.goto(idx);
          return;
        }
      }
    } catch (e) {
      // localStorage unavailable (private mode / SSR); ignore
    }
    const startIndex = parseInt(this.getAttribute('start-index') || '0', 10);
    this.goto(Number.isFinite(startIndex) ? startIndex : 0);
  }

  _persistToStorage() {
    if (this.hasAttribute('no-persist')) return;
    try {
      localStorage.setItem(this._storageKey(), String(this._current));
    } catch (e) {
      // ignore
    }
  }

  _storageKey() {
    return this.getAttribute('storage-key') || DEFAULT_STORAGE_KEY;
  }

  _onKeydown(event) {
    if (event.defaultPrevented) return;
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }
    switch (event.key) {
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        event.preventDefault();
        this.next();
        break;
      case 'ArrowLeft':
      case 'PageUp':
        event.preventDefault();
        this.prev();
        break;
      case 'Home':
        event.preventDefault();
        this.goto(0);
        break;
      case 'End':
        event.preventDefault();
        this.goto(this._slides.length - 1);
        break;
      case 'b':
      case 'B':
        event.preventDefault();
        this.toggleBlackout();
        break;
      case 'p':
      case 'P':
        event.preventDefault();
        this.togglePrint();
        break;
      case 'n':
      case 'N':
        event.preventDefault();
        this.openNotes();
        break;
      case 'Enter':
        if (this._numberBuffer.length > 0) {
          event.preventDefault();
          const target = parseInt(this._numberBuffer, 10) - 1;
          this.goto(target);
          this._numberBuffer = '';
        }
        break;
      default:
        if (/^[0-9]$/.test(event.key)) {
          this._numberBuffer += event.key;
          if (this._numberBufferTimer) clearTimeout(this._numberBufferTimer);
          this._numberBufferTimer = setTimeout(() => {
            this._numberBuffer = '';
          }, 1500);
        }
    }
  }

  _notifyNotesWindow() {
    if (!this._notesWindow || this._notesWindow.closed) return;
    const slide = this._slides[this._current];
    const notes = slide ? (slide.dataset.notes || '') : '';
    try {
      const targetOrigin = this.getAttribute('notes-target') || window.location.origin;
      this._notesWindow.postMessage({
        type: 'deck-stage:notes',
        index: this._current,
        total: this._slides.length,
        notes,
      }, targetOrigin);
      // Direct DOM update fallback (same-origin window.open)
      const notesEl = this._notesWindow.document.getElementById('notes');
      if (notesEl) {
        notesEl.innerHTML =
          `<div style="opacity:0.6;font-size:13px;margin-bottom:8px;">Slide ${this._current + 1} / ${this._slides.length}</div>` +
          `<div style="font-size:18px;white-space:pre-wrap;">${this._escapeHtml(notes) || '<em>(no notes)</em>'}</div>`;
      }
    } catch (e) {
      // cross-origin or window closed
    }
  }

  _escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[c]);
  }

  _exposeGlobalApi() {
    // Fork verifier 友善：把當前 instance 暴露到 window.__deck
    Object.defineProperty(window, '__deck', {
      value: this,
      writable: true,
      configurable: true,
    });
  }
}

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, DeckStage);
}

export default DeckStage;

# Tweaks 即時變體切換系統

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。

## 概述

Tweaks 讓使用者在瀏覽器中即時切換設計變體（配色 / 字級 / layout / 密度），不需要改原始碼。切換結果透過 localStorage 持久化，重新整理不丟。

## 何時加 Tweaks

- 使用者明確要求「能調參」/「多版本切換」
- 設計有多個 variations 需要對比
- **預設行為**：fe-design Stage 5 實作時，主腦為每案加 2-3 個 tweaks（除非使用者拒絕）

## 各 mode 預設 tweaks

| Mode | 預設 Tweaks |
|---|---|
| deck | 配色主題（light/dark）+ 字級（compact/normal/large）+ 資訊密度（high/normal） |
| page | 配色（brand/neutral）+ layout（單欄/雙欄） |
| app | light/dark mode + 字級 |

## 使用方式

### 1. 定義 tweak 清單

```js
const tweakDefs = [
  {
    key: 'primaryColor',
    label: '主色',
    type: 'color',
    default: '#0ea5e9',
    section: 'Colors',
  },
  {
    key: 'fontSize',
    label: '字級',
    type: 'range',
    default: 16,
    min: 12,
    max: 24,
    step: 1,
    section: 'Typography',
  },
  {
    key: 'density',
    label: '密度',
    type: 'select',
    default: 'comfortable',
    options: [
      { value: 'compact', label: 'Compact' },
      { value: 'comfortable', label: 'Comfortable' },
      { value: 'spacious', label: 'Spacious' },
    ],
    section: 'Layout',
  },
  {
    key: 'darkMode',
    label: 'Dark Mode',
    type: 'boolean',
    default: false,
    section: 'Theme',
  },
];
```

### 2. 產生面板 HTML + script

```js
import { TweaksPanel } from '~/.claude/skills/starter-components/scaffolds/tweaks_panel.mjs';

const { html, script } = TweaksPanel({ tweakDefs });
// html → 注入 body 末尾
// script → 注入 <script> 標籤
```

### 3. 在 CSS 中引用 tweak 值

Tweaks 面板會自動設定 `--tweak-<key>` CSS 變數到 `:root`：

```css
:root {
  --color-primary: var(--tweak-primaryColor, #0ea5e9);
  --font-size-base: var(--tweak-fontSize, 16)px;
}

body[data-density="compact"] { --space-base: 4px; }
body[data-density="comfortable"] { --space-base: 8px; }
body[data-density="spacious"] { --space-base: 12px; }
```

## 支援的 input 類型

| type | 產出 | 值型別 |
|---|---|---|
| `color` | `<input type="color">` | HEX string |
| `range` | `<input type="range">` | number |
| `select` | `<select>` | string |
| `boolean` | `<input type="checkbox">` | boolean |
| `text` | `<input type="text">` | string |

## Shadow DOM 相容性

CSS custom properties 可穿透 Shadow DOM boundary 繼承。`deck_stage.js` 使用 Shadow DOM 時，Tweaks 透過 `document.documentElement.style.setProperty()` 設定的 CSS 變數會自動繼承到 Shadow DOM 內部。已確認相容。

## localStorage 行為

- Key：`design-tweaks`（可透過 `storageKey` prop 自訂）
- 格式：JSON 序列化的 key-value 物件
- Reset All：還原所有值到 `default`，清除 localStorage
- 跨分頁：同 origin 下的不同分頁共享 localStorage（瀏覽器原生行為）

## 列印

`@media print` 時自動隱藏面板和 toggle 按鈕。

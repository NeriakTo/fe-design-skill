---
name: Tech Dark
description: 深色科技感 SaaS 風格 — 電青強調、精緻層級、微光效果。適用於 SaaS 產品頁面、技術 Dashboard、AI/ML 平台介紹、開發者工具。
version: 1.0.0
theme: dark
colors:
  primary: "#00d4aa"
  on-primary: "#0f1117"
  primary-container: "#0d1f1a"
  on-primary-container: "#00d4aa"
  surface: "#0f1117"
  surface-dim: "#0a0c10"
  surface-bright: "#1a1d27"
  surface-container-lowest: "#0a0c10"
  surface-container-low: "#13161e"
  surface-container: "#1a1d27"
  surface-container-high: "#252a35"
  surface-container-highest: "#2f3542"
  on-surface: "#e2e8f0"
  on-surface-variant: "#94a3b8"
  outline: "#5a6373"
  outline-variant: "#2f3542"
  secondary: "#3b82f6"
  on-secondary: "#ffffff"
  secondary-container: "#111827"
  on-secondary-container: "#93c5fd"
  tertiary: "#ff6b35"
  on-tertiary: "#0f1117"
  error: "#ef4444"
  on-error: "#ffffff"
  error-container: "#1f1315"
  on-error-container: "#fca5a5"
  background: "#0f1117"
  on-background: "#e2e8f0"
typography:
  display-lg:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 48px
    fontWeight: "800"
    lineHeight: 56px
    letterSpacing: -0.03em
  headline-lg:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 28px
    fontWeight: "700"
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 22px
    fontWeight: "600"
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 28px
  body-md:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  label-sm:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 12px
    fontWeight: "500"
    lineHeight: 16px
    letterSpacing: 0.04em
spacing:
  unit: 8px
  container-padding: 32px
  card-gap: 24px
  section-margin: 64px
rounded:
  sm: 4px
  DEFAULT: 8px
  md: 12px
  lg: 16px
  xl: 24px
  full: 9999px
components:
  card-standard:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "24px"
    borderColor: "{colors.outline-variant}"
  card-highlight:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "24px"
    borderColor: "{colors.primary}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 24px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 24px"
    borderColor: "{colors.primary}"
  button-tertiary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 24px"
    minFontSize: "18.66px bold or 24px normal"
  input-field:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 14px"
    borderColor: "{colors.outline}"
  badge:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  navbar:
    backgroundColor: "{colors.surface-dim}"
    textColor: "{colors.on-surface}"
    rounded: "0"
    padding: "12px 32px"
    borderColor: "{colors.outline-variant}"
---

## 1. Visual Theme
<!-- tech-dark · refined · luminous -->

Tech Dark 以**深灰底面搭配電青強調色**為核心，追求 Linear / Vercel / Stripe 暗色系的精緻感：乾淨的層級結構、微妙的光暈效果、現代化的大圓角。全黑體（方案 B）確保中日韓文字在螢幕上的清晰度，字重對比建立視覺節奏。

**設計哲學**：luminous-minimalism（發光極簡）
**適用場景**：SaaS 產品首頁、技術 Dashboard、AI/ML 平台介紹、開發者工具文件、API 產品頁面
**情緒關鍵字**：精緻、科技感、專業、前衛、值得信賴

## 2. Color Palette

以電青（`--primary`）為品牌行動色，深灰（`--surface`）為全域背景。藍色（`--secondary`）作為輔助互動色，暖橘（`--tertiary`）用於警示和數據強調。

| Token | Hex | 用途 |
|-------|-----|------|
| --primary | #00d4aa | 品牌行動色：CTA 按鈕、超連結、重點強調 |
| --on-primary | #0f1117 | 主色背景上的文字（深色） |
| --primary-container | #0d1f1a | 徽章和標籤底色 |
| --surface | #0f1117 | 全域深色背景 |
| --surface-container | #1a1d27 | 卡片、區塊背景 |
| --surface-container-high | #252a35 | 高亮區塊、hover 狀態背景 |
| --on-surface | #e2e8f0 | 主要內文文字 |
| --on-surface-variant | #94a3b8 | 次要說明文字、placeholder |
| --secondary | #3b82f6 | 輔助互動色：次要按鈕、圖表、連結 |
| --tertiary | #ff6b35 | 警告和資料強調：重要通知、關鍵指標 |
| --outline | #5a6373 | 輸入框邊框、分隔線 |
| --outline-variant | #2f3542 | 卡片邊框、裝飾分隔 |
| --error | #ef4444 | 錯誤狀態、負成長指標 |

**WCAG AA 對比度**：
- `--on-surface`（#e2e8f0）對 `--surface`（#0f1117）= 15.3:1 ✓
- `--on-surface`（#e2e8f0）對 `--surface-container-high`（#252a35）= 11.7:1 ✓
- `--primary`（#00d4aa）對 `--surface`（#0f1117）= 9.9:1 ✓
- `--secondary`（#3b82f6）對 `--surface`（#0f1117）= 5.1:1 ✓
- `--tertiary`（#ff6b35）對 `--surface`（#0f1117）= 6.7:1 ✓
- `--error`（#ef4444）對 `--surface`（#0f1117）= 5.0:1 ✓
- `--on-primary`（#0f1117）對 `--primary`（#00d4aa）= 9.9:1 ✓
- `--outline`（#5a6373）對 `--surface`（#0f1117）= 3.1:1（符合 WCAG 1.4.11 非文字元素 3:1 標準）

所有文字組合均超過 AA 標準 4.5:1。`--on-secondary`（#ffffff）對 `--secondary`（#3b82f6）= 3.7:1，**限制用於 WCAG Large Text（≥24px normal 或 ≥18.66px bold）按鈕文字**，component 定義已綁定 minFontSize。

## 3. Typography

全黑體策略（字體配對方案 B）：標題用 800/700 字重營造力量感，內文 400 字重維持閱讀舒適度。深色背景上的文字不宜過細，label 層級使用 500 而非 600 以避免過度刺眼。

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|-------------|----------|------------|------------|---------------|
| display-lg | Inter, Noto Sans TC | 48px | 800 | 56px | -0.03em |
| headline-lg | Inter, Noto Sans TC | 28px | 700 | 36px | -0.02em |
| headline-md | Inter, Noto Sans TC | 22px | 600 | 28px | -0.01em |
| body-lg | Inter, Noto Sans TC | 18px | 400 | 28px | 0 |
| body-md | Inter, Noto Sans TC | 16px | 400 | 24px | 0 |
| label-sm | Inter, Noto Sans TC | 12px | 500 | 16px | 0.04em |

**CJK fallback chain**: `Inter, "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif`
**字體載入策略**: `font-display: swap`，Inter 透過 Google Fonts 或 `next/font` 載入，Noto Sans TC 同步載入以避免 CJK 文字閃爍。

## 4. Components

### 主按鈕（Button Primary）

電青填充背景，深色文字。圓角 8px，padding 10px 24px。hover 時加上微妙光暈（`--glow-accent`），背景色不變。disabled 狀態降低 opacity 至 0.4。

### 次要按鈕（Button Secondary / Ghost）

透明背景，1px `--primary` 邊框，文字 `--primary`。hover 時背景填充 `rgba(0, 212, 170, 0.08)`，邊框增亮至 `--primary`。適用於次要操作或取消動作。

### 輔助按鈕（Button Tertiary）

藍色填充背景 `--secondary`，白色文字。用於輔助行動、導航按鈕等非主要但仍需要醒目度的操作。

### 標準卡片（Card Standard）

圓角 12px，背景 `--surface-container`，1px `--outline-variant` 邊框。padding 24px。hover 時邊框變為 `--outline`，加上微弱光暈。適用於功能介紹、定價方案、團隊成員等。

### 高亮卡片（Card Highlight）

圓角 12px，背景 `--surface-container-high`，1px `--primary` 邊框。用於推薦方案、重要公告等需要突出的區塊。hover 時邊框加上 accent glow。

### 輸入欄位（Input Field）

背景 `--surface-container-low`，1px `--outline` 邊框，圓角 8px。placeholder 使用 `--on-surface-variant`。focus 狀態邊框變為 `--primary`，加上 accent glow ring。

### 徽章（Badge / Tag）

背景 `--primary-container`，文字 `--on-primary-container`，圓角 `--rounded-full`。padding 4px 12px，字級 label-sm。用於標籤、狀態指示、分類標記。

### 導覽列（Navbar）

背景 `--surface-dim`，底部 1px `--outline-variant` 邊框。高度固定 56px，內容左右 padding 32px。文字 `--on-surface`，active 項目使用 `--primary` 底線標記。支援 `backdrop-filter: blur(12px)` 半透明效果。

### 程式碼區塊（Code Block）

背景 `--surface-container-lowest`（最深色階），圓角 12px，padding 20px 24px。字體切換為 `"JetBrains Mono", "Fira Code", monospace`，字級 body-md，行高 28px。左側可選顯示行號，使用 `--on-surface-variant` 色。

### Dashboard 資料視覺化配色

六色 series palette 適用於圖表和資料呈現：
- `--chart-1`: #00d4aa（電青，主指標）
- `--chart-2`: #3b82f6（藍色，對比指標）
- `--chart-3`: #ff6b35（暖橘，警示指標）
- `--chart-4`: #a78bfa（紫色，分類輔助）
- `--chart-5`: #22d3ee（淺青，趨勢線）
- `--chart-6`: #94a3b8（中灰，基準線）

## 5. Layout

基礎單位 8px。web 頁面以 1280px 最大寬度置中，左右 padding 32px。大螢幕（>1440px）可擴展至 1440px。

| Token | 值 | 用途 |
|-------|------|------|
| --space-1 | 8px | 元素內間距最小值（icon 與文字間距） |
| --space-2 | 16px | 元件間距（按鈕之間） |
| --space-3 | 24px | 卡片內 padding |
| --space-4 | 32px | container padding |
| --space-5 | 64px | section 間距 |
| --space-6 | 96px | hero 和 footer 的垂直 padding |

**Grid**：CSS Grid 為主，12 欄系統。常見版型：
- 全寬單欄（hero、CTA）
- `1fr 1fr` 雙欄（功能介紹、圖文分割）
- `repeat(3, 1fr)` 三欄（定價卡片、功能列表）
- `repeat(4, 1fr)` 四欄（Dashboard KPI 摘要）

欄間距統一 24px（`--card-gap`），section 之間 64px（`--section-margin`）。

## 6. Depth & Motion

**光暈深度策略**：深色主題以微妙的光暈取代傳統陰影，營造「發光浮起」的科技感。

| 層級 | 表現方式 |
|------|----------|
| base | `--surface`（最深背景） |
| elevated | `--surface-container`（卡片底色）+ 1px `--outline-variant` 邊框 |
| emphasis | `--primary` 邊框 + accent glow |
| overlay | `backdrop-filter: blur(12px)` + `--surface-dim` 半透明 |

**Glow 效果**：
- `--glow-accent`: `0 0 24px rgba(0, 212, 170, 0.15)` — 主行動色微光，用於 hover 狀態和高亮卡片
- `--glow-accent-strong`: `0 0 32px rgba(0, 212, 170, 0.25)` — 強調光暈，用於 focus ring 和推薦方案
- `--glow-blue`: `0 0 20px rgba(59, 130, 246, 0.12)` — 藍色微光，用於輔助互動元素

**Subtle Gradient**：
- Hero 背景：`radial-gradient(ellipse at 50% 0%, rgba(0, 212, 170, 0.06) 0%, transparent 60%)`
- Section 分界：`linear-gradient(to bottom, transparent, rgba(0, 212, 170, 0.03), transparent)`

**Transition**：
- 互動元素（按鈕、連結）：`all 150ms ease-out`
- 卡片 hover：`all 200ms ease-out`
- 頁面轉場：`opacity 300ms ease-in-out`

**動畫規則**：
- `prefers-reduced-motion: reduce` 時移除所有 glow 和 transition
- 初次載入動畫：fade-up stagger 100ms/element，總時長不超過 600ms
- 數據動畫：counter-up 800ms ease-out，進度條由左至右 600ms ease-out

## 7. Do & Don't

### Do

- **Do** 使用 `--primary` 電青色僅限於行動呼籲元素（CTA 按鈕、重要連結、關鍵數據）。
- **Do** 卡片邊框使用 `--outline-variant`，hover 時升級為 `--outline` 或 `--primary`。
- **Do** 利用 `--glow-accent` 光暈強化互動回饋，但限制同時發光的元素數量（每個視區最多 2-3 個）。
- **Do** 所有文字保持在 `--on-surface` / `--on-surface-variant` 色階，不使用純白 #ffffff 作為內文色（過亮刺眼）。
- **Do** 深色漸層和光暈保持極淡（opacity ≤ 0.15），避免頁面整體過亮。

### Don't

- **Don't** 在深色背景上使用黑色文字或深灰文字（#333、#666 等淺色主題色值）。
- **Don't** 大面積使用飽和色塊（整區 `--primary` 背景 + 白字）——深色主題的強調透過邊框和光暈表達，不靠大色塊。
- **Don't** 同一區域疊加多種光暈效果（accent glow + blue glow 同時出現）。
- **Don't** 使用純黑 #000000 作為背景色，保持 `--surface`（#0f1117）的深灰調性。
- **Don't** 使用手寫體、襯線體、或任何非黑體字型——破壞科技感統一調性。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| desktop-lg | ≥ 1440px | 最大寬度 1440px 置中，左右 auto margin |
| desktop | 1024-1439px | 最大寬度 1280px，12 欄 grid |
| tablet | 768-1023px | 雙欄→單欄，card-gap 縮至 16px，section-margin 縮至 48px |
| mobile | < 768px | 全單欄，container-padding 縮至 20px，display-lg 降至 36px |

**Touch target**：行動裝置上按鈕和互動元素最小 44×44px。
**字級縮放**：mobile 時 display-lg 36px → headline-lg 24px → headline-md 20px → body-lg 16px → body-md 14px。
**光暈效果**：mobile 裝置上降低 glow opacity 至 50% 或完全移除，減少 GPU 負擔。
**導覽列**：mobile 時收合為 hamburger menu，展開時使用 `--surface-dim` 全屏覆蓋 + `backdrop-filter: blur(12px)`。

## 9. Agent Prompt Guide

### 必用
1. `var(--primary)` 僅用於 CTA 按鈕背景和重要強調元素（禁止 hardcode `#00d4aa`）
2. `var(--surface-container)` 作為卡片和區塊底色（禁止 hardcode `#1a1d27`）
3. `var(--on-surface)` 作為主要內文色（禁止 hardcode `#e2e8f0`）
4. font-family 必須使用 `Inter, "Noto Sans TC", sans-serif`（禁止 hardcode 其他字體）
5. 卡片圓角使用 `var(--rounded-md)`（12px），按鈕使用 `var(--rounded-DEFAULT)`（8px）

### 禁止
1. 禁止使用純黑 `#000000` 作為背景或邊框色
2. 禁止使用淺色主題的灰色色值（#f5f5f5、#e5e7eb、#d1d5db 等）
3. 禁止在非 code block 場景使用等寬字體（monospace）
4. 禁止大面積飽和色塊（整個 section 填滿 `--primary` 或 `--secondary`）
5. 禁止使用 Tailwind 預設的 indigo、purple、pink 色階——色調與電青品牌色衝突

### 優先順序
DESIGN.md token > Tailwind config 自定義值 > Tailwind 預設值 > agent 預設值

### 語氣
簡潔有力但平易近人。像資深工程師寫產品頁面：技術準確、邏輯清晰、不堆砌行銷詞彙。中文使用通俗用語，避免翻譯腔。英文術語首次以「中譯（原文）」格式標示。

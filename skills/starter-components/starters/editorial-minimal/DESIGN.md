---
name: Editorial Minimal
description: 白底明體年報學術風 — 大量留白、文字為王、嚴謹排版。適用於年度報告、研究白皮書、學術課件、公開刊物。
version: "1.0.0"
theme: light
colors:
  primary: "#1a1a2e"
  on-primary: "#ffffff"
  primary-container: "#e8e6ef"
  on-primary-container: "#1a1a2e"
  surface: "#ffffff"
  surface-dim: "#f8f5f0"
  surface-bright: "#ffffff"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#faf8f5"
  surface-container: "#f1ece4"
  surface-container-high: "#e8e2d8"
  surface-container-highest: "#ddd6ca"
  on-surface: "#1a1a2e"
  on-surface-variant: "#495057"
  outline: "#6b7280"
  outline-variant: "#d1cdc6"
  secondary: "#8b2252"
  on-secondary: "#ffffff"
  secondary-container: "#f5e0ea"
  on-secondary-container: "#5c1637"
  tertiary: "#b8860b"
  on-tertiary: "#ffffff"
  tertiary-container: "#faf0d4"
  on-tertiary-container: "#7a5a07"
  error: "#b91c1c"
  on-error: "#ffffff"
  error-container: "#fde8e8"
  on-error-container: "#7f1d1d"
  background: "#ffffff"
  on-background: "#1a1a2e"
typography:
  display-lg:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 48px
    fontWeight: "700"
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 28px
    fontWeight: "700"
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 22px
    fontWeight: "700"
    lineHeight: 30px
    letterSpacing: 0
  body-lg:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 32px
    letterSpacing: 0.01em
  body-md:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 28px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: "Source Serif Pro, Noto Serif TC, serif"
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.04em
spacing:
  unit: 8px
  container-padding: 40px
  card-gap: 24px
  section-margin: 72px
rounded:
  sm: 0px
  DEFAULT: 2px
  md: 3px
  lg: 4px
  xl: 4px
  full: 9999px
components:
  card-article:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.card-gap}"
    borderColor: "{colors.outline-variant}"
  card-highlight:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.card-gap}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 28px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 28px"
    borderColor: "{colors.primary}"
  pull-quote:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    rounded: "0"
    padding: "0 0 0 24px"
    borderColor: "{colors.secondary}"
  section-divider:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "0"
    padding: "0"
    borderColor: "{colors.primary}"
  footnote-bar:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface-variant}"
    rounded: "0"
    padding: "16px 40px"
    borderColor: "{colors.outline-variant}"
  table-header:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "0"
    padding: "10px 16px"
---

## 1. Visual Theme
<!-- editorial · serif · academic -->

Editorial Minimal 以**白底明體**為核心，追求 The Economist、Harvard Business Review、Foreign Affairs 等國際刊物的排版精神：文字為王、留白即呼吸、嚴謹即信任。全明體（方案 C）在中英文混排場景下展現學術氣質與閱讀沉浸感。

**設計哲學**：typographic-minimalism（字體極簡主義）
**適用場景**：年度報告、研究白皮書、學術課件、政策建議書、公開刊物、深度分析文章
**情緒關鍵字**：沉靜、嚴謹、信任、雋永、知性

## 2. Color Palette

以近黑（`--primary`）為墨色基底，搭配深紅（`--secondary`）作為語意強調，金色（`--tertiary`）僅作裝飾點綴。全域純白底，低彩度策略讓文字層級自然浮現。

| Token | Hex | 用途 |
|-------|-----|------|
| --primary | #1a1a2e | 標題、表頭背景、主文字色 |
| --on-primary | #ffffff | 深色背景上的反白文字 |
| --surface | #ffffff | 全域白底 |
| --surface-dim | #f8f5f0 | 暖調淺底（引用區塊、側邊欄） |
| --surface-container | #f1ece4 | 卡片、附注區塊背景 |
| --on-surface | #1a1a2e | 主要內文文字 |
| --on-surface-variant | #495057 | 次要說明、圖說、附注 |
| --secondary | #8b2252 | 強調色：拉引句、首字放大、關鍵標記 |
| --tertiary | #b8860b | 裝飾專用：分隔線飾條、章節標記、小圖標 |
| --outline | #6b7280 | 表格邊框、分隔線 |
| --outline-variant | #d1cdc6 | 輕量分隔、卡片邊框 |
| --error | #b91c1c | 警示、負面數據 |

**WCAG AA 對比度**：
- `--on-surface`（#1a1a2e）對 `--surface`（#ffffff）= 17.1:1 ✓
- `--on-primary`（#ffffff）對 `--primary`（#1a1a2e）= 17.1:1 ✓
- `--secondary`（#8b2252）對 `--surface`（#ffffff）= 8.6:1 ✓
- `--on-surface-variant`（#495057）對 `--surface`（#ffffff）= 8.2:1 ✓
- `--outline`（#6b7280）對 `--surface`（#ffffff）= 4.8:1 ✓（AA 正文通過）
- `--tertiary`（#b8860b）對 `--surface`（#ffffff）= 3.3:1 — **僅通過 AA 大字標準（≥3:1）**，禁止用於正文或小字，限裝飾用途

## 3. Typography

全明體策略（字體配對方案 C）：標題用 700 字重建立層級權威感，內文 400 字重確保長文閱讀舒適。行高比黑體方案更寬鬆，適應明體的視覺特性。

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|-------------|----------|------------|------------|---------------|
| display-lg | Source Serif Pro, Noto Serif TC | 48px | 700 | 56px | -0.02em |
| headline-lg | Source Serif Pro, Noto Serif TC | 28px | 700 | 36px | -0.01em |
| headline-md | Source Serif Pro, Noto Serif TC | 22px | 700 | 30px | 0 |
| body-lg | Source Serif Pro, Noto Serif TC | 18px | 400 | 32px | 0.01em |
| body-md | Source Serif Pro, Noto Serif TC | 16px | 400 | 28px | 0.01em |
| label-sm | Source Serif Pro, Noto Serif TC | 12px | 600 | 16px | 0.04em |

**CJK fallback chain**: `"Source Serif Pro", "Noto Serif TC", "Songti TC", "PMingLiU", "新細明體", serif`
**PPTX 映射**: `Noto Serif TC` → `新細明體`（CJK）；`Source Serif Pro` → `Georgia`（Latin fallback）

**明體排版注意**：
- body-lg 行高 32px（1.78 倍）比黑體多 4px，因明體橫豎筆畫粗細差大，需更多垂直呼吸空間
- 正文字距微正（+0.01em）補償明體天然的視覺緊密感
- display-lg 可使用負字距（-0.02em），讓大標題更緊湊有力

## 4. Components

### 拉引句（Pull Quote）

左側 3px 實線邊框 `--secondary`，無背景色。引文使用 headline-md 字級、`--secondary` 文字色、400 字重斜體。出處使用 label-sm、`--on-surface-variant`。用於文章中段插入關鍵摘句。

### 章節分隔線（Section Divider）

水平線 1px solid `--primary`，上下 margin 各 `--section-margin`（72px）。可選加金色（`--tertiary`）裝飾符號居中（如 ◆ 或 ※），字級 label-sm。分隔線是整份文件視覺節奏的核心元素。

### 文章卡片（Article Card）

背景 `--surface`，1px 邊框 `--outline-variant`，圓角 2px。內含：headline-md 標題 + body-md 摘要（限兩行 clamp）+ label-sm 日期與作者。hover 時邊框色加深至 `--outline`。

### 附注列（Footnote Bar）

底部固定區塊，背景 `--surface-container-low`，上邊框 1px `--outline-variant`。字級 label-sm，文字色 `--on-surface-variant`。用於頁面底部的註釋、參考文獻、版權聲明。

### 資料表格（Data Table）

表頭背景 `--primary`，文字 `--on-primary`，字級 label-sm 字重 600。表身無斑馬紋，行間以 1px `--outline-variant` 水平線分隔（學術表格慣例）。對齊規則：文字左對齊、數字右對齊。

### 按鈕

Primary：背景 `--primary`，文字 `--on-primary`，圓角 2px，padding 10px 28px。
Secondary（Ghost）：透明背景，1px `--primary` 邊框，文字 `--primary`，hover 時背景 `--surface-container`。
兩種按鈕字級均為 body-md、字重 600。

## 5. Layout

基礎單位 8px。學術排版以閱讀舒適為最高優先，正文行寬控制在 65-72 字元（中文約 32-36 字），避免視線折返疲勞。

| Token | 值 | 用途 |
|-------|------|------|
| --space-1 | 8px | 元素內間距最小值 |
| --space-2 | 16px | 行間附注、圖說與圖片間距 |
| --space-3 | 24px | 元件間距、卡片內 padding |
| --space-4 | 40px | container 左右 padding |
| --space-5 | 72px | section 間距（大量留白核心） |
| --space-6 | 120px | 頁面頂底 margin |

**正文行寬**：`max-width: 68ch`（約 640px），置中對齊，兩側大量留白。這是與顧問簡報最大的差異——簡報填滿畫面，社論留白呼吸。

**Grid**：主內容單欄為主，輔以 sidebar 或 margin note 構成非對稱版型（如 70-30 主文-旁注）。雙欄圖文分割時使用 60-40 或 50-50。

**垂直節奏**：所有 margin/padding 為 8px 倍數，section-margin 72px 確保章節間有明確的視覺斷點。

## 6. Depth & Motion

**零深度策略**：學術刊物不使用 box-shadow、drop-shadow 或 elevation。所有層級差異透過留白量和邊線表達。

| 層級 | 表現方式 |
|------|----------|
| base | `--surface`（純白底） |
| inset | `--surface-container`（暖灰底，附注/引用區塊） |
| emphasis | `--primary`（深色底反白，表頭/頁首） |
| border | 1px `--outline-variant`（卡片/表格的輕量邊界） |

**Transition**：`all 0.15s ease-in-out`（hover 狀態切換，極輕微）。
**頁面轉場**：淡入 0.3s opacity，無位移動畫（維持靜態印刷感）。
**捲動行為**：`scroll-behavior: smooth`，無 parallax、無 sticky 以外的捲動效果。
**首字放大（Drop Cap）**：開篇段落首字使用 display-lg 字級 + `--secondary` 色，float left，佔 3 行高度，0.5s 淡入。

## 7. Do & Don't

- **Do** 正文行寬控制在 65-72 字元（中文 32-36 字），兩側保留充足留白。
- **Do** 使用 1px 水平線（`--primary`）分隔章節，建立清晰的閱讀節奏。
- **Do** 開篇段落使用首字放大（Drop Cap），以 `--secondary` 深紅色強化學術開場感。
- **Do** 圖說、附注、頁碼使用 label-sm 字級 + `--on-surface-variant` 色，與正文拉開層級。
- **Do** 標題一律靠左對齊（封面頁除外），遵循學術排版慣例。
- **Don't** 金色（`--tertiary`）用於正文或小字——對比度僅 3.3:1，限大標題或裝飾元素。
- **Don't** 使用 box-shadow、漸層或任何擬物效果。
- **Don't** 混用黑體與明體——全文統一 serif 字族，不在標題或按鈕切換 sans-serif。
- **Don't** 使用 justify（兩端對齊）排列中文正文——CJK 文字缺乏連字號機制，會產生不均勻字距。
- **Don't** 圓角超過 4px——銳利邊角是學術嚴肅感的視覺基礎。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| desktop | ≥ 1280px | 正文 68ch 置中，旁注欄 margin note 顯示 |
| tablet | 768-1279px | 正文 68ch 置中，margin note 收回正文流內 |
| mobile | < 768px | 全寬單欄，padding 縮減至 16px，字級不縮放 |
| print (A4) | 210×297mm | page-break-inside:avoid，字級不縮放，隱藏互動元素 |

**Touch target**：mobile 模式按鈕最小 44×44px。
**正文閱讀體驗**：所有斷點下 body-md 維持 16px，body-lg 維持 18px，不做字級縮放——學術內容的可讀性不可妥協。
**列印優化**：A4 輸出時 `--surface-container` 區塊改為白底 + 邊框，節省墨水。

## 9. Agent Prompt Guide

### 必用
1. `var(--on-surface)` 作為主要文字色（禁止 hardcode `#1a1a2e`）
2. `var(--secondary)` 作為語意強調色：拉引句、首字放大、重點標記
3. 全域字體必須使用 `"Source Serif Pro", "Noto Serif TC", serif`（禁止混入 sans-serif）
4. 正文區塊必須設定 `max-width: 68ch` 並置中，確保閱讀舒適
5. 章節之間使用 `--section-margin`（72px）間距，體現大量留白原則

### 禁止
1. 禁止使用 box-shadow、drop-shadow 或任何 elevation 效果
2. 禁止在正文或 label-sm 使用 `var(--tertiary)`（金色對比度僅 3.3:1，限裝飾用途）
3. 禁止使用漸層背景、玻璃擬態、模糊效果
4. 禁止混入 sans-serif 字體（Inter、Noto Sans TC 等均不得出現）
5. 禁止圓角超過 4px（`--rounded-lg` = 4px 已是上限，`--rounded-full` 僅限特殊場景如 pagination dot）

### 優先順序
DESIGN.md token > editorial-minimal.css preset > agent 預設值

### 語氣
沉穩內斂。像 The Economist 的資深編輯撰稿：觀點鮮明但語調克制，數據充分但不堆砌，每一句都有存在的必要。中文使用通順的書面語，避免口語化也避免學究氣。

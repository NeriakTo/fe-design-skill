---
name: Corporate Warm
description: 暖色中性底地產商務風 — 深棕主色、暖金強調、sage green 輔助。覆蓋物業管理提案、社區活動頁面、高端住宅品牌溝通。
version: 1.0.0
theme: light
colors:
  primary: "#3d2b1f"
  on-primary: "#ffffff"
  primary-container: "#e8ddd4"
  on-primary-container: "#3d2b1f"
  surface: "#f9f6f1"
  surface-dim: "#f0e9df"
  surface-bright: "#ffffff"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#f5f0e8"
  surface-container: "#f0e9df"
  surface-container-high: "#e8ddd4"
  surface-container-highest: "#ddd0c3"
  on-surface: "#3d2b1f"
  on-surface-variant: "#6b5c50"
  outline: "#b8a99a"
  outline-variant: "#ddd0c3"
  secondary: "#c4932a"
  on-secondary: "#3d2b1f"
  secondary-container: "#faf3e6"
  on-secondary-container: "#5c4510"
  tertiary: "#5a7a5a"
  tertiary-text: "#4a6a4a"
  on-tertiary: "#ffffff"
  tertiary-container: "#e4ede4"
  on-tertiary-container: "#2d3e2d"
  error: "#c0392b"
  on-error: "#ffffff"
  error-container: "#f8d7d2"
  on-error-container: "#7a2118"
  background: "#f9f6f1"
  on-background: "#3d2b1f"
typography:
  display-lg:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 48px
    fontWeight: "900"
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
    fontWeight: "700"
    lineHeight: 30px
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
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.04em
spacing:
  unit: 8px
  container-padding: 32px
  card-gap: 16px
  section-margin: 48px
rounded:
  sm: 4px
  DEFAULT: 8px
  md: 10px
  lg: 12px
  xl: 16px
  full: 9999px
components:
  card-standard:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.card-gap}"
  card-highlight:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.card-gap}"
  card-notice:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.md}"
    padding: "20px 24px"
    borderLeft: "4px solid {colors.secondary}"
  card-event:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "20px 24px"
    borderColor: "{colors.outline-variant}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "12px 28px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.DEFAULT}"
    padding: "12px 28px"
    borderColor: "{colors.primary}"
  button-accent:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.on-secondary}"
    rounded: "{rounded.DEFAULT}"
    padding: "12px 28px"
  input-field:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "10px 14px"
    borderColor: "{colors.outline}"
  signature-banner:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.md}"
    padding: "16px 24px"
---

## 1. Visual Theme
<!-- warm-trust · hospitable · professional -->

Corporate Warm 以**暖米色底**搭配**深棕主色**，傳達高端住宅社區的溫暖可信形象。不追求科技感的冷銳，而是像一座管理良好的社區大廳——木質調、柔和光線、體貼入微。

**設計哲學**：warm-trust（溫暖信賴）
**適用場景**：物業管理提案簡報、社區活動網頁、住戶公告系統、高端住宅品牌形象
**情緒關鍵字**：溫暖、可信、親切、沉穩、體貼

## 2. Color Palette

以深棕（`--primary`）為主色調，搭配暖金（`--secondary`）傳達品質與價值，sage green（`--tertiary`）帶入社區綠意。整體色彩取自天然材質——深木、暖金、草葉——而非人工螢光。

| Token | Hex | 用途 |
|-------|-----|------|
| --primary | #3d2b1f | 標題文字、主按鈕、頁首區塊 |
| --on-primary | #ffffff | 深色背景上的文字 |
| --surface | #f9f6f1 | 全域暖米底色 |
| --surface-container-low | #f5f0e8 | 卡片背景、區塊底色 |
| --surface-container | #f0e9df | 次級區塊背景、sidebar |
| --surface-container-lowest | #ffffff | 輸入框、彈窗底色 |
| --on-surface | #3d2b1f | 主要內文文字 |
| --on-surface-variant | #6b5c50 | 次要說明文字、時間戳 |
| --secondary | #c4932a | 強調色：暖金，用於公告重點、CTA、徽章 |
| --on-secondary | #3d2b1f | 金色背景上的文字（深棕，非白色） |
| --tertiary | #5a7a5a | 輔助色：sage green，非文字用途（圖標、邊框、大標題） |
| --tertiary-text | #4a6a4a | sage green 文字專用（body 字級以上） |
| --outline | #b8a99a | 分隔線、邊框 |
| --error | #c0392b | 錯誤提示、逾期警示 |

**WCAG AA 對比度**：

| 文字色 | 背景色 | 對比度 | 判定 |
|--------|--------|--------|------|
| --on-surface（#3d2b1f） | --surface（#f9f6f1） | 12.5:1 | AA 通過 |
| --on-primary（#ffffff） | --primary（#3d2b1f） | 13.4:1 | AA 通過 |
| --on-secondary（#3d2b1f） | --secondary（#c4932a） | 4.8:1 | AA 通過 |
| --on-surface-variant（#6b5c50） | --surface（#f9f6f1） | 6.0:1 | AA 通過 |
| --tertiary-text（#4a6a4a） | --surface（#f9f6f1） | 5.6:1 | AA 通過 |
| --on-surface（#3d2b1f） | --surface-container（#f0e9df） | 11.1:1 | AA 通過 |
| --error（#c0392b） | --surface（#f9f6f1） | 5.0:1 | AA 通過 |

**設計決策**：`--on-secondary` 選用深棕而非白色。白色在暖金底上對比度僅 2.8:1（不達標），深棕則達 4.8:1 且形成同色系的色調和諧，更符合品牌的溫暖調性。`--tertiary`（#5a7a5a）僅用於圖標、邊框、≥18pt 大標題等非正文場景；正文字級的 sage green 必須使用 `--tertiary-text`（#4a6a4a，5.6:1）。

## 3. Typography

全黑體策略（字體配對方案 B）：標題用 900/700 字重拉出層級，內文 400 保持閱讀舒適。行高較 consulting 版略寬鬆，提升暖感與閱讀體驗。

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|-------------|----------|------------|------------|---------------|
| display-lg | Inter, Noto Sans TC | 48px | 900 | 56px | -0.03em |
| headline-lg | Inter, Noto Sans TC | 28px | 700 | 36px | -0.02em |
| headline-md | Inter, Noto Sans TC | 22px | 700 | 30px | -0.01em |
| body-lg | Inter, Noto Sans TC | 18px | 400 | 28px | 0 |
| body-md | Inter, Noto Sans TC | 16px | 400 | 24px | 0 |
| label-sm | Inter, Noto Sans TC | 12px | 600 | 16px | 0.04em |

**CJK fallback chain**: `Inter, "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif`
**PPTX 映射**: `Noto Sans TC` → `微軟正黑體`（CJK）；`Inter` → `Calibri`（Latin fallback）

## 4. Components

### 公告卡（Notice Card）

社區公告、管理處通知的標準容器。左側 4px `--secondary` 金色邊條提示重要性，背景 `--secondary-container` 暖金淡底。標題 headline-md、內文 body-md、時間戳 label-sm `--on-surface-variant`。圓角 10px。

### 活動卡（Event Card）

社區活動、住戶服務的展示元件。白底（`--surface-container-lowest`），1px `--outline-variant` 邊框，圓角 12px。內含：活動圖片（頂部滿寬，圓角頂部 12px）、標題 headline-md、日期/地點 body-md `--on-surface-variant`、報名按鈕 button-primary。

### 簽呈條（Signature Banner）

物業提案中的關鍵資訊帶，用於強調核心數據或結論。背景 `--primary-container`，文字 `--on-primary-container`，圓角 10px，padding 16px 24px。適合放置：預算摘要、管理費調整幅度、年度維修計畫重點。

### 按鈕

- **Primary**：背景 `--primary`（深棕），文字 `--on-primary`（白），圓角 8px，padding 12px 28px。
- **Secondary（Ghost）**：透明背景，1px `--primary` 邊框，文字 `--primary`，圓角 8px。
- **Accent**：背景 `--secondary`（暖金），文字 `--on-secondary`（深棕），圓角 8px。用於關鍵行動呼籲。

### 輸入框

白底（`--surface-container-lowest`），1px `--outline` 邊框，圓角 8px，padding 10px 14px。Focus 狀態邊框色切換為 `--primary`，邊框寬度 2px。Placeholder 色 `--on-surface-variant`。

### 圖表配色

六色 series palette 取自暖色大地色系：
- `--chart-1`: #3d2b1f（深棕）
- `--chart-2`: #c4932a（暖金）
- `--chart-3`: #5a7a5a（sage green）
- `--chart-4`: #a0522d（赤陶 terracotta）
- `--chart-5`: #8b7d6b（灰褐 taupe）
- `--chart-6`: #b07d8e（乾燥玫瑰 dusty rose）

## 5. Layout

基礎單位 8px。以 web 頁面為主要 viewport，兼顧提案簡報 A4/16:9 輸出。

| Token | 值 | 用途 |
|-------|------|------|
| --space-1 | 8px | 元素內間距最小值 |
| --space-2 | 16px | 元件間距、卡片 gap |
| --space-3 | 24px | 區塊內間距 |
| --space-4 | 32px | container padding |
| --space-5 | 48px | section 間距 |
| --space-6 | 64px | 頁面 hero 區域垂直 padding |

**Grid**：web 模式採 CSS Grid + `max-width: 1200px` 置中。常見版型：全寬單欄 / 50-50 雙欄 / 33-33-33 三欄 / 60-40 圖文分割。卡片網格用 `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))` 自適應。

**提案簡報模式**：1920×1080 viewport 時，左右 padding 80px，上下 padding 60px，以 flexbox 排版。

## 6. Depth & Motion

**無陰影深度策略**：所有層級差異透過暖色底的明度變化表達，不使用 box-shadow。

| 層級 | 表現方式 | 色值 |
|------|----------|------|
| base | 全域底色 | `--surface`（#f9f6f1 暖米） |
| elevated | 卡片、區塊 | `--surface-container-low`（#f5f0e8 暖象牙） |
| recessed | 輸入框、彈窗 | `--surface-container-lowest`（#ffffff 純白） |
| emphasis | 深色反白區塊 | `--primary`（#3d2b1f 深棕） |

**Transition**：`all 0.25s ease-in-out`（hover / focus 狀態切換）。比 consulting 版略慢 50ms，傳達從容不急的氛圍。
**頁面轉場**：淡入 0.3s，不使用滑動或翻轉。
**微互動**：按鈕 hover 背景加亮 8%（`brightness(1.08)`）；卡片 hover `translateY(-2px)` 配合底色微變至 `--surface-container`。

## 7. Do & Don't

### Do
- 使用 `--surface` 暖米底色作為全域背景，保持溫暖基調。
- 公告和重要資訊用 `--secondary` 金色左邊條或徽章標示。
- 大量留白，單一區塊只傳達一個核心訊息。
- 圖片使用暖色濾鏡或挑選暖調攝影（自然光、木質、綠植）。
- 所有互動元素提供明確的 focus 狀態（2px `--primary` 邊框）。

### Don't
- 禁止使用冷色系作為主色（藍、紫、靛）。
- 禁止使用 box-shadow 或 drop-shadow（深度用底色差異表達）。
- 禁止圓角超過 16px（`--rounded-xl` = 16px 為最大值，full 僅限 avatar/badge）。
- 禁止白色文字搭配 `--secondary` 暖金底（對比度不達標 2.8:1，改用深棕 `--on-secondary`）。
- 禁止使用 `--tertiary`（#5a7a5a）作為 body 字級文字色（改用 `--tertiary-text` #4a6a4a）。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| desktop | ≥ 1280px | 標準版型，max-width 1200px 置中，三欄卡片網格 |
| tablet | 768-1279px | 雙欄卡片網格，container padding 縮至 24px |
| mobile | < 768px | 全單欄，container padding 縮至 16px，headline-lg 降至 24px |
| print (A4) | 210×297mm | PDF 輸出，字級不縮放，page-break-inside:avoid |
| deck (16:9) | 1920×1080 | 提案簡報模式，padding 80px/60px |

**Touch target**：mobile 和 tablet 模式下，所有互動元素最小 44×44px。
**字級調整**：mobile 下 display-lg 降至 36px（fontWeight 維持 900），headline-lg 降至 24px。body-md 維持 16px 不縮放。

## 9. Agent Prompt Guide

### 必用
1. `var(--surface)` 暖米底色作為全域 `background-color`（禁止 hardcode `#f9f6f1`）
2. `var(--primary)` 深棕作為標題和主按鈕色（禁止 hardcode `#3d2b1f`）
3. `var(--secondary)` 暖金作為強調、CTA、公告徽章（搭配深棕文字 `var(--on-secondary)`）
4. `var(--on-surface)` 作為主要內文色（禁止使用 Tailwind 預設灰色系）
5. font-family 必須使用 `Inter, "Noto Sans TC", sans-serif`（禁止 hardcode 其他字體）

### 禁止
1. 禁止使用 Tailwind 預設 gray/slate/zinc 色系取代暖色 surface tokens
2. 禁止白色文字放在 `--secondary` 暖金底上（WCAG 不達標，改用 `--on-secondary` 深棕）
3. 禁止 `--tertiary`（#5a7a5a）用於 < 18pt 正文文字（改用 `--tertiary-text` #4a6a4a）
4. 禁止 box-shadow 或 drop-shadow（深度一律用暖色底差異表達）
5. 禁止冷色系（藍、紫、靛）作為功能性 UI 色彩

### 優先順序
DESIGN.md token > corporate-warm.css preset > agent 預設值

### 語氣
溫暖但專業。像高端社區管理公司的品牌經理對住戶說話：親切、可信、體貼，但不失專業。中文使用通俗生活化用語，避免官腔和學術措辭。

---
name: Consulting Professional
description: 白底全黑體 McKinsey/BCG 簡報風格 — 高對比、強層級、資訊密度優先。適用於企業顧問提案、教育訓練課程、工業科技簡報。
version: 1.0.0
theme: light
colors:
  primary: "#1a2332"
  on-primary: "#ffffff"
  primary-container: "#e8edf5"
  on-primary-container: "#1a2332"
  surface: "#ffffff"
  surface-dim: "#f5f5f5"
  surface-bright: "#ffffff"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#f8f9fa"
  surface-container: "#f1f3f5"
  surface-container-high: "#e9ecef"
  surface-container-highest: "#dee2e6"
  on-surface: "#212529"
  on-surface-variant: "#495057"
  outline: "#adb5bd"
  outline-variant: "#dee2e6"
  secondary: "#e67e22"
  on-secondary: "#ffffff"
  secondary-container: "#fef3e2"
  on-secondary-container: "#8b4513"
  tertiary: "#2c7be5"
  on-tertiary: "#ffffff"
  error: "#dc3545"
  on-error: "#ffffff"
  error-container: "#f8d7da"
  on-error-container: "#842029"
  background: "#ffffff"
  on-background: "#212529"
typography:
  display-lg:
    fontFamily: "Inter, Noto Sans TC, sans-serif"
    fontSize: 48px
    fontWeight: "900"
    lineHeight: 52px
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
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.04em
spacing:
  unit: 8px
  container-padding: 32px
  card-gap: 16px
  section-margin: 48px
rounded:
  sm: 2px
  DEFAULT: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px
components:
  card-standard:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-gap}"
  card-highlight:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-gap}"
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
  kpi-card:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "20px 24px"
  action-title-bar:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "0"
    padding: "12px 32px"
  table-header:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "0"
    padding: "8px 12px"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
    padding: "8px 12px"
    borderColor: "{colors.outline}"
---

## 1. Visual Theme
<!-- consulting · structured · authoritative -->

Consulting Professional 以**白底深色文字**為基底，遵循 McKinsey / BCG / Bain 三大管顧的簡報視覺傳統：極簡裝飾、極強層級、資訊密度最大化。全黑體（方案 B）確保中日韓文字在投影環境下的清晰度。

**設計哲學**：structured-minimalism（結構化極簡）
**適用場景**：企業顧問提案簡報、教育訓練全天課程、工業科技產品介紹、內部策略報告
**情緒關鍵字**：專業、權威、理性、清晰、可信賴

## 2. Color Palette

以深海軍藍（`--primary`）為主色調，搭配暖橘（`--secondary`）作為行動呼籲和關鍵數據強調。白底確保列印和投影的最佳可讀性。

| Token | Hex | 用途 |
|-------|-----|------|
| --primary | #1a2332 | 標題背景、action title bar、表頭 |
| --on-primary | #ffffff | 深色背景上的文字 |
| --surface | #ffffff | 全域白底 |
| --surface-container | #f1f3f5 | 卡片、數據區塊背景 |
| --on-surface | #212529 | 主要內文文字 |
| --on-surface-variant | #495057 | 次要說明文字 |
| --secondary | #e67e22 | 強調色：KPI 增長箭頭、關鍵數字、CTA 按鈕 |
| --tertiary | #2c7be5 | 圖表輔助色、超連結 |
| --outline | #adb5bd | 分隔線、表格邊框 |
| --error | #dc3545 | 負成長、警示 |

**WCAG AA 對比度**：`--on-surface`（#212529）對 `--surface`（#ffffff）= 15.4:1；`--on-primary`（#ffffff）對 `--primary`（#1a2332）= 14.7:1。所有文字組合均超過 AA 標準 4.5:1。

## 3. Typography

全黑體策略（字體配對方案 B）：標題用 900/700 字重拉出層級，內文 400 字重保持閱讀舒適度。

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|-------------|----------|------------|------------|---------------|
| display-lg | Inter, Noto Sans TC | 48px | 900 | 52px | -0.03em |
| headline-lg | Inter, Noto Sans TC | 28px | 700 | 36px | -0.02em |
| headline-md | Inter, Noto Sans TC | 22px | 700 | 28px | -0.01em |
| body-lg | Inter, Noto Sans TC | 18px | 400 | 28px | 0 |
| body-md | Inter, Noto Sans TC | 16px | 400 | 24px | 0 |
| label-sm | Inter, Noto Sans TC | 12px | 600 | 16px | 0.04em |

**CJK fallback chain**: `Inter, "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif`
**PPTX 映射**: `Noto Sans TC` → `微軟正黑體`（CJK）；`Inter` → `Calibri`（Latin fallback）

## 4. Components

### 行動標題列（Action Title Bar）

投影片頂端深色帶，pyramid principle 必用。背景 `--primary`，文字 `--on-primary`，高度固定 52px，文字左對齊，字級 headline-md。

### 資料卡片（KPI Card）

圓角 6px，背景 `--surface-container`，內含：大字 KPI 值（display-lg 字級）+ 增減箭頭（`--secondary` 正成長 / `--error` 負成長）+ 說明標籤（label-sm）。

### 表格（Data Table）

表頭背景 `--primary`，文字 `--on-primary`，字級 label-sm，字重 600。表身斑馬紋交替 `--surface` / `--surface-container-low`。無外邊框，內邊框 1px `--outline-variant`。

### 按鈕

Primary：背景 `--primary`，文字 `--on-primary`，圓角 4px，padding 10px 24px。
Secondary（Ghost）：透明背景，1px `--primary` 邊框，文字 `--primary`。

### 圖表配色

六色 series palette 對齊 `mckinsey-consulting.css`：
- `--chart-1`: #1a2332（主色）
- `--chart-2`: #e67e22（暖橘）
- `--chart-3`: #2c7be5（科技藍）
- `--chart-4`: #6c757d（中灰）
- `--chart-5`: #28a745（正成長綠）
- `--chart-6`: #868e96（淺灰）

## 5. Layout

基礎單位 8px。投影片 1920×1080 viewport，左右 padding 80px，上下 padding 60px（扣除 action title bar 52px）。

| Token | 值 | 用途 |
|-------|------|------|
| --space-1 | 8px | 元素內間距最小值 |
| --space-2 | 16px | 元件間距 |
| --space-3 | 24px | 區塊間距 |
| --space-4 | 32px | container padding |
| --space-5 | 48px | section 間距 |
| --space-6 | 80px | slide 左右 margin |

**Grid**：deck mode 不走 CSS Grid，以 flexbox + 百分比寬度為主。常見版型：全寬單欄 / 50-50 雙欄 / 33-33-33 三欄 / 60-40 圖文分割。

## 6. Depth & Motion

**極簡深度策略**：consulting deck 不使用 box-shadow 或 elevation。所有層級差異透過背景色對比表達（白底 vs `--surface-container`）。

| 層級 | 表現方式 |
|------|----------|
| base | `--surface`（白底） |
| elevated | `--surface-container`（淺灰底） |
| emphasis | `--primary`（深色底反白） |

**Transition**：`all 0.2s ease-in-out`（hover 狀態切換用，deck 投影時通常無互動）。
**Slide 轉場**：淡入淡出 0.3s，不使用滑動或翻轉（保持專業感）。
**數據揭示動畫**：KPI 數字 counter-up 0.8s ease-out，bar chart 由左向右 stagger 0.1s/bar。

## 7. Do & Don't

- **Do** 每張內容投影片必須有 action title（結論句，≤18 CJK 字）。
- **Do** 圖表標題標註資料來源和時間範圍。
- **Do** 大量留白，單頁只傳達一個核心訊息。
- **Do** 數據使用 `--secondary` 橘色強調關鍵數字。
- **Don't** 使用漸層背景或玻璃擬態效果。
- **Don't** 在正文中使用 emoji 作為功能性圖標。
- **Don't** 單頁超過 7 個 bullet point。
- **Don't** 使用圓角超過 8px 的元件（保持銳利專業感）。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| deck (projection) | 1920×1080 | 標準投影，所有元素按 viewport 設計 |
| print (A4) | 210×297mm | PDF 輸出，字級不縮放，page-break-inside:avoid |
| tablet (preview) | 768-1024px | 預覽用途，雙欄→單欄，字級 body-md 維持 16px |
| mobile (preview) | < 768px | 預覽用途，全單欄，action title bar 字級降至 body-md |

**Touch target**：mobile 預覽模式按鈕最小 44×44px。
**deck mode 重點**：投影片設計以 1920×1080 為唯一正式 viewport，responsive 僅為預覽和 PDF 降級服務。

## 9. Agent Prompt Guide

### 必用
1. `var(--primary)` 作為 action title bar 和表頭背景
2. `var(--secondary)` 作為關鍵數據強調色和 CTA
3. `var(--surface-container)` 作為卡片和數據區塊背景
4. `var(--on-surface)` 作為主要內文色（禁止 hardcode `#212529`）
5. font-family 必須使用 `Inter, "Noto Sans TC", sans-serif`（禁止 hardcode 其他字體）

### 禁止
1. 禁止使用 Tailwind 預設 indigo 系列（#6366f1 等）或 purple 系列
2. 禁止 emoji 作為功能性 icon（清單項目符號、流程步驟圖標）
3. 禁止 lorem ipsum 或 placeholder 文字，所有文字必須來自 Facts 表
4. 禁止 box-shadow 或 drop-shadow（深度用背景色差異表達）
5. 禁止圓角 > 8px（`--rounded-xl` = 12px 僅限 avatar 等特殊場景）

### 優先順序
DESIGN.md token > mckinsey-consulting.css preset > agent 預設值

### 語氣
專業但不冰冷。像資深顧問向 C-suite 報告：數據導向、結論先行、無贅詞。中文使用通俗商務用語，避免學術腔。

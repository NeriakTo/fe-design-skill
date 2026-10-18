---
name: 晨曦琉璃 Light
description: 玻璃擬態風格的繁中 design system starter（淺色變體），承襲晨曦琉璃的通透感與漸層氛圍，將深夜版的琉璃面板翻轉為清晨的明亮色調——像晨光穿透琉璃窗。
version: 1.0.0
theme: light
colors:
  surface: "#f0f4ff"
  surface-dim: "#e4e9f5"
  surface-bright: "#ffffff"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#f5f7fc"
  surface-container: "#edf0f8"
  surface-container-high: "#e2e6f0"
  surface-container-highest: "#d6dbe8"
  on-surface: "#1a2332"
  on-surface-variant: "#4a5568"
  inverse-surface: "#1a2332"
  inverse-on-surface: "#e8ecf5"
  outline: "#8e9aab"
  outline-variant: "#c8d0dc"
  surface-tint: "#4a7ad4"
  primary: "#1a2332"
  on-primary: "#ffffff"
  primary-container: "#2d3f59"
  on-primary-container: "#c8d6e8"
  inverse-primary: "#adc9eb"
  secondary: "#7aa3d4"
  on-secondary: "#ffffff"
  secondary-container: "#d4e4f5"
  on-secondary-container: "#2a4a6b"
  tertiary: "#e48baf"
  on-tertiary: "#ffffff"
  tertiary-container: "#fce4ee"
  on-tertiary-container: "#8b2258"
  error: "#d93025"
  on-error: "#ffffff"
  error-container: "#fce8e6"
  on-error-container: "#8b1a10"
  primary-fixed: "#2d3f59"
  primary-fixed-dim: "#1a2332"
  on-primary-fixed: "#e8ecf5"
  on-primary-fixed-variant: "#c8d6e8"
  secondary-fixed: "#d4e4f5"
  secondary-fixed-dim: "#7aa3d4"
  on-secondary-fixed: "#0d2740"
  on-secondary-fixed-variant: "#2a4a6b"
  tertiary-fixed: "#fce4ee"
  tertiary-fixed-dim: "#e48baf"
  on-tertiary-fixed: "#5c0035"
  on-tertiary-fixed-variant: "#8b2258"
  background: "#f0f4ff"
  on-background: "#1a2332"
  surface-variant: "#e2e6f0"
  accent: "#4a7ad4"
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 84px
    fontWeight: "700"
    lineHeight: 90px
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: "600"
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: "500"
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  card-gap: 16px
  section-margin: 40px
  glass-padding: 20px
components:
  glass-card-standard:
    backgroundColor: rgba(255, 255, 255, 0.65)
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.glass-padding}"
  glass-card-elevated:
    backgroundColor: rgba(255, 255, 255, 0.80)
    textColor: "{colors.primary}"
    rounded: "{rounded.xl}"
    padding: "{spacing.glass-padding}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.xl}"
    height: 48px
    padding: 0 24px
  button-primary-hover:
    backgroundColor: "{colors.primary-container}"
  button-ghost:
    backgroundColor: rgba(255, 255, 255, 0.30)
    textColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.xl}"
  input-field:
    backgroundColor: rgba(255, 255, 255, 0.50)
    textColor: "{colors.primary}"
    typography: "{typography.body-md}"
    rounded: "{rounded.xl}"
    padding: 20px
    height: 48px
  weather-display-large:
    textColor: "{colors.primary}"
    typography: "{typography.display-lg}"
  metric-label:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.label-sm}"
  list-item-interactive:
    backgroundColor: transparent
    rounded: "{rounded.md}"
    padding: 12px
  list-item-interactive-hover:
    backgroundColor: rgba(255, 255, 255, 0.40)
---

<!--
Derived from chenxi-liuli (dark variant) DESIGN.md
Light variant created by Kevin Du (2026-05-24)

Based on google-labs-code/design.md examples/atmospheric-glass/DESIGN.md
Pinned upstream commit: 8ecd4645b957e6a683a05fb9c79cd6c9028873d0 (2026-04-25)
Pinned npm package: @google/design.md@0.1.1
Apache-2.0 — see ./LICENSE-APACHE-2.0
Original copyright: Copyright 2026 Google LLC

Modifications by Kevin Du on 2026-05-24:
  - Light variant of 晨曦琉璃 — all color values inverted for light theme
  - Glass card backgrounds changed from dark translucent to white translucent
  - Added accent token (#4a7ad4) for saturated blue highlights
  - Follows 9-section schema (fe-design v1.7 P9.6)
-->

## 1. Visual Theme
<!-- glassmorphism · morning-light · airy -->

晨曦琉璃 Light 是暗色版「晨曦琉璃」的日間對映——保留玻璃擬態（Glassmorphism）的通透感與層次結構，但將底色從深夜翻轉為清晨。想像一面清晨的琉璃窗：陽光穿透半透明的玻璃面板，在淡藍白的底色上投射出柔和的光影。

UI 採「明亮通透」策略：底景用淡色漸層（淺藍、薰衣草、淡粉交織）作為情感載體，前景元件化為磨砂白琉璃片，以半透明白底 + 模糊濾鏡承載資訊。整體情緒走向是清爽而精緻的，透過透明與模糊堆疊，模擬實體琉璃在晨光中的溫暖質感。

適用場景：日間使用為主的儀表板、智慧家居控制、健康與生活風格應用、SaaS 產品 landing page、資料視覺化介面。

## 2. Color Palette

色彩策略以「淺底深字」為核心。因為背景是低飽和度的淡色漸層，前景元件採半透明白搭配不同 alpha 值，文字則用深藍確保清晰可讀。

| Token | Hex | 用途 |
|-------|-----|------|
| `--bg` / background | #f0f4ff | 全域背景（淡藍白） |
| `--surface` / surface | #f0f4ff | 基底元件表面 |
| `--surface-container` | #edf0f8 | 標準容器表面 |
| `--fg` / on-surface | #1a2332 | 主要文字（深藍） |
| `--accent` / accent | #4a7ad4 | 強調色（飽和藍） |
| `--secondary` / secondary | #7aa3d4 | 次強調色（淡化藍） |
| `--tertiary` / tertiary | #e48baf | 第三色（淡化粉） |
| `--muted` / on-surface-variant | #4a5568 | 次要文字 / metric label |
| primary | #1a2332 | 最高對比元素（按鈕、標題） |
| outline | #8e9aab | 邊界線 |
| error | #d93025 | 錯誤狀態 |

- **底景畫布**：淡色 linear / radial 漸層底，常用色站包括淡藍（#dbeafe）、薰衣草（#e8d5f5）、淡粉（#fce7f3）。
- **元件表面**：所有元件背景**禁用實心色**，使用半透明白：次層 `rgba(255, 255, 255, 0.65)`，主互動區 `0.80`。
- **文字**：嚴格限定深藍（#1a2332）或中灰藍（#4a5568），確保 WCAG AA 4.5:1 對比度。

**WCAG AA 對比度**：`--on-surface`（#1a2332）對 `--background`（#f0f4ff）= 12.8:1；`--on-surface-variant`（#4a5568）對 `--background`（#f0f4ff）= 6.2:1；`--accent`（#4a7ad4）對 `--background`（#f0f4ff）= 3.8:1（僅限大字標題或圖標，非內文）。所有內文組合均超過 AA 標準 4.5:1。

## 3. Typography

採用 **Inter** 字型家族，與暗色版完全一致。幾何中性、識別度高，平衡底景模糊的有機感。CJK fallback chain：`Inter, "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif`。中英混排時 Inter 處理拉丁字元，CJK 字元由系統字型接手，字重對應一致（Regular 400 / Medium 500 / SemiBold 600）。

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|------------|----------|------------|------------|---------------|
| display-lg | Inter | 84px | 700 | 90px | -0.04em |
| headline-lg | Inter | 32px | 600 | 40px | -0.02em |
| headline-md | Inter | 24px | 500 | 32px | 0 |
| body-lg | Inter | 18px | 400 | 28px | 0 |
| body-md | Inter | 16px | 400 | 24px | 0 |
| label-sm | Inter | 12px | 600 | 16px | 0.05em |

- **層次**：超大 display 字級保留給核心數值（氣溫、即時數據），形成視覺焦點。
- **可讀性**：在磨砂琉璃上，字重比預設**加重一級**（Regular → Medium），對抗背景模糊。
- **修飾**：小字若位於底景亮區與琉璃邊緣交界，可加 text-shadow（`0px 1px 2px rgba(0,0,0,0.06)`）增加跳脫感。

> **零外部依賴注記**：本 starter 採 self-hosted Inter 字型（OFL 授權，見 `../../Inter-LICENSE-OFL`），不依賴 Google Fonts CDN。

## 4. Components

形狀語彙走「圓潤親和」風格，與暗色版一致。圓角策略：卡片 `1rem`（16px）、互動元件 `rounded-xl`（24px）、圖示 line icon + 圓角端點（stroke-width 2px）。

### Glass Containers（琉璃容器）

標準卡片用 20px blur 與半透明白底顯示一般指標；高度提升的卡片（彈窗、焦點區）用 40px blur 與更高不透明度，物理上「浮」得更高。所有琉璃元件**必有** 1px 白邊框（`rgba(255, 255, 255, 0.9)`），模擬邊緣光線折射。

| 元件 | backgroundColor | textColor | rounded | padding |
|------|----------------|-----------|---------|---------|
| glass-card-standard | rgba(255,255,255,0.65) | {colors.primary} | {rounded.lg} | 20px |
| glass-card-elevated | rgba(255,255,255,0.80) | {colors.primary} | {rounded.xl} | 20px |

### Action Elements（互動元件）

按鈕一律使用 `rounded-xl`，維持柔和有機感。主要按鈕採實心深藍色（最高對比），ghost 按鈕則保留 backdrop filter 與底景融合。

| 元件 | backgroundColor | textColor | rounded | padding | height |
|------|----------------|-----------|---------|---------|--------|
| button-primary | {colors.primary} | {colors.on-primary} | {rounded.xl} | 0 24px | 48px |
| button-ghost | rgba(255,255,255,0.30) | {colors.primary} | {rounded.xl} | 0 24px | — |

### Inputs & Interaction（輸入與互動）

可點選列表項與文字輸入框，hover 用淡淡 blur 與透明度切換，避免實心色塊跳出。

| 元件 | backgroundColor | textColor | rounded | padding | height |
|------|----------------|-----------|---------|---------|--------|
| input-field | rgba(255,255,255,0.50) | {colors.primary} | {rounded.xl} | 20px | 48px |
| list-item-interactive | transparent | {colors.primary} | {rounded.md} | 12px | — |

> 大型數值可加微妙 text-shadow（`0px 1px 2px rgba(0,0,0,0.06)`），確保在淡色底景下都清晰；metric label 使用中灰藍 `on-surface-variant`。

## 5. Layout

排版採流動性的脈絡式佈局，元件被歸納成「琉璃容器」漂浮於 viewport 安全區之內。

- **基礎網格**：8px unit，所有尺寸為 8 的倍數或 4px 半步。
- **間距 scale**：card-gap 16px / glass-padding 20px / container-padding 24px / section-margin 40px。
- **群組**：相關資料統一放入 CSS grid 或 flex 容器，間距 16px。
- **留白**：外圍邊距至少 24px，刻意露出底景漸層色彩，凸顯「漂浮」的物理感。
- **Container max-width**：1200px（桌面），100% - 48px（行動裝置）。

## 6. Depth & Motion

深度感不靠陰影濃度，而是透過光線折射與模糊強度的差異堆疊。淺色版的琉璃面板使用更高的白底 alpha，模擬光線從後方穿透的效果。

### 琉璃疊層（The Glass Stack）

| Level | 用途 | backdrop-filter | 背景 alpha | 邊框 |
|-------|------|----------------|-----------|------|
| 1（基底） | 淡色動態漸層底 | — | — | — |
| 2（標準卡片） | 一般指標 | blur(20px) | rgba(255,255,255,0.65) | 1px rgba(255,255,255,0.9) |
| 3（提升/彈窗） | 焦點區 | blur(40px) | rgba(255,255,255,0.80) | 1px rgba(255,255,255,0.9) |

- **邊緣定義**：所有琉璃面**必有** 1px 實心邊框（高不透明白）；可額外加上底端與右側 1px 內側「光暈邊」（`rgba(255, 255, 255, 0.95)`），模擬晨光從上方投射的反射。
- **陰影**：極軟大擴散（`box-shadow: 0 8px 32px 0 rgba(100, 120, 160, 0.08)`），拉開層次但不沉重。淺色版陰影使用帶藍調的淡灰，避免髒灰感。

### Motion 規範

| 屬性 | 值 | 備註 |
|------|---|------|
| transition-duration（預設） | 200ms | 互動回饋 |
| transition-duration（展開） | 350ms | 面板展開/收合 |
| transition-easing | cubic-bezier(0.4, 0, 0.2, 1) | Material ease-in-out |
| 入場動畫 | fade-in + translateY(8px) | 琉璃片「浮起」效果 |
| 退場動畫 | fade-out + translateY(-4px) | 輕柔消散 |
| 動畫最長時長 | 500ms | 超過則感知遲緩 |

## 7. Do & Don't

- **Do** 保留底景淡色漸層的「呼吸感」，外圍至少留白 24px。
- **Do** 在所有琉璃面加上 1px 白色邊框（`rgba(255,255,255,0.9)`），模擬光線折射。
- **Do** 主按鈕用實心深藍色（`--primary`）保證最高對比，給最重要的單一行為。
- **Do** 字型在琉璃上加重一級（Regular → Medium），對抗背景模糊。
- **Do** 使用 `--accent`（#4a7ad4）標記可互動元素或關鍵數據。
- **Don't** 使用實心色塊作為元件背景（會破壞玻璃擬態的氛圍）。
- **Don't** 在同一畫面混用 sharp 角（`rounded-sm`）與 `rounded-xl` — 形狀語彙要統一。
- **Don't** 把對比度低於 WCAG AA 4.5:1 的文字色放在淡色底景上 — 必驗 contrast。
- **Don't** 用過量 hover 特效（scale + shadow + color 同時變）— 互動回饋要精準不喧鬧。
- **Don't** 使用深色陰影（`rgba(0,0,0,0.3)` 以上）— 淺色版陰影必須輕盈帶藍調。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| sm（mobile） | < 640px | 單欄堆疊；display-lg 降為 48px；glass-padding 縮為 16px |
| md（tablet） | 640–1024px | 雙欄 grid；標準字級；container-padding 24px |
| lg（desktop） | > 1024px | 三欄或自由 grid；完整字級階梯；container-padding 24px |

- **Touch target**：行動裝置互動元素最小 44x44px（WCAG 2.5.5）。
- **底景漸層**：小螢幕上降低色站數量（2 站取代 3 站），避免 GPU 繪製負擔。
- **琉璃 blur**：在低效能裝置上退化為 `backdrop-filter: blur(10px)` + 提高背景 alpha 至 0.75，維持可讀性。

## 9. Agent Prompt Guide

### 必用
1. `var(--surface)` 或 YAML `{colors.surface}` 作為元件底色，禁止 hardcode hex。
2. `var(--primary)` 作為最高對比文字/按鈕色（深藍 #1a2332）。
3. `var(--accent)` 或 `{colors.accent}` 作為飽和藍強調色。
4. `var(--secondary)` 或 `{colors.secondary}` 作為次強調色。
5. `{typography.body-md}` 作為內文預設字級。
6. `{rounded.xl}` 作為互動元件圓角。

### 禁止
1. 禁止使用 Tailwind 預設 indigo 系列（#6366f1 / #4f46e5 / #4338ca 等）。
2. 禁止 emoji 作為功能性 icon——使用 line icon（stroke-width 2px）。
3. 禁止實心色塊作為卡片背景——必須使用 rgba 半透明白。
4. 禁止 lorem ipsum 或 placeholder 文字。
5. 禁止 purple→blue 兩段式 trust gradient 作為裝飾。
6. 禁止深色重陰影（`rgba(0,0,0,0.2)` 以上）——淺色版一律用 `rgba(100,120,160,0.08)` 級輕陰影。

### 優先順序
YAML frontmatter token > 第 7 節 Do & Don't > craft rules > agent 預設值

### 語氣
清爽而精緻、溫暖但不甜膩。文案用短句、避免驚嘆號、資料面板以數值為主角。像清晨的第一道光——明亮、從容、令人安心。

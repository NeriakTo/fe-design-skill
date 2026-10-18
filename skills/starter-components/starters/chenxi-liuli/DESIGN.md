---
name: 晨曦琉璃
description: 玻璃擬態風格的繁中 design system starter，承襲深夜微光與漸層的氛圍，把資訊面板做成漂浮在多彩底景上的琉璃片。
colors:
  surface: "#0b1326"
  surface-dim: "#0b1326"
  surface-bright: "#31394d"
  surface-container-lowest: "#060e20"
  surface-container-low: "#131b2e"
  surface-container: "#171f33"
  surface-container-high: "#222a3d"
  surface-container-highest: "#2d3449"
  on-surface: "#dae2fd"
  on-surface-variant: "#c4c7c8"
  inverse-surface: "#dae2fd"
  inverse-on-surface: "#283044"
  outline: "#8e9192"
  outline-variant: "#444748"
  surface-tint: "#c6c6c7"
  primary: "#ffffff"
  on-primary: "#2f3131"
  primary-container: "#e2e2e2"
  on-primary-container: "#636565"
  inverse-primary: "#5d5f5f"
  secondary: "#adc9eb"
  on-secondary: "#14324e"
  secondary-container: "#304b68"
  on-secondary-container: "#9fbbdd"
  tertiary: "#ffffff"
  on-tertiary: "#620040"
  tertiary-container: "#ffd8e7"
  on-tertiary-container: "#ab3779"
  error: "#ffb4ab"
  on-error: "#690005"
  error-container: "#93000a"
  on-error-container: "#ffdad6"
  primary-fixed: "#e2e2e2"
  primary-fixed-dim: "#c6c6c7"
  on-primary-fixed: "#1a1c1c"
  on-primary-fixed-variant: "#454747"
  secondary-fixed: "#d0e4ff"
  secondary-fixed-dim: "#adc9eb"
  on-secondary-fixed: "#001d35"
  on-secondary-fixed-variant: "#2d4965"
  tertiary-fixed: "#ffd8e7"
  tertiary-fixed-dim: "#ffafd3"
  on-tertiary-fixed: "#3d0026"
  on-tertiary-fixed-variant: "#85145a"
  background: "#0b1326"
  on-background: "#dae2fd"
  surface-variant: "#2d3449"
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
    backgroundColor: rgba(255, 255, 255, 0.1)
    textColor: "{colors.primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.glass-padding}"
  glass-card-elevated:
    backgroundColor: rgba(255, 255, 255, 0.2)
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
    backgroundColor: "{colors.primary-fixed-dim}"
  button-ghost:
    backgroundColor: rgba(255, 255, 255, 0.05)
    textColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.xl}"
  input-field:
    backgroundColor: rgba(255, 255, 255, 0.1)
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
    backgroundColor: rgba(255, 255, 255, 0.1)
---

<!--
Derived from google-labs-code/design.md examples/atmospheric-glass/DESIGN.md
Pinned upstream commit: 8ecd4645b957e6a683a05fb9c79cd6c9028873d0 (2026-04-25)
Pinned npm package: @google/design.md@0.1.1
Apache-2.0 — see ./LICENSE-APACHE-2.0
Original copyright: Copyright 2026 Google LLC

Modifications by Kevin Du (2026-04-25):
  - Translated to Traditional Chinese (繁中翻譯)
  - Adapted brand voice for Taiwanese aesthetic (台灣品牌語感重寫)
  - Renamed "Atmospheric Glass" → "晨曦琉璃" (chenxi-liuli)
  - Added Do's and Don'ts section (補完 spec.md 8 大 section)
  - Added `description` field in YAML frontmatter (upstream 無此欄位)
  - Token values (colors / typography / rounded / spacing / components) unchanged from upstream

Migrated to 9-section schema (2026-05-03, fe-design v1.7 P9.6):
  - Reorganized sections: Brand & Style→Visual Theme, Colors→Color Palette,
    Shapes merged into Components, Elevation & Depth→Depth & Motion
  - Added §8 Responsive and §9 Agent Prompt Guide (new sections)
  - Added Color Palette token table and Typography scale table
-->

## 1. Visual Theme
<!-- glassmorphism · atmospheric · premium -->

晨曦琉璃以高擬真度的玻璃擬態（Glassmorphism）為基底，呈現清晰、有層次、具當代精緻感的視覺氛圍。整套品牌個性兼顧詩意與功能，把原本繁瑣的資料面板，轉化成一片片漂浮的透明琉璃，讓使用者在凝視之間感到從容。

UI 採「鮮豔極簡」策略：底景用多彩漸層（粉、紫、藍交織）作為情感載體，前景元件則化為磨砂琉璃片，承擔資訊聚焦的角色。整體情緒走向是沉穩而高級的，透過透明與模糊堆疊，模擬實體玻璃漂浮在數位流體之中的感受。

適用場景：氣象儀表板、智慧家居控制、即時資料監控介面、金融儀表板、夜間使用為主的高階產品 landing。

## 2. Color Palette

色彩策略以「光度與對比」為核心。因為背景是飽和度極高的多色漸層，前景元件刻意採單色白系搭配不同 alpha 值，確保任何底景下文字都清晰可讀。

| Token | Hex | 用途 |
|-------|-----|------|
| `--bg` / background | #0b1326 | 全域背景 |
| `--surface` / surface | #0b1326 | 基底元件表面 |
| `--surface-container` | #171f33 | 標準容器表面 |
| `--fg` / on-surface | #dae2fd | 主要文字 |
| `--accent` / secondary | #adc9eb | 強調色（冷調藍銀） |
| `--muted` / on-surface-variant | #c4c7c8 | 次要文字 / metric label |
| primary | #ffffff | 最高對比元素（按鈕、標題） |
| outline | #8e9192 | 邊界線 |
| error | #ffb4ab | 錯誤狀態 |

- **底景畫布**：多色 linear / radial 漸層底，常用色站包括深邃藍（#1E3A8A）、絢紫（#7E22CE）、柔粉（#DB2777）。
- **元件表面**：所有元件背景**禁用實心色**，使用半透明白：次層 `rgba(255, 255, 255, 0.1)`，主互動區 `0.2`。
- **文字**：嚴格限定純白（#FFFFFF）或高亮銀（#E2E8F0），確保 WCAG AA 4.5:1 對比度。

## 3. Typography

採用 **Inter** 字型家族，幾何中性、識別度高，平衡底景模糊的有機感。CJK fallback chain：`Inter, "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif`。中英混排時 Inter 處理拉丁字元，CJK 字元由系統字型接手，字重對應一致（Regular 400 / Medium 500 / SemiBold 600）。

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
- **修飾**：小字若位於底景明亮區，可加 text-shadow（`0px 2px 4px rgba(0,0,0,0.15)`）增加跳脫感。

> **零外部依賴注記**：本 starter 採 self-hosted Inter 字型（OFL 授權，見 `Inter-LICENSE-OFL`），不依賴 Google Fonts CDN。

## 4. Components

形狀語彙走「圓潤親和」風格，搭配底景的流體感。圓角策略：卡片 `1rem`（16px）、互動元件 `rounded-xl`（24px）、圖示 line icon + 圓角端點（stroke-width 2px）。

### Glass Containers（琉璃容器）

標準卡片用 20px blur 顯示一般指標；高度提升的卡片（彈窗、焦點區）用 40px blur 與更高不透明度，物理上「浮」得更高。所有琉璃元件**必有** 1px 白邊，模擬邊緣光線折射。

| 元件 | backgroundColor | textColor | rounded | padding |
|------|----------------|-----------|---------|---------|
| glass-card-standard | rgba(255,255,255,0.1) | {colors.primary} | {rounded.lg} | 20px |
| glass-card-elevated | rgba(255,255,255,0.2) | {colors.primary} | {rounded.xl} | 20px |

### Action Elements（互動元件）

按鈕一律使用 `rounded-xl`，維持柔和有機感。主要按鈕採實心白色（最高對比），ghost 按鈕則保留 backdrop filter 與底景融合。

| 元件 | backgroundColor | textColor | rounded | padding | height |
|------|----------------|-----------|---------|---------|--------|
| button-primary | {colors.primary} | {colors.on-primary} | {rounded.xl} | 0 24px | 48px |
| button-ghost | rgba(255,255,255,0.05) | {colors.primary} | {rounded.xl} | 0 24px | — |

### Inputs & Interaction（輸入與互動）

可點選列表項與文字輸入框，hover 用淡淡 blur 與透明度切換，避免實心色塊跳出。

| 元件 | backgroundColor | textColor | rounded | padding | height |
|------|----------------|-----------|---------|---------|--------|
| input-field | rgba(255,255,255,0.1) | {colors.primary} | {rounded.xl} | 20px | 48px |
| list-item-interactive | transparent | {colors.primary} | {rounded.md} | 12px | — |

> 大型數值加微妙 text-shadow，確保在多彩底景下都清晰；metric label 使用銀調 `on-surface-variant`。

## 5. Layout

排版採流動性的脈絡式佈局，元件被歸納成「琉璃容器」漂浮於 viewport 安全區之內。

- **基礎網格**：8px unit，所有尺寸為 8 的倍數或 4px 半步。
- **間距 scale**：card-gap 16px / glass-padding 20px / container-padding 24px / section-margin 40px。
- **群組**：相關資料統一放入 CSS grid 或 flex 容器，間距 16px。
- **留白**：外圍邊距至少 24px，刻意露出底景色彩，凸顯「漂浮」的物理感。
- **Container max-width**：1200px（桌面），100% - 48px（行動裝置）。

## 6. Depth & Motion

深度感不靠陰影濃度，而是透過光線折射與模糊強度的差異堆疊。

### 琉璃疊層（The Glass Stack）

| Level | 用途 | backdrop-filter | 背景 alpha | 邊框 |
|-------|------|----------------|-----------|------|
| 1（基底） | 動態漸層底 | — | — | — |
| 2（標準卡片） | 一般指標 | blur(20px) | rgba(255,255,255,0.1) | 1px rgba(255,255,255,0.2) |
| 3（提升/彈窗） | 焦點區 | blur(40px) | rgba(255,255,255,0.2) | 1px rgba(255,255,255,0.2) |

- **邊緣定義**：所有琉璃面**必有** 1px 實心邊框；可額外加上頂端與左側 1px 內側「光暈邊」模擬光源反射。
- **陰影**：極軟大擴散（`box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1)`），拉開層次但不沉重。

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

- **Do** 保留底景多彩漸層的「呼吸感」，外圍至少留白 24px。
- **Do** 在所有琉璃面加上 1px 白色邊框，模擬光線折射。
- **Do** 主按鈕用實心白色保證最高對比，給最重要的單一行為。
- **Do** 字型在琉璃上加重一級（Regular → Medium），對抗背景模糊。
- **Don't** 使用實心色塊作為元件背景（會破壞玻璃擬態的氛圍）。
- **Don't** 在同一畫面混用 sharp 角（`rounded-sm`）與 `rounded-xl` — 形狀語彙要統一。
- **Don't** 把對比度低於 WCAG AA 4.5:1 的文字色放在多彩底景上 — 必驗 contrast。
- **Don't** 用過量 hover 特效（scale + shadow + color 同時變）— 互動回饋要精準不喧鬧。

## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| sm（mobile） | < 640px | 單欄堆疊；display-lg 降為 48px；glass-padding 縮為 16px |
| md（tablet） | 640–1024px | 雙欄 grid；標準字級；container-padding 24px |
| lg（desktop） | > 1024px | 三欄或自由 grid；完整字級階梯；container-padding 24px |

- **Touch target**：行動裝置互動元素最小 44×44px（WCAG 2.5.5）。
- **底景漸層**：小螢幕上降低色站數量（2 站取代 3 站），避免 GPU 繪製負擔。
- **琉璃 blur**：在低效能裝置上退化為 `backdrop-filter: blur(10px)` + 提高背景 alpha 至 0.15，維持可讀性。

## 9. Agent Prompt Guide

### 必用
1. `var(--surface)` 或 YAML `{colors.surface}` 作為元件底色，禁止 hardcode hex。
2. `var(--primary)` 作為最高對比文字/按鈕色。
3. `var(--secondary)` 或 `{colors.secondary}` 作為強調色。
4. `{typography.body-md}` 作為內文預設字級。
5. `{rounded.xl}` 作為互動元件圓角。

### 禁止
1. 禁止使用 Tailwind 預設 indigo 系列（#6366f1 / #4f46e5 / #4338ca 等）。
2. 禁止 emoji 作為功能性 icon——使用 line icon（stroke-width 2px）。
3. 禁止實心色塊作為卡片背景——必須使用 rgba 半透明。
4. 禁止 lorem ipsum 或 placeholder 文字。
5. 禁止 purple→blue 兩段式 trust gradient 作為裝飾。

### 優先順序
YAML frontmatter token > § 7 Do & Don't > craft rules > agent 預設值

### 語氣
沉穩而高級、詩意但不浮誇。文案用短句、避免驚嘆號、資料面板以數值為主角。

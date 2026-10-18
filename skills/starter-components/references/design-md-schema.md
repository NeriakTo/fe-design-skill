# DESIGN.md 9-Section Schema

> 版本：v1.0（fe-design v1.7 P9.6）
> 用途：標準化所有 starter / 品牌模板的 DESIGN.md 格式
> 狀態：規範

---

## 概述

每個 starter 的 `DESIGN.md` 必須包含兩大部分：

1. **YAML frontmatter** — machine-readable design tokens（colors / typography / spacing / rounded / components）
2. **Markdown body** — 9 個標準 section，提供人類可讀的設計意圖與使用指南

YAML frontmatter 與 Google `@google/design.md@0.1.1 lint` 相容（8 條結構規則），Markdown body 採本規範的 9-section 架構。

---

## YAML Frontmatter 規格

### 必要欄位

```yaml
---
name: "{品牌名稱}"
description: "{一句話描述設計風格與適用場景}"
colors:
  primary: "{hex}"
  on-primary: "{hex}"
  surface: "{hex}"
  on-surface: "{hex}"
  # 其餘 semantic token 依需求擴展
typography:
  body-md:
    fontFamily: "{font name}"
    fontSize: "{N}px"
    fontWeight: "{weight}"
    lineHeight: "{N}px"
  # 至少定義 body-md；建議補 display-lg / headline-lg / label-sm
spacing:
  unit: "{N}px"
  # 建議補 container-padding / card-gap / section-margin
rounded:
  DEFAULT: "{value}"
  # 建議補 sm / md / lg / xl / full
components:
  # 至少定義 3 個核心元件（card / button / input 或等效）
  card-default:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "{spacing.card-gap}"
---
```

### 選用欄位

| 欄位 | 用途 | 範例 |
|------|------|------|
| `craft.requires` | 引用 craft rules（P9.8） | `[anti-ai-slop, typography]` |
| `version` | 設計系統版本 | `1.0.0` |
| `theme` | 主題標識 | `dark` / `light` / `adaptive` |

### Token 值格式

- **Colors**：hex 為必要格式（`#RRGGBB`）；OKLch 為選用（v1.8 可能升為必要）
- **Typography**：fontFamily 為字串、fontSize/lineHeight 為 `Npx`、fontWeight 為數字字串
- **Spacing / Rounded**：含單位（`Npx` 或 `Nrem`）
- **Component references**：`"{path.to.token}"` 語法引用其他 token

---

## Markdown Body — 9 Section 架構

### Section 順序（必須遵守）

| # | Section 標題 | 對應 Google spec | 必要性 |
|---|---|---|---|
| 1 | Visual Theme | Overview (Brand & Style) | **必要** |
| 2 | Color Palette | Colors | **必要** |
| 3 | Typography | Typography | **必要** |
| 4 | Components | Shapes + Components | **必要** |
| 5 | Layout | Layout & Spacing | **必要** |
| 6 | Depth & Motion | Elevation & Depth | **必要** |
| 7 | Do & Don't | Do's and Don'ts | **必要** |
| 8 | Responsive | 新增（Google spec 無） | **必要** |
| 9 | Agent Prompt Guide | 新增（Google spec 無） | **必要** |

### 各 Section 規格

#### § 1. Visual Theme

整體視覺方向的定性描述。

**必須包含**：
- 設計哲學標籤（1-3 個，例：glassmorphism / brutalist / editorial / minimal）
- 適用場景列表（2-5 個具體場景）
- 情緒關鍵字（3-5 個形容詞）

**字數**：100-300 字

**範例開頭**：
```markdown
## 1. Visual Theme
<!-- glassmorphism · atmospheric · premium -->

{品牌名}以...為基底，呈現...的視覺氛圍。
```

#### § 2. Color Palette

色彩策略與 CSS custom properties 對照。

**必須包含**：
- 色彩策略描述（1-3 段，說明配色邏輯）
- CSS custom properties 表格或列表，至少含：
  - `--bg` / `--surface` / `--fg` / `--accent` / `--muted`（或等效語義名）
  - hex 值（必要）+ OKLch 值（選用）
- WCAG AA 對比度承諾（文字 vs 背景）

**格式要求**：
```markdown
## 2. Color Palette

{色彩策略描述}

| Token | Hex | 用途 |
|-------|-----|------|
| --bg | #0b1326 | 全域背景 |
| --surface | #171f33 | 元件表面 |
| --fg | #dae2fd | 主要文字 |
| --accent | #adc9eb | 強調色 |
| --muted | #8e9192 | 次要文字 |
```

#### § 3. Typography

字體家族、字重階梯、字級系統、字距、OpenType features。

**必須包含**：
- font-family 宣告（display + body，含 CJK fallback chain）
- 字級階梯表（至少 4 級：display / headline / body / label）
- 每級含：fontSize (px) / fontWeight / lineHeight (px) / letterSpacing (em)
- CJK 特殊處理說明（若適用）

**格式要求**：
```markdown
## 3. Typography

| 層級 | font-family | fontSize | fontWeight | lineHeight | letterSpacing |
|------|------------|----------|------------|------------|---------------|
| display-lg | Inter | 84px | 700 | 90px | -0.04em |
| headline-lg | Inter | 32px | 600 | 40px | -0.02em |
| body-md | Inter | 16px | 400 | 24px | 0 |
| label-sm | Inter | 12px | 600 | 16px | 0.05em |
```

#### § 4. Components

常用元件規格。合併原 Google spec 的 Shapes + Components。

**必須包含**：
- 至少 3 個核心元件（card / button / input 或等效）
- 核心元件四欄必填：backgroundColor / textColor / rounded / padding
- State/variant token（如 `button-primary-hover`）可只定義差異欄位（partial）
- 形狀語彙描述（圓角策略、一致性規則）

**格式要求**：依元件或元件群組使用 `###` 子標題，含 token 對照表。群組式（如 Glass Containers 含多個 card 變體）比逐元件拆分更易讀。

#### § 5. Layout

Grid 系統、spacing scale、max-width、breakpoints。

**必須包含**：
- 基礎網格單位（如 8px）
- Spacing scale（至少 4 級）
- Container max-width
- 群組間距規則

#### § 6. Depth & Motion

Shadow 系統、transition 規範、動畫時長。合併原 Google spec 的 Elevation & Depth + 動畫面向。

**必須包含**：
- 深度層級定義（至少 2 級：base / elevated）
- Shadow 值（box-shadow CSS 值）
- Transition 預設值（duration / easing）
- 動畫規範（入場 / 退場 / 持續時長範圍）

#### § 7. Do & Don't

明確的設計規則。

**必須包含**：
- 至少 3 條 Do
- 至少 3 條 Don't
- 每條用一句話，具體可執行（非「做好的設計」這類空話）

**格式要求**：
```markdown
## 7. Do & Don't

- **Do** {具體規則}。
- **Do** {具體規則}。
- **Do** {具體規則}。
- **Don't** {具體禁止事項}。
- **Don't** {具體禁止事項}。
- **Don't** {具體禁止事項}。
```

#### § 8. Responsive

Mobile-first breakpoints 與行為差異。

**必須包含**：
- Breakpoints 定義（至少 sm / md / lg）
- 各斷點的關鍵行為差異（字級縮放、欄數變化、元件堆疊方式）
- Touch target 最小尺寸（mobile）

**格式要求**：
```markdown
## 8. Responsive

| Breakpoint | 寬度 | 行為 |
|------------|------|------|
| sm (mobile) | < 640px | 單欄、字級 -1 級 |
| md (tablet) | 640-1024px | 雙欄、標準字級 |
| lg (desktop) | > 1024px | 三欄、完整 layout |
```

#### § 9. Agent Prompt Guide

給 LLM 的明確指令——這是 9-section 架構的核心差異化。

**必須包含**：
- **必用 token**：5 個 agent 產出時必須使用的 token，格式為 CSS variable `var(--xxx)` 或 YAML token reference `{path.to.token}`（兩者等效，前者用於 CSS context，後者用於 YAML/JSON context）
- **禁止項**：5 個明確禁止的做法（含具體值，如「禁止 `#6366f1` indigo」）
- **優先順序**：當規則衝突時的決策優先級
- **語氣指引**：產出的文案風格（如「專業但不冰冷」）

**格式要求**：
```markdown
## 9. Agent Prompt Guide

### 必用
1. `var(--bg)` 作為全域背景，禁止 hardcode hex
2. `var(--accent)` 作為互動元素強調色
3. `var(--font-display)` 用於 h1/h2
4. `var(--font-body)` 用於內文
5. `var(--radius-lg)` 作為 card 圓角

### 禁止
1. 禁止使用 Tailwind 預設 indigo 系列（#6366f1 等）
2. 禁止 emoji 作為功能性 icon
3. 禁止 lorem ipsum 或 placeholder 文字
4. 禁止未標來源的數據宣稱
5. 禁止 purple→blue trust gradient

### 優先順序
DESIGN.md token > craft rules > agent 預設值

### 語氣
{品牌語氣描述}
```

---

## 與 Google design.md lint 的相容性

### 預期 Warning（正常現象）

本 schema 的 section 命名與排序與 Google spec 不完全一致，conforming 的 DESIGN.md 跑 `npx @google/design.md@0.1.1 lint` 會產生以下 **預期 warning**：

| 規則 | 預期行為 | 原因 |
|------|---------|------|
| `orphaned-tokens` | warning（本地 remap 為 nit） | Material Design 完整 palette 複製來的 token 中大量未被 component 引用（chenxi-liuli 實測 43 個） |
| `section-order` | @0.1.1 實測未觸發（保留供未來版本參考） | 本 schema §4 Components 在 §5 Layout 前，與 Google 原序不同 |

**實測基線（chenxi-liuli, @0.1.1）**：`0 errors, 43 warnings (all orphaned-tokens), 1 info (token-summary)`。

Anti-slop-review 的 design-md-lint 層會 passthrough 這些 warning，不影響最終 verdict（`orphaned-tokens` 本地 remap 為 `nit`，`section-order` 為 warning 不升 hard fail）。

### 不受影響的規則

以下規則完全相容，無預期 warning：
- `broken-ref` — token reference 語法不變
- `contrast-ratio` — 對比度計算不變
- `missing-primary` — `colors.primary` 仍為必要
- `missing-typography` — `typography` 區塊仍為必要
- `orphaned-tokens` — 取決於 component 引用覆蓋率（與 schema 無關）
- `token-summary` — 純資訊輸出

---

## 命名對照表

| 本 Schema Section | Google spec Section | 差異說明 |
|---|---|---|
| Visual Theme | Overview / Brand & Style | 更聚焦視覺面，去掉品牌故事 |
| Color Palette | Colors | 語義更明確 |
| Typography | Typography | 一致 |
| Components | Shapes + Components | 合併——形狀規則融入元件定義 |
| Layout | Layout & Spacing | 簡化名稱 |
| Depth & Motion | Elevation & Depth | 加入動畫面向 |
| Do & Don't | Do's and Don'ts | 簡化 |
| Responsive | （新增） | Google spec 未定義 |
| Agent Prompt Guide | （新增） | 本 schema 核心差異化 |

---

## Checklist（品質檢核）

DESIGN.md 完成後，逐項確認：

### YAML Frontmatter
- [ ] 含 `name` + `description`
- [ ] `colors` 含 `primary` + `on-primary` + `surface` + `on-surface`
- [ ] `typography` 至少含 `body-md`
- [ ] `spacing` 含 `unit`
- [ ] `rounded` 含 `DEFAULT`
- [ ] `components` 至少 3 個核心元件，每個含 backgroundColor / textColor / rounded / padding

### Markdown Body — Section 級
- [ ] 含完整 9 個 `##` section，順序正確（1→9）
- [ ] § 1 Visual Theme 含設計哲學標籤 + 適用場景 + 情緒關鍵字
- [ ] § 2 Color Palette 含 token 表 + WCAG AA 對比度承諾
- [ ] § 3 Typography 含字級階梯表（≥4 級）+ CJK fallback chain（若適用）
- [ ] § 4 Components 含 ≥3 元件群組的 token 對照表
- [ ] § 6 Depth & Motion 含 motion 規範（transition duration / easing / 入退場）
- [ ] § 7 Do & Don't 至少各 3 條
- [ ] § 8 Responsive 含 breakpoint 表 + touch target 尺寸
- [ ] § 9 Agent Prompt Guide 含必用 5 + 禁止 5 + 優先順序 + 語氣

### Lint 驗證
- [ ] `npx @google/design.md@0.1.1 lint` 無 error（warning/info 可接受）
- [ ] `python3 scan.py` 無 P0 finding

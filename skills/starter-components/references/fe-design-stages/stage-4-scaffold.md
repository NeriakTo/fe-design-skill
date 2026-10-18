> 用途：fe-design pipeline 第 4 階段 Scaffold 初始化完整規格。
> 來源：自 fe-design.md v1.8.3 第 403–591 行拆出，2026-08-27。
> 本檔由 ~/.claude/commands/fe-design.md 於該階段以 Read 載入；修改本檔等於修改 pipeline。
> 範圍：只承接原主檔第 4 階段內容。

### [4/7] 🧱 Scaffold 初始化

呼叫 `Skill starter-components`：

| Mode | 取用 scaffold |
|---|---|
| `deck` | `scaffolds/deck_stage.js`（單檔，≤10 頁預設）或 `scaffolds/deck_index.html`（多檔，≥10 頁）— 見下方架構選擇規則 |
| `page` | `scaffolds/browser_window.jsx`（預覽用 chrome）+ `scaffolds/reading_progress.mjs`（頁首閱讀進度條，必含）|
| `app` | `scaffolds/design_canvas.jsx` + 選用裝置外框（`ios_frame.jsx` / `android_frame.jsx` / `macos_window.jsx`）+ 多屏 flow demo 用 `scaffolds/app_phone.jsx`（v1.5 P7.8）|
| `system` | （跳過，stage 3 已產 DESIGN.md）|
| `migrate` | （跳過，stage 6 才取 patch 用）|

**Mode 適用範圍**：

- **`deck` / `page` mode**：vanilla HTML，直接走 `scaffolds/` 基底版
- **`app` mode**：走 `scaffolds/` 基底版（React variants 已於 v1.7 移除，未來視需求重建）
- **`system` / `migrate` mode**：跳過 stage 4，不適用

#### Deck mode 架構選擇規則（v1.5 P7.7）

| 場景 | 架構 | scaffold | 理由 |
|---|---|---|---|
| ≤10 頁 / pitch deck / 跨頁共享 CSS 狀態 | 單檔 | `deck_stage.js` | CSS 共享、狀態管理方便、PPTX 翻譯器直接支援 |
| ≥10 頁 / 學術課件 / 多 agent 並行撰寫 | 多檔 | `deck_index.html` + `slides/*.html` | 每頁獨立 HTML，免 CSS 串擾，可平行編輯 |

多檔架構注意事項：
- 每頁 slide 為獨立 HTML，透過 iframe 載入
- `window.__deck` API 為單檔架構的核心子集（slideCount / current / next / prev / goto / togglePrint；不含 toggleBlackout / openNotes）
- PPTX 翻譯需由 `export-deck-pptx.mjs` wrapper 逐檔處理（v1.1 待實作）
- 預設使用單檔架構；僅在 brief 明確指定大型 deck 或多 agent 並行時切換

#### Deck mode 色盤與字級

依 brief 從 `starters/` 選一套 `DESIGN.md` 作為基底（chenxi-liuli、chenxi-liuli-light、consulting-professional、corporate-warm、editorial-minimal、tech-dark）。署名與變體規則改由 deck-gates 的設定檔定義（見 `skills/starter-components/scripts/` 的設定檔），預設不檢查署名。
先把 Stage 1 的字體 preset 複製到 case，再複製並載入 `design-tokens-presets/` 內選定的 preset（例如 `mckinsey-consulting.css`），確保色盤與固定 px 字級最後生效。CSS 使用專案相對路徑或 inline，不能把 `~` 當瀏覽器路徑。
既有 working styles.css 保留結構，更新 token／alias 後實測。圖表需要的 token 以所選色盤建立 alias，不引入其他色碼。

#### Deck mode action title（pyramid principle）標準（v1.4-short §24.11 P6.10；v1.8 register-aware）

> **v1.8 register-aware 修訂**：本段全套機制（`slide_action_titles[]` frontmatter + verify 腳本 + ≤18 CJK）僅在 Art Direction Contract 的文案 register = **consulting** 時強制。register = educational-warm / product 時，標題改用教學點句／利益句（「成績是三扇窗，不是標籤」型——有觀點、是結論、不是名詞），僅人審不跑 verify 腳本。**noun-only 標題禁令（「XX 概況」「XX 簡介」）全 register 不變。** reader_prior = zero 時再加一條全 register 通用：標題不得含同頁未白話定義的術語（v1.8.3 P11.2）。

`deck` mode 採 consulting-style（McKinsey / BCG / Bain）時，**每張內容投影片頂端必須有 action title**（pyramid principle 必用）：

- **action title 定義**：一句結論性句子（**≤ 18 個 CJK 字**，標點與半形數字/英文不計入），不是名詞性 label。
- **正反例**：
  - ✅「2026 Q2 營收成長 30% 來自三大新品線」（結論：誰、做了什麼、結果）
  - ✅「QCC 從日本起家，60 年內擴及全球製造業」（結論：起源 + 擴展軌跡）
  - ❌「2026 Q2 營收概況」（純名詞 label，沒結論）
  - ❌「QCC 簡介」（純名詞 label）
- **適用範圍 selector**（formal）：`section.slide:not(.slide-cover):not(.slide-section-divider)` — 即 class 為純 `slide` 的內容投影片。某 fullday 簡報範例是 47/55（cover 2 + divider 6 + 內容 47）。
  - **不適用**：`section.slide.slide-cover`（封面用 cover title）、`section.slide.slide-section-divider`（章節分隔頁用 section title 而非 action title）。
- **HTML 結構**：`<section class="slide"><h1 class="slide-title">…</h1>…</section>`。
  - 標題 token 引用 `--action-title-fs / --action-title-fw`（由所選 design-tokens preset 或 starter 提供）；既有 case 已有 `--type-h1` 等自訂 token 可在 case `:root` 加 alias（`--action-title-fs: var(--type-h1)`）。
- **DESIGN.md 必含 `slide_action_titles[]` 欄位**（pyramid 對齊清單；spec authoritative form）：
  - **Canonical (machine-readable)**：DESIGN.md frontmatter 加 YAML array，每筆 flow-style mapping `{section, title, cjk}`，**逐張對應內容投影片**：

    ```yaml
    ---
    case: example-fullday-deck
    mode: deck
    direction: McKinsey / BCG consulting deck
    slide_action_titles:
      - {section: "01 QCC 概論 · 定義", title: "QCC 是員工自發組成、自主解題的小型品管組織", cjk: 18}
      - {section: "01 QCC 概論 · 沿革", title: "QCC 從日本起家，60 年內擴及全球製造業", cjk: 14}
      - {section: "01 QCC 概論 · 三層價值", title: "QCC 的三層價值：個人成長、團隊協作、企業競爭力", cjk: 18}
      # … 共 47 筆對應 47 張內容投影片
    ---
    ```

  - **Optional (human-readable)**：body 可額外加 `## Action Titles` markdown table 給審查人員快讀；表格列數必須等於 frontmatter 陣列長度（verify 會交叉檢查）：

    ```markdown
    ## Action Titles

    | # | section | action title | CJK |
    |---|---------|--------------|-----|
    | 01 | 01 QCC 概論 · 定義 | QCC 是員工自發組成、自主解題的小型品管組織 | 18 |
    | 02 | 01 QCC 概論 · 沿革 | QCC 從日本起家，60 年內擴及全球製造業 | 14 |
    | … | … | … | … |
    ```

  - **欄位語意**：`section`（slide-eyebrow 文字）、`title`（h1.slide-title 文字）、`cjk`（CJK 字元數，verify 即時計算後比對）。**只列內容投影片**（cover / section-divider 除外）。
  - **YAML 字串約束（emitter/parser lockstep）**：canonical schema 限制 `section` 與 `title` 雙引號內**只接受兩種 escape**：`\"`（字面 "）與 `\\`（字面 \）。**禁用** `\n` / `\t` / `\b` / `\f` / `\xNN` / `\uNNNN` / `\UNNNNNNNN` 等 YAML 1.2 擴充 escape — 含這類字元的文字請改寫成實際 Unicode codepoint 直寫（CJK / emoji 直接打），或重新設計 title 避免換行/控制字元。verify 會 reject 所有不在白名單內的 backslash sequence。
  - `cjk` 欄位是反向驗證用，必須 ≤ 18；超過時 case 必修（短不了的特例不應超過 24，且需在 case 內加 `<!-- action-title-overflow: <reason> -->` HTML comment）。
- **反向驗證腳本**（每 case 推薦放）：`verify-action-titles.mjs` 必驗 5 項：
  1. 每張 `section.slide:not(.slide-cover):not(.slide-section-divider)` 都有 `<h1 class="slide-title">` + 文字非空
  2. 每張 title CJK ≤ 18
  3. `deck.html` 與 `deck-standalone.html` 47 個 title + section 必須完全一致（cross-file parity）
  4. DESIGN.md frontmatter `slide_action_titles[]` 陣列長度 = 內容投影片數，且每筆 `section/title/cjk` 與 HTML 抽出的值一致（content parity，不是只算 row count）
  5. （optional）DESIGN.md body `## Action Titles` table row 數 = 陣列長度且各列內容對齊
- **禁止自寫 noun-only 標題**：deck mode v1.4+ 不再允許「XX 概況 / XX 分析 / XX 簡介」之類 label；遇到「真的只想列名詞」的場景請改用 cover title 或 section divider，而非塞進 `<h1 class="slide-title">`。

#### Deck mode chart 元件標準（v1.4-short §24.10 P6.9）

`deck` mode 採 consulting-style 時，圖表元件 **優先用 starter 版本**（`~/.claude/skills/starter-components/scaffolds/charts/`）：

```js
// 三個元件 + 共用 CSS（B 拷貝法或 C file:// 法擇一，同 P6.8 規則）
import { PieChart } from '~/.claude/skills/starter-components/scaffolds/charts/pie_chart.mjs';
import { BarChart } from '~/.claude/skills/starter-components/scaffolds/charts/bar_chart.mjs';
import { KpiCard } from '~/.claude/skills/starter-components/scaffolds/charts/kpi_card.mjs';
```

```html
<!-- charts.css 先載；暖色 preset 最後覆蓋 token -->
<link rel="stylesheet" href="scaffolds/charts/charts.css">
<link rel="stylesheet" href="design-tokens-presets/mckinsey-consulting.css">
```

- **可用圖表**（v1.5 全數交付，共 8 種）：pie / bar (h+v) / kpi-card / gantt / waterfall / matrix / process-flow（位於 `scaffolds/charts/`）+ radar（位於 `scaffolds/radar_chart.mjs`，獨立於 charts/ 子目錄，供 Stage 6 量化評審使用）
- **API summary**（細節見 `scaffolds/charts/README.md`，10KB 完整文件）：
  - `PieChart({ data:[{label,value,color?}], size, showLegend, showPercent, valueFormat })`
  - `BarChart({ data, orientation:'v'|'h', width, height, max?, valueFormat, showValueLabels, padding })`
  - `KpiCard({ value, prefix, suffix, label, change?, changeDirection?, comparator? })`
  - `RadarChart({ data:[{axis,value}], size, levels, showValues })` — 5 維設計評審用
  - `GanttChart({ tasks:[{name,start,end,progress?,color?}], width, height })` — 專案時程
  - `WaterfallChart({ data:[{label,value,type?}], width, height })` — 增減分析
  - `MatrixChart({ rows, cols, data, cellRenderer? })` — 交叉比較矩陣
  - `ProcessFlow({ steps:[{label,description?,icon?}], direction })` — 流程步驟
- **Token 接線**：所有元件預設色取 `--chart-1..6`、文字色取 `--color-text*`、字級取 `--fs-body / --fs-caption`、間距取 `--space-1..3`、KPI 卡片取 `--kpi-card-*`，依附件 A 暖色 token 建 alias；不得沿用 charts.css 的異色色碼 fallback。
- **a11y 內建**：每個 chart 容器 `role="img" aria-label="…"` 描述完整 series 數值；SVG 用 `<title>` 提供 hover tooltip；KPI 卡片把 label + value + change 拼成 aria-label。
- **既有 case 替換**：既有 case 自寫 CSS-based `.bar-chart / .kpi-row / .scatter-svg` 等可保留 backward-compat；新增 chart 一律走 starter；漸進替換時可先在 case `:root` 加 alias 接 token（與 P6.8 一致）。
- **不適用 page mode**：page mode 字級會過大；page 內若需要小型 KPI 卡片可改用 `kpi-card--sm` size（自行擴充 class）。
- **反向驗證腳本**（每 case 推薦放）：`verify-charts.mjs` 必驗：
  1. starter scaffold export 都可被 import 到 case 內並產出非空 HTML
  2. demo case 的 chart container 都有正確 `role="img"` + non-empty `aria-label`
  3. SVG `<title>` element count ≥ data series count（pie / bar tooltip 完整）
  4. token 解析後值 = 預期值（避免漏載所選 preset CSS 退回 fallback 而不察覺）
  5. KPI 三方向（up / down / neutral）都各有實例 render
- **IV24(d) reverse-verify 範圍**：在 case 內透過 `verify/charts-demo.html` 反向驗證 starter scaffolds **可在 case CSS+token 環境中正確 render**（含 a11y / token 解析 / SVG tooltip）。**既有 case 已 ship 的內容（如 `.bar-chart` / `.kpi-row` / `.scatter-svg`）保留 backward-compat 不強制替換**（避免 regressing client 已交付視覺）；新增 chart 一律走 starter。這是 spec §24.10 + 「既有 case 替換策略」段的明文 deviation：「驗證可替換」非「強制替換已 ship 內容」。

#### Page mode 互動 prompt copy button 標準引用（v1.4-short §24.6 P6.5）

`page` mode 內若有「複製 prompt 到 clipboard」按鈕，**一律使用 starter 版本**：

```js
// 1) component template — 可重複呼叫產多顆按鈕
import { CopyButton } from '~/.claude/skills/starter-components/scaffolds/copy_button.mjs';
const html = `${CopyButton({ text: 'prompt 內容', label: '複製', successLabel: '✓ 已複製' })}`;

// 2) runtime singleton — 每頁只注入一次（layout 層）：
//    <link rel="stylesheet" href="copy_button.css">
//    <script src="copy_button.runtime.js" defer></script>
```

- **三檔分工**：`copy_button.mjs`（component template，純 HTML string）+ `copy_button.runtime.js`（runtime singleton，掃 `.copy-btn` 加 click listener）+ `copy_button.css`（基礎樣式，引 `--color-accent` token）
- **防 listener 重複綁定**：runtime 用 `dataset.bound='true'` flag 雙保險，即使 IIFE 重複執行也只綁一次
- **取文邏輯**：`data-text`（首選；spec 設計）優先；`data-target` 備援（v1.x backward-compat）
- **successLabel 走 dataset**：`data-success-label` 屬性，避免 string template 引號逃逸
- **禁止自寫 inline 版本**：page mode v1+ 不再允許每案重寫 `addEventListener('click', async () => navigator.clipboard.writeText(...))`

#### Page mode reading progress 標準引用（v1.4-short §24.8 P6.7）

`page` mode 的頁首閱讀進度條 **一律使用 starter 版本**：

```js
// 注入方式（page mode index.html 的 <body> 開頭）：
import { readingProgressHTML } from '~/.claude/skills/starter-components/scaffolds/reading_progress.mjs';
// `<body>${readingProgressHTML}<main>...</main></body>`
```

- **樣式**：3px 高、固定 top:0、`var(--color-accent, #0ea5e9)` 漸層；引 design-tokens-presets/* 任一 preset 即自動接 token；未引也有 fallback。
- **行為**：scroll + resize 觸發 `aria-valuenow` + `width` 同步；`@media print` 自動隱藏；passive event listener 不擋 scroll。
- **禁止自寫 inline 版本**：page mode v1+ 不再允許每案重寫 `.progress-bar` 樣式 / `window.addEventListener('scroll', ...)` 邏輯。
- **deck mode 不適用**：deck mode 的「目前第幾頁」進度條由 `deck_stage.js` 內建，不要混用本元件。

**輸出**：拷貝到 `<project_root>/components/starters/<scaffold-name>.{js,jsx}`

**Checkpoint**：列出複製清單 → 等 ✅ 繼續


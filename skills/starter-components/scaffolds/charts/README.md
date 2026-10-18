# scaffolds/charts/

Consulting-grade chart scaffolds for `deck` mode (1920×1080). Seven components:
`pie_chart.mjs` / `bar_chart.mjs` / `kpi_card.mjs` (v1.4) +
`gantt_chart.mjs` / `waterfall_chart.mjs` / `matrix_chart.mjs` / `process_flow.mjs` (v1.5)
+ a shared `charts.css` for base styles.

> Spec: fe-design v1.4-short §24.10 P6.9 (pie / bar / kpi) +
> fe-design v1.5 P7.12 (gantt / waterfall / matrix / process flow).

## Why these and not Chart.js / D3 / ECharts?

- **Zero runtime**: pure HTML string export. `deck.html` becomes self-contained
  on the wire — no script tag, no hydration, no flash-of-empty-chart.
- **Token-aware**: each chart pulls `--chart-1..6` and `--color-*` from
  `design-tokens-presets/mckinsey-consulting.css` (or any preset that
  defines these). Single design-token source = same look across deck/page.
- **Print-friendly**: SVG renders identically in `page.pdf()` viewport-matching
  pipeline (P6.4). `print-color-adjust: exact` keeps colors in PDF.
- **No external dep**: no `node_modules`, no CDN. Works on `file://` local
  preview and on any static host.

When you need brushing / cross-filter / 100k-point data → reach for ECharts
in the case-specific layer; do not extend these scaffolds.

## Component imports

```js
import { PieChart } from '~/.claude/skills/starter-components/scaffolds/charts/pie_chart.mjs';
import { BarChart } from '~/.claude/skills/starter-components/scaffolds/charts/bar_chart.mjs';
import { KpiCard } from '~/.claude/skills/starter-components/scaffolds/charts/kpi_card.mjs';
import { GanttChart } from '~/.claude/skills/starter-components/scaffolds/charts/gantt_chart.mjs';
import { WaterfallChart } from '~/.claude/skills/starter-components/scaffolds/charts/waterfall_chart.mjs';
import { MatrixChart } from '~/.claude/skills/starter-components/scaffolds/charts/matrix_chart.mjs';
import { ProcessFlow } from '~/.claude/skills/starter-components/scaffolds/charts/process_flow.mjs';
```

> **⚠️ 引用方式**：與 `design-tokens-presets/*` 一樣，`~` 路徑不可被 browser
> 直接解析。三種落地方式：(A) build/scaffold 階段 cp 到 case 內、(B) 把
> module 內容 inline 到 `<script type="module">` 區塊、(C) 本機開發 file://
> import。

## CSS（必載）

```html
<link rel="stylesheet" href="design-tokens-presets/mckinsey-consulting.css">
<link rel="stylesheet" href="scaffolds/charts/charts.css">
```

`charts.css` 為 self-contained 帶 fallback；單獨載入也可工作（套用通用 sans-
serif + 預設色），引 mckinsey-consulting.css 後自動接 token。

## API summary

### PieChart({ data, size, showLegend, showPercent, valueFormat })

| param | type | default | desc |
|---|---|---|---|
| `data` | `[{label, value, color?}]` | `[]` | 必填，slice 序列 |
| `size` | `number` (px) | `320` | SVG 直徑 |
| `showLegend` | `boolean` | `true` | 右側圖例 |
| `showPercent` | `boolean` | `true` | slice ≥ 5% 時印百分比 |
| `valueFormat` | `(v)=>string` | `(v)=>v` | tooltip + legend value 格式 |

每 slice 自動取 `--chart-1..6` 循環；可用 `color` prop 覆寫。`<title>` 提供
原生 hover tooltip。

### BarChart({ data, orientation, width, height, max, valueFormat, showValueLabels, padding })

| param | type | default | desc |
|---|---|---|---|
| `data` | `[{label, value, color?}]` | `[]` | 必填 |
| `orientation` | `'v'|'h'` | `'v'` | vertical / horizontal |
| `width`/`height` | `number` (px) | `480/320` | viewBox |
| `max` | `number` | auto from data | scale 上界 |
| `valueFormat` | `(v)=>string` | `(v)=>v` | bar value label + tooltip |
| `showValueLabels` | `boolean` | `true` | 在 bar 端印 value |
| `padding` | `{top,right,bottom,left}` | `{16,16,32,48}` | inner padding |

預設色 `--chart-1`；單根 bar 可用 `color` prop 強調（例：`var(--chart-2)`
emphasis 那一根）。

### KpiCard({ value, prefix, suffix, label, change, changeDirection, comparator, size })

| param | type | default | desc |
|---|---|---|---|
| `value` | `number|string` | — | 必填，主數字 |
| `prefix`/`suffix` | `string` | `''` | 例 `+` / `%` / `MB` |
| `label` | `string` | `''` | 數字下方說明 |
| `change` | `number` | `undefined` | 變化幅度（%）；省略則不印 |
| `changeDirection` | `'up'|'down'|'neutral'` | auto from change sign | 強制覆寫方向 |
| `comparator` | `string` | `undefined` | 例 `vs Q1` / `vs YoY` |
| `size` | `'sm'|'md'|'lg'` | `'md'` | 卡片尺寸（class hook，自行擴充） |

### GanttChart({ tasks, width, height, showToday, todayLabel })

| param | type | default | desc |
|---|---|---|---|
| `tasks` | `[{label, start, end, color?, progress?}]` | `[]` | 必填，task 序列；start/end 接受 ISO 字串、Date、epoch ms |
| `width` | `number` (px) | `720` | viewBox 寬 |
| `height` | `number` (px) | auto (row count) | viewBox 高，預設依 task 數量自動計算 |
| `showToday` | `boolean` | `false` | 顯示今日紅色虛線標記 |
| `todayLabel` | `string` | `'Today'` | 今日標記文字 |

每 task 自動取 `--chart-1..6` 循環；可用 `color` prop 覆寫。`progress`（0-1）
會在 bar 內繪製半透明進度條。今日標記僅在日期範圍內時顯示。

### WaterfallChart({ data, width, height, valueFormat })

| param | type | default | desc |
|---|---|---|---|
| `data` | `[{label, value, type?}]` | `[]` | 必填；type 可為 `'increase'`/`'decrease'`/`'total'`（省略則依 value 正負自動判定） |
| `width`/`height` | `number` (px) | `560/360` | viewBox |
| `valueFormat` | `(v)=>string` | `(v)=>v` | bar value label 格式 |

色彩對應：increase `--waterfall-increase`（綠）、decrease `--waterfall-decrease`（紅）、
total `--waterfall-total`（藍）。連接虛線串接前後 bar。

#### Total Bar 行為

`total` 型 bar 的行為與 increase/decrease 不同：

- **value prop 被忽略**：total bar 的高度由 running sum 決定，非 value prop
- **從 baseline 0 畫到 running sum**：視覺上代表「到這裡為止的累計值」
- **total 後可繼續累加**：total 不重置 running sum，後續 increase/decrease 繼續從原值累加
- **displayValue**：bar 頂端數字顯示 running sum（非 value prop）

**Data 設計模式**：

```js
WaterfallChart({ data: [
  { label: 'Q1 營收', value: 100 },           // 100（increase）
  { label: 'Q2 營收', value: -30 },            // 70（decrease）
  { label: 'H1 小計', value: 0, type: 'total' }, // 顯示 70（從 0 畫到 running sum）
  { label: 'Q3 營收', value: 50 },             // 120（繼續從 70 累加）
  { label: 'Q4 營收', value: 30 },             // 150
  { label: '全年合計', value: 0, type: 'total' }, // 顯示 150（從 0 畫到 running sum）
] })
```

常見用法：中間小計（H1/H2）+ 最終合計。value prop 設 0 即可（反正被忽略），
但建議語意清晰。

### MatrixChart({ cells, rowLabels, colLabels, width, height })

| param | type | default | desc |
|---|---|---|---|
| `cells` | `[{row, col, label, value?, color?}]` | `[]` | 格子資料；row/col 為 0-based index |
| `rowLabels` | `string[]` | `[]` | 必填，列標題 |
| `colLabels` | `string[]` | `[]` | 必填，欄標題 |
| `width` | `number` (px) | `480` | viewBox 寬 |
| `height` | `number` (px) | auto (row count) | viewBox 高 |

常見用途：BCG 矩陣、SWOT、優先序矩陣。每格背景色預設取 `--chart-1..4` 循環
（低透明度），可用 `color` prop 覆寫。未填入的格位渲染為空白。

### ProcessFlow({ steps, direction, width })

| param | type | default | desc |
|---|---|---|---|
| `steps` | `[{label, description?, icon?, status?}]` | `[]` | 必填；status 為 `'done'`/`'active'`/`'pending'`（預設 `'pending'`） |
| `direction` | `'horizontal'`/`'vertical'` | `'horizontal'` | 排列方向 |
| `width` | `number` (px) | auto (step count) | viewBox 寬 |

done=實心圓（勾號）、active=脈動圓（CSS 動畫）、pending=空心圓。箭頭三角連接
相鄰步驟。色彩：done `--process-done`、active `--process-active`、pending
`--process-pending`。脈動動畫在 `prefers-reduced-motion: reduce` 時自動停用。

## Token references

所有 chart 引用 mckinsey-consulting.css 提供的 token：

| Token | Used by | Fallback |
|---|---|---|
| `--chart-1..6` | pie / bar 預設色 | navy / orange / slate / dark accent / mid navy / gray |
| `--color-bg` | pie slice stroke (separator) | `#ffffff` |
| `--color-text` / `--color-text-muted` / `--color-text-faint` | label / axis / value | navy / muted / faint |
| `--color-divider` | bar axis line | `#e5e7eb` |
| `--font-body` | 所有文字 | system-ui sans |
| `--fs-body` / `--fs-caption` | label / axis | 16px / 12px |
| `--space-1..3` | gap / padding | 8 / 16 / 24 px |
| `--kpi-card-bg/-border/-radius/-fs/-fw` | KpiCard | self-defined |
| `--color-success/-danger` | KpiCard up/down change | green / red |
| `--gantt-today` | GanttChart today marker | `--color-danger` / `#b91c1c` |
| `--waterfall-increase` | WaterfallChart positive bar | `--chart-3` / `#15803d` |
| `--waterfall-decrease` | WaterfallChart negative bar | `--chart-6` / `#b91c1c` |
| `--waterfall-total` | WaterfallChart total bar | `--chart-1` / `#003366` |
| `--process-done` | ProcessFlow done node | `--chart-3` / `#15803d` |
| `--process-active` | ProcessFlow active node | `--chart-1` / `#003366` |
| `--process-pending` | ProcessFlow pending node | `--color-text-muted` / `#4a5568` |

## v1.5 新增（P7.12）

以下 4 個 chart 已於 v1.5 實作完成：

- `gantt_chart.mjs` — 甘特圖（時程橫條圖，含 today marker + progress bar）
- `waterfall_chart.mjs` — 瀑布圖（累計變化正負分色 + 連接虛線）
- `matrix_chart.mjs` — 矩陣圖（NxN 網格，BCG / SWOT / 優先序）
- `process_flow.mjs` — 流程圖（步驟 + 箭頭，done/active/pending 三態）

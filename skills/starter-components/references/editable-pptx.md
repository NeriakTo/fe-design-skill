# 語義級 PPTX 導出 — HTML 硬約束與翻譯策略

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。
> 版本：v1.5 P7.1a（fe-design 能力對齊）
> 適用工具：`tools/html2pptx.mjs`

---

## 概述

`html2pptx.mjs` 將 HTML slide deck 翻譯為可編輯文字框的 PowerPoint（.pptx），使客戶可在 PowerPoint / LibreOffice Impress 中直接雙擊編輯文字。翻譯器透過 Playwright 讀取 DOM computedStyle，逐元素映射到 pptxgenjs API。

不可翻譯的元素（CSS gradient / canvas / complex SVG / CSS filter）自動退回 element-level Playwright 截圖 fallback，以圖片嵌入。

---

## 7 條 HTML 硬約束

以下約束適用於所有需要 PPTX 語義導出的 HTML slide。違反不會導致翻譯器崩潰（有 fallback），但會降低 semantic 率。

### 約束 1：畫布尺寸維持 1920×1080px

HTML deck 繼續以 1920×1080px 渲染（`deck_stage.js` / `pdf-export.mjs` 現有行為不變）。

翻譯器（`html2pptx.mjs`）內部做座標轉換：
- pptxgenjs `LAYOUT_WIDE` = 13.333″ × 7.5″ = 960pt × 540pt
- HTML 1920px 映射到 13.333″ → 有效 DPI = 144（1920 / 13.333）
- 座標換算：`inch = html_px / 144`（等價於 `(html_px / 1.5) / 96`）
- 字級換算：`font_pt = html_font_px / 2`（144 dpi ÷ 72 pt/in = 2）
- 容差：±0.05″（= 7.2px @1920 viewport）

**注意**：座標和字級的除數不同——座標除以 144 得 inch，字級除以 2 得 pt。

### 約束 2：避免 CSS transform 做排版（v1.6 P8.2 自動 fallback）

pptxgenjs 不支援 `transform: translate/rotate/scale` 的佈局推導。v1.6 翻譯器會自動偵測 transform 元素並做適當處理：

- **文字 + transform** → 仍走 `addText()`（位置用 getBoundingClientRect，可接受微小偏移）
- **非文字 + transform** → 自動用 Playwright `element.screenshot()` 取代手動 clip 裁切（v1.6 P8.2）
- **建議**：排版仍優先用 `position: absolute` / `flexbox` / `grid`，避免 transform 以獲得最佳語義率
- **不再嚴格禁止**：transform 元素不會破壞翻譯器，但會計入 fallback（降低 semantic_ratio）

### 約束 3：文字必須在可識別的 DOM 節點

- 禁止：`::before` / `::after` 的 `content` 屬性放實質文字（pptxgenjs 讀不到 pseudo-element）
- 禁止：SVG `<text>` 作為主要文字載體（退回圖片模式）
- 允許：`<h1-h6>` / `<p>` / `<span>` / `<li>` / `<div>` 內的 text node

### 約束 4：圖片必須是 `<img>` 或 CSS `background-image`

- 禁止：`<canvas>` 繪製（pptxgenjs 無法提取 canvas 像素）→ 退回截圖 fallback
- 允許：`<img src="...">` / `background-image: url(...)` → `addImage()`
- SVG inline 圖示：退回 element-level 截圖 fallback

### 約束 5：禁用 CSS gradient + backdrop-filter + CSS filter

pptxgenjs `addShape()` 的 `ShapeFillProps.type` 僅支援 `'none' | 'solid'`，**完全不支援任何漸層填充**（含 linear/radial/conic gradient）。

- `linear-gradient` / `radial-gradient` / `conic-gradient` → element-level 截圖 fallback
- `backdrop-filter` / `filter` → 視覺效果遺失（標註於 per_slide_stats，不阻斷）
- `box-shadow` → 遺失（不阻斷）。若客戶要求 box-shadow 視覺一致，建議使用截圖模式 `--pptx-mode image`。
- `border` → v1.6 P8.4 支援四邊等寬 border 映射到 pptxgenjs `line` 屬性（solid/dashed/dotted）。`border-radius` 映射到 `roundRect` shape 的 `rectRadius`（0.0-1.0 ratio）。非等寬四邊 border 靜默忽略。

### 約束 6：z-index 遍歷順序

pptxgenjs 元素層級由 `addText` / `addImage` / `addShape` 呼叫順序決定，非 z-index 屬性。

翻譯器按 **computed stacking context** 順序遍歷 DOM（v1.6 P8.1 實作完成）：
1. 建構 stacking context 樹（觸發新 context 的條件：`position` 非 static + z-index 非 auto、`opacity < 1`、`transform` 非 none、`filter` 非 none、`isolation: isolate`、`will-change: transform/opacity`、`mix-blend-mode` 非 normal）
2. 每個 context 內按 z-index 排序（negative z-index 先於 parent 繪製，non-negative 後繪製）
3. DFS 遍歷整棵樹決定呼叫順序
4. `opacity === 0` 的元素在 SC 建構前即跳過整個子樹

**禁止 flat sort by z-index**——嵌套在 stacking context parent 下的元素層級關係會被破壞。

### 約束 7：CJK 字體 fallback 策略

pptxgenjs `addText()` 的 `fontFace` 同時寫入 `<a:latin>` / `<a:ea>` / `<a:cs>` 三標籤。theme XML 的 `<a:font script="Hant">` 硬編碼於 pptxgenjs 原始碼，無 API 可覆寫。**不依賴 slide master fallback**。

策略：翻譯器提供 fontFace 映射表，在翻譯階段做替換。

**預設映射表**：

| HTML fontFamily（CSS stack 第一項） | PPTX fontFace |
|---|---|
| Noto Sans TC | 微軟正黑體 |
| Noto Serif TC | 新細明體 |
| Source Serif 4 | Times New Roman |
| Inter | Calibri |
| system-ui | Calibri |

映射邏輯：
1. 解析 `computedStyle.fontFamily`（CSS stack，以逗號分隔）
2. 取第一項，去除引號與空白
3. 查映射表 → 命中則替換
4. 未命中 → 原樣保留（PPTX 端 fallback 至系統字體）

可透過 `--font-map <json>` 旗標覆寫預設映射表。

**交付提醒**：若客戶需精確字體一致，建議安裝 Noto Sans TC；否則預設使用微軟正黑體確保可讀性。

---

## 畫布尺寸銜接策略

| 層級 | 尺寸 | 單位 |
|---|---|---|
| HTML viewport | 1920 × 1080 | px |
| pptxgenjs LAYOUT_WIDE | 13.333 × 7.5 | inch（= 960 × 540 pt） |
| scaleFactor | 1.5 | px/px_pptx |

**換算公式**：

```
pptx_inch_x = html_px_x / 144
pptx_inch_y = html_px_y / 144
pptx_inch_w = html_px_w / 144
pptx_inch_h = html_px_h / 144
font_pt     = html_font_px / 2
```

座標：px ÷ 144（有效 DPI）= inch
字級：px ÷ 2（DPI 144 ÷ pt/in 72）= pt

---

## 元素決策樹

翻譯器對每個可見 DOM 元素依以下規則決定輸出方式：

```
元素有直接 text node + solid background + 無 positioned children？
  → addText({ fill: { color, type: 'solid' } })（合併為單一物件）

元素僅有 solid background（無文字）？
  → addShape({ fill: { color, type: 'solid' } })

元素有 gradient / filter / backdrop-filter background？
  → element-level Playwright 截圖 → addImage()

元素是 <img>？
  → Playwright element 截圖 → addImage()

元素是 <canvas> / complex SVG？
  → element-level Playwright 截圖 → addImage()

元素有文字 + gradient background？
  → 背景：element-level 截圖 → addImage()
  → 文字：addText()（疊在截圖上方）

其他文字元素（無 background 或 transparent）？
  → addText()
```

**核心文字保護規則**：`h1-h6` / `p` / `ul` / `ol` / `li` / `span`（含直接 text node）**永遠不得整體退回截圖 fallback**。若背景需要 fallback，文字部分仍必須用 `addText()` 輸出。違反此規則即違反 IV26(c) 核心文字 100% semantic 門檻。

---

## per_slide_stats 計數規則

| 輸出方式 | 計為 |
|---|---|
| `addText()`（含帶 fill 的合併版） | 1 semantic element |
| `addShape()`（solid fill） | 1 semantic element |
| `addImage()`（來自 `<img>` 標籤） | 1 semantic element |
| `addImage()`（來自截圖 fallback） | 1 fallback element |
| 背景截圖 + 文字 addText 合成 | 1 fallback + 1 semantic |

**semantic 率** = `semantic_elements / (semantic_elements + fallback_elements)`

IV26(c) 門檻：
- 核心文字（h1-h6/p/ul/ol/li）：100% semantic（零 fallback）
- 整頁 semantic 率：≥ 60%

---

## 降級路徑

| 層級 | 觸發條件 | 行為 |
|---|---|---|
| element-level | 單一元素不支援（gradient/canvas/SVG/filter） | 對該元素做 Playwright 截圖 → `addImage()` |
| slide-level | 整頁翻譯拋出未預期錯誤 | 退回全頁截圖（現有 image-based 行為） |
| deck-level | pptxgenjs 初始化失敗 / 無法 writeFile | 退回 `--pptx-mode image` 全截圖模式 |

降級事件記錄於 `build-metadata.json` 的 `per_slide_stats`。

---

## 常見錯誤與排除

| 症狀 | 原因 | 解法 |
|---|---|---|
| PPTX 文字框位置偏移 | scaleFactor 換算遺漏 | 確認所有座標都除以 1.5 再除以 96 |
| 文字亂碼 / 方塊 | fontFace 指定的字體收件方未安裝 | 使用映射表指定高安裝率字體（微軟正黑體）|
| 漸層背景變成純色 | pptxgenjs 不支援 gradient fill | 預期行為——改走截圖 fallback |
| 元素層疊順序錯亂 | 未按 stacking context DFS 遍歷 | 確認建構 SC 樹而非 flat sort |
| 截圖 fallback 圖片裁切不準 | `getBoundingClientRect()` 在 transform 元素上的座標偏移 | v1.6 P8.2 已自動處理：transform 非文字元素自動改用 `element.screenshot()` |
| deck-standalone.html 翻譯卡死 | base64 inline 字型阻塞 AST parser | 必須使用 `deck.html`（非 standalone）作為輸入 |
| 字級偏大/偏小 | 座標與字級除數混用 | `fontSize_pt = computedStyle.fontSize_px / 2`（非 /1.5） |

---

## build-metadata.json PPTX 欄位 schema

```json
{
  "pptx": {
    "path": "delivery/deck.pptx",
    "mode": "semantic",
    "text_editable": true,
    "layout": "LAYOUT_WIDE",
    "layout_size_pt": { "width": 960, "height": 540 },
    "pptxgenjs_version": "4.0.1",
    "font_map": {
      "Noto Sans TC": "微軟正黑體",
      "Noto Serif TC": "新細明體"
    },
    "per_slide_stats": [
      {
        "slide": 1,
        "semantic_elements": 12,
        "fallback_elements": 1,
        "semantic_ratio": 0.923,
        "core_text_semantic": true,
        "stacking_contexts_count": 3,
        "max_nesting_depth": 2,
        "transform_elements": 1,
        "transform_screenshot_fallbacks": 1,
        "rich_text_elements": 5,
        "total_inline_runs": 18,
        "bordered_elements": 4,
        "border_mapped": 3,
        "border_skipped_asymmetric": 1
      }
    ]
  }
}
```

v1.6 新增欄位說明：
- `stacking_contexts_count` — P8.1：slide 內 stacking context 數量
- `max_nesting_depth` — P8.1：最大 SC 巢狀深度
- `transform_elements` — P8.2：含 CSS transform 的元素數
- `transform_screenshot_fallbacks` — P8.2：透過 element.screenshot() 處理的 transform 元素數
- `rich_text_elements` — P8.3：使用 rich text array 輸出的文字元素數
- `total_inline_runs` — P8.3：所有 rich text 元素的 inline run 總數
- `bordered_elements` — P8.4：帶 border 的元素數
- `border_mapped` — P8.4：成功映射到 pptxgenjs line 的 border 數
- `border_skipped_asymmetric` — P8.4：因四邊不等寬而跳過的 border 數

`mode` 為 `"semantic"` 時 `text_editable` 必為 `true`；`mode` 為 `"image-based"` 時 `text_editable` 為 `false`。

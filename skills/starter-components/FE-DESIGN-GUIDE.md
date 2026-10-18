# fe-design 功能說明文件

> 版本：v1.7 | 最後更新：2026-05-24 | 維護者：Kevin Du

## 目錄

1. [概述](#概述)
2. [快速開始](#快速開始)
3. [使用方式](#使用方式)
4. [7 階段 Pipeline](#7-階段-pipeline)
5. [輸出格式](#輸出格式)
6. [運作原理](#運作原理)
7. [技能生態系](#技能生態系)
8. [品質保證](#品質保證)
9. [版本歷程](#版本歷程)
10. [常見問題](#常見問題)

---

## 概述

fe-design 是一套完整的前端設計自動化技能（Skill），透過一句話指令啟動 7 階段 pipeline，從需求澄清到最終交付，覆蓋設計系統建立、HTML 實作、品質檢核、多格式匯出全鏈路。

### 規模

| 類別 | 數量 | 程式碼行數 |
|------|------|-----------|
| Orchestrator | 1 檔 | 1,060 行 |
| 工具（tools/） | 10 支 | 3,287 行 |
| 骨架元件（scaffolds/） | 15 個 | 2,791 行 |
| 圖表元件（charts/） | 7 種 + CSS | 1,233 行 |
| 品牌模板（starters/） | 6 套 | 1,883 行 |
| 品質規則（craft/） | 5 檔 | 345 行 |
| 參考文件（references/） | 10 份 | 1,684 行 |
| Token 預設（design-tokens-presets/） | 5 套 | 281 行 |
| Anti-slop 掃描器 | 3 檔 | 1,291 行 |
| 測試 | 見 `bash tools/verify.sh` | — |
| **合計** | **91 檔** | **~15,000 行** |

---

## 快速開始

最短路徑：一句話啟動完整 pipeline。

```bash
# 做一份客戶啟動會議簡報
/fe-design deck "客戶 Q3 啟動會議"

# 做一個課程介紹 landing page
/fe-design page "AI 轉型課程 landing"

# 不確定要什麼？全互動引導
/fe-design
```

pipeline 會自動走完 7 階段（澄清→風格→設計系統→骨架→實作→品質→交付），每階段停下等你確認。最終產出在 `delivery/` 目錄。

---

## 使用方式

### 基本語法

```
/fe-design [mode] [brief] [flags]
/fe-design --resume
```

### 範例

```bash
# 完整參數 — 直接進入 pipeline
/fe-design deck "客戶啟動會議簡報"

# 指定 mode，互動澄清 brief
/fe-design page "課程 landing page"

# 全互動 — 先選 mode 再問 brief
/fe-design

# 從中斷點恢復
/fe-design --resume

# 強制走完整設計諮詢（非 shortcut）
/fe-design app "管理後台" --full-design-consultation
```

### 五種 Mode

| Mode | 用途 | 產出物 |
|------|------|--------|
| `deck` | 簡報投影片 | HTML + PDF + PPTX + MP4 + standalone HTML |
| `page` | 單頁網站 / Landing page | HTML + 雙 PDF（A4 + viewport）+ standalone HTML |
| `app` | 應用程式 UI | 元件目錄（components/）+ 整合指南 |
| `system` | 設計系統 | DESIGN.md + design_tokens.json + Tailwind config |
| `migrate` | 設計遷移 | 遷移計畫 + diff patches |

### 可用旗標

| 旗標 | 預設值 | 說明 |
|------|--------|------|
| `--async-timeout <分鐘>` | 5 | 訊息通道 async 模式下 checkpoint 等待時間 |
| `--async-default <行為>` | accept | timeout 後行為：accept / skip / abort |
| `--full-design-consultation` | off | 強制走完整 6-Phase 設計諮詢 |
| `--shortcut` | off | system mode 強制走主腦快速寫（含 warning） |

---

## 7 階段 Pipeline

### 流程概覽

```
Stage 0 → [1/7] → [2/7] → [3/7] → C1 → [4/7] → [5/7] → [6/7] → C2 → [7/7]
意圖判定   澄清    風格    設計系統  壓縮   骨架    實作    品質檢核  壓縮   交付
```

### Stage 0 — 意圖判定

使用者未指定 mode 時，自動分析 brief 文字和專案結構推斷最可能的 mode。

- **匹配方式**：token-level 比對，最長匹配優先
- **計分**：每命中關鍵詞 +0.3（上限 0.9），專案結構加權 ×1.2
- **信心閾值**：≥ 0.7 推薦推斷結果，< 0.7 退回手動選擇
- **安全閥**：推斷不跳過 Stage 1 澄清；兩 mode 分數差距 < 0.1 強制問使用者

### [1/7] 澄清

收集需求細節：用途、受眾、品牌參考、輸出格式、時程。

- **字體配對方案**（4 種）：A 西方 consulting / B 全黑體 + 字重對比 / C 全明體 / D 全黑體 + 不同字族
- **品牌資產觸發**：brief 涉及具體品牌時，啟動 5 步品牌資產協議（問→搜→下載→驗證→固化 brand-spec.md）

### [2/7] 風格定位

從 20 種設計哲學 × 5 流派中推薦 3 個差異化方向。

- 場景模板推薦：deck 10 種 / page 7 種 / app 5 種
- 設計方向顧問 Fallback：brief 模糊時啟動互動式設計諮詢

### [3/7] 設計系統

產出 DESIGN.md（Google design.md 格式 + 9 section schema）。

- **mode-conditional 路徑**：
  - deck / page / app → shortcut（主腦快速寫），仍需通過 lint + 9-section 驗證
  - system → 完整 design-consultation 6-Phase
  - migrate → design-system audit mode
- **Content Fidelity Lock**（deck/page mode）：Sources 段 + Facts 表格 + fact-check.mjs 交叉驗證
- **Craft Rules 動態注入**：依 DESIGN.md 的 `craft.requires` 欄位載入品質規則模組

### C1 — Context 壓縮

Stage 1-3 摘要壓縮為 ≤ 500 字，寫入 `.checkpoints/1-to-3.md`，釋放約 30k tokens。

### [4/7] 骨架初始化

依 mode 拷貝對應 scaffold 到專案目錄。

| Mode | 骨架元件 |
|------|---------|
| deck | `deck_stage.js`（單檔 ≤10 頁）或 `deck_index.html`（多檔 ≥10 頁）|
| page | `browser_window.jsx` + `reading_progress.mjs` + `copy_button.mjs` |
| app | `design_canvas.jsx` + 裝置外框（iOS / Android / macOS）+ `app_phone.jsx` |
| system / migrate | 跳過 |

### [5/7] 實作

依 mode 呼叫主力 skill 產出實際程式碼。

- **Junior Designer 雙階段**：新品牌首次合作時，先出假設 + placeholder 版本給使用者確認方向，再做正式版
- **Tweaks 即時變體**：每案預設加 2-3 個配色/字級/密度 tweaks
- **真圖優先**：禁止在正式交付物使用 placeholder 圖片
- **app mode 子組件拆分**：單一元件超過 300 行時提議拆分

### [6/7] 品質檢核

三層自動掃描 + 互動設計審查。

#### 三層 Anti-slop 掃描器

| 層 | 來源 | 規則數 | 工具 |
|----|------|--------|------|
| 第一層 | Google design.md lint | 8 條結構規則 | `npx @google/design.md@0.1.1 lint`（含 vendored fallback） |
| 第二層 | 自家 trope catalog | 19 條繁中 trope | `scan.py`（regex + heuristic） |
| 第三層 | 7 sins P0 硬擋 | 7 條 CSS token-aware | `scan.py scan_seven_sins()`（依賴 `token_resolver.py`） |

#### 7 sins 明細

| Sin | 名稱 | 偵測方式 |
|-----|------|---------|
| 1 | Tailwind Indigo | CSS token-aware：偵測 7 色 indigo 在非 :root 區域使用 |
| 2 | Trust Gradient | 偵測 purple→blue / blue→cyan / indigo→pink 兩色漸層 |
| 3 | Emoji as Icon | 偵測 emoji 出現在 heading / button / li / icon 元素內 |
| 4 | Font Conflict | CSS token-aware：--font-display 為 serif 但 h1/h2 用 sans-serif |
| 5 | Rounded Left Border | 偵測 border-radius + border-left 同時出現 |
| 6 | Invented Metric | 偵測無來源的「Nx faster/better」宣稱 |
| 7 | Filler Copy | 偵測 lorem ipsum / placeholder text / feature one 等填充文案 |

#### 量化評審（可選）

5 維度雷達圖評分：哲學一致性 20% / 視覺層級 25% / 細節執行 25% / 功能性 20% / 創新性 10%。

### C2 — Context 壓縮

Stage 4-6 摘要壓縮為 ≤ 800 字，釋放約 50k tokens。

### [7/7] 驗證與交付

多格式匯出 + 自動化驗證。

---

## 輸出格式

### deck mode 交付物

```
delivery/
  deck.html              # 主 HTML（Playwright 驗證用）
  deck-standalone.html    # 零外部依賴封裝版（離線開啟）
  deck.pdf               # viewport-matching PDF（1920×1080）
  deck.pptx              # 語義級翻譯 PPTX（文字可編輯）
  deck.mp4               # HyperFrames 影片（條件觸發）
  build-metadata.json     # 建置 metadata
```

### page mode 交付物

```
delivery/
  page.html              # 主 HTML
  page-standalone.html    # standalone 版
  page-a4.pdf            # A4 portrait（列印閱讀）
  page-viewport.pdf      # viewport 截圖版
  build-metadata.json
```

### app mode 交付物

```
delivery/
  components/
    index.tsx            # 入口元件
    Header.tsx           # 子元件
    Sidebar.tsx          # 子元件
    *.types.ts           # 型別定義
  integration-guide.md   # 整合指南
  build-metadata.json
```

### system mode 交付物

```
delivery/
  .design/
    DESIGN.md               # Google design.md 格式（9 section）
    design_tokens.json       # DTCG 格式 token
    tailwind.theme.extend.js # Tailwind 設定
  build-metadata.json
```

### migrate mode 交付物

```
delivery/
  migration-plan.md      # 遷移計畫
  patches/
    001-colors.diff      # 差異 patch
    002-typography.diff
  build-metadata.json
```

### build-metadata.json

每次 pipeline 完成都會產出 metadata 檔案，紀錄建置參數和品質結果。涵蓋欄位：

- `brief` / `mode` / `build_timestamp` / `scaffolds`
- `deck` viewport 設定 / `pdf` 格式與頁數
- `pptx` 語義翻譯統計（semantic_ratio / per_slide_stats）
- `mp4` 引擎與參數（HyperFrames 版本 / duration / fps）
- `fidelity_lock` 事實層驗證結果（deck/page mode）
- `lint_warnings_unresolved` / `async_timeout_advances`

---

## 運作原理

### 架構

```
fe-design.md（Orchestrator, 1060 行）
  │
  ├── Stage 0: 意圖判定（內建關鍵詞比對 + 專案結構偵測）
  ├── Stage 1-2: 需求收集（AskUserQuestion 互動 / async timeout 推進）
  ├── Stage 3: 設計系統（呼叫 design-consultation skill 或 shortcut）
  │     └── craft/ 品質規則動態注入
  ├── Stage 4: 骨架（從 scaffolds/ 拷貝元件）
  ├── Stage 5: 實作（呼叫 frontend-slides / frontend-design skill）
  ├── Stage 6: 品質（呼叫 anti-slop-review 三層掃描）
  │     ├── scan.py → 第一層 Google lint + 第二層 19 trope + 第三層 7 sins
  │     └── token_resolver.py → CSS var() 4 層解析（供 sin 1 + sin 4）
  └── Stage 7: 交付（呼叫 tools/ 工具鏈）
        ├── html2pptx.mjs → HTML→PPTX 語義翻譯
        ├── html2video.mjs → HTML→MP4（HyperFrames + FFmpeg 退化）
        ├── pdf-export.mjs → HTML→PDF（Playwright）
        ├── standalone-export.mjs → 零依賴 HTML 封裝
        ├── fact-check.mjs → 事實層交叉驗證
        └── visual-diff.mjs → 多版視覺比較
```

### 雙模式運行

| 特性 | sync 模式（TTY） | async 模式（訊息通道） |
|------|------------------|----------------------|
| checkpoint | 等使用者回覆 | 5 分鐘 timeout 自動推進 |
| 多選題 timeout | 等到回覆 | 取第一個選項 |
| 連續 3 次 timeout | 不適用 | 自動暫停（安全閥） |
| 30 分鐘無回覆 | 存 draft + memory | 不適用（由 timeout 接管） |

### Context 管理

pipeline 在 Stage 3 和 Stage 6 後各執行一次 Context 壓縮（C1 / C2），將前序階段摘要為精簡 checkpoint 檔案，釋放 working memory。

| 節點 | 壓縮量 | 累積 context |
|------|--------|-------------|
| Stage 1-3 完成 | ~50k | 50k |
| C1 壓縮後 | -30k | 20k |
| Stage 4-6 完成 | +60k | 80k |
| C2 壓縮後 | -50k | 30k |
| Stage 7 完成 | +30k | 60k |

目標：pipeline 結束時 session < 80k tokens。

### 中斷恢復

```
/fe-design --resume
```

讀取 `.checkpoints/1-to-3.md` 和 `.checkpoints/4-to-6.md` 恢復決策上下文，從最後一個未完成 stage 繼續。

### 關鍵保護機制

#### Case 目錄隔離

當 `<project_root>` 偵測為共享工作目錄（多個案子共用的工作目錄），pipeline 主動建議在子目錄做 `git init` 隔離，避免 `.checkpoints/` 和 `delivery/` 等中間檔汙染共享目錄。推薦結構：`<共用工作目錄>/design-cases/<case-name>/`。

#### 管線輸入隔離

`deck-standalone.html`（含 inline base64 字型，可達 45 MB）僅作最終離線交付物，不可作為下游處理的中繼輸入。所有工具步驟（Playwright 測試、PDF 產出、PPTX 翻譯、MP4 轉換）一律使用 `delivery/deck.html`（60 KB 級）作為輸入，避免效能問題。

#### Lint 自動修復斷路器

Stage 3 的 anti-slop lint 可能需要迭代修補 warning。為避免無限迴圈：對單一 warning 最多嘗試自動修復 3 次。超過 3 次仍失敗則停止、保留 warning、轉交人類決定。C1 摘要必須包含「未解 warning 數」欄位（即使為 0）。

#### Action Title 金字塔原則（deck consulting mode）

deck mode 採 consulting-style 時，每張內容投影片頂端必須有 action title — 一句結論性句子（≤ 18 個 CJK 字），不是名詞性標題。例：「2026 Q2 營收成長 30% 來自三大新品線」而非「2026 Q2 營收概況」。DESIGN.md frontmatter 加 `slide_action_titles[]` YAML 陣列逐張對應，`verify-action-titles.mjs` 做反向驗證。

---

## 技能生態系

### 工具鏈（tools/）

| 工具 | 行數 | 功能 | 依賴 |
|------|------|------|------|
| html2pptx.mjs | 447 | HTML→PPTX 語義翻譯主程式 | pptxgenjs |
| html2pptx-extract.mjs | 252 | PPTX helper：DOM 元素提取 | — |
| html2pptx-render.mjs | 127 | PPTX helper：slide 渲染 | — |
| export-deck-pptx.mjs | 223 | PPTX 導出 pipeline wrapper | Playwright |
| html2video.mjs | 362 | HTML→MP4 影片轉換 | HyperFrames / FFmpeg |
| pdf-export.mjs | 168 | HTML→PDF（viewport / A4） | Playwright |
| standalone-export.mjs | 318 | 零外部依賴 HTML 封裝 | — |
| fonts-inline.mjs | 286 | Google Fonts woff2 inline | — |
| fact-check.mjs | 548 | 事實層交叉驗證（LLM Part A+B） | Gemini CLI / Codex CLI |
| visual-diff.mjs | 556 | 多版 side-by-side 視覺比較 | Playwright / pixelmatch |

### 骨架元件（scaffolds/）

| 元件 | 行數 | 適用 mode |
|------|------|----------|
| deck_stage.js | 455 | deck（單檔 ≤10 頁） |
| deck_index.html | — | deck（多檔 ≥10 頁） |
| browser_window.jsx | 280 | page |
| copy_button.mjs + .runtime.js + .css | 227 | page |
| reading_progress.mjs | 67 | page |
| design_canvas.jsx | 258 | app |
| app_phone.jsx | 166 | app |
| ios_frame.jsx | 198 | app |
| android_frame.jsx | 235 | app |
| macos_window.jsx | 159 | app |
| animations.jsx | 209 | 共用 |
| tweaks_panel.mjs | 210 | 共用 |
| radar_chart.mjs | 106 | Stage 6 量化評審 |

### 圖表元件

7 種位於 `scaffolds/charts/` + 1 種位於 `scaffolds/`（radar），全部接 design token（`--chart-1..6`）：

| 元件 | API 簽章 |
|------|---------|
| PieChart | `PieChart({ data, size, showLegend, showPercent, valueFormat })` |
| BarChart | `BarChart({ data, orientation, width, height, max, valueFormat })` |
| KpiCard | `KpiCard({ value, prefix, suffix, label, change, comparator })` |
| GanttChart | `GanttChart({ tasks, width, height })` |
| WaterfallChart | `WaterfallChart({ data, width, height })` |
| MatrixChart | `MatrixChart({ rows, cols, data, cellRenderer })` |
| ProcessFlow | `ProcessFlow({ steps, direction })` |
| RadarChart | `RadarChart({ data, size, levels, showValues })` |

### 品牌模板（starters/）

6 套預建 DESIGN.md，每套符合 9-section schema：

| 模板 | 風格 | 行數 | 適用場景 |
|------|------|------|---------|
| consulting-professional | 白底黑體 McKinsey 風 | 272 | 企業顧問簡報 |
| corporate-warm | 暖米底地產商務風 | 312 | 物業 / 不動產 |
| tech-dark | 深色科技 Linear/Vercel 風 | 339 | 科技產品 / SaaS |
| editorial-minimal | 白底明體年報學術風 | 300 | 報告 / 白皮書 |
| chenxi-liuli | 晨曦琉璃（深色） | 327 | 通用 |
| chenxi-liuli-light | 晨曦琉璃（淺色） | 333 | 通用淺色 |

### Craft Rules（品質規則模組）

透過 DESIGN.md 的 `craft.requires` 宣告式引用：

| 模組 | 內容 |
|------|------|
| anti-ai-slop | 7 sins 延伸規則 + AI 生成痕跡偵測 |
| typography | 字體配對紀律 + CJK fallback stack |
| color | 對比度門檻（WCAG AA）+ palette 數量限制 |
| motion | 動畫時長上限 + easing 函數規範 |

### Design Token Presets

5 套 CSS custom property 預設，可直接 `<link>` 引入：

| Preset | 字體策略 |
|--------|---------|
| consulting-mono-sans | 全黑體 + 字重對比（預設首選） |
| editorial-serif | 全明體 + 字重對比 |
| mixed-bilingual | 明體標題 + 黑體內文（僅英文受眾） |
| premium-mixed-sans | 全黑體 + 不同字族 |
| mckinsey-consulting | McKinsey 風 token（含圖表色板 chart-1..6） |

---

## 品質保證

### 測試覆蓋

| 測試檔 | 測試數 | 覆蓋範圍 |
|--------|--------|---------|
| anti-slop-review/test_scan.py | 135 | anti-slop 三層掃描 + token resolver（pytest） |
| demo-structure.mjs | 45 | 3 個 demo HTML 結構不變式（Node.js assert） |
| tools-cli.mjs | 26 | pdf-export / standalone / html2video CLI 介面（subprocess） |
| regression.mjs | 1 | html2pptx PPTX 輸出 stats 比對（baseline JSON） |
| **其他** | — | 簡報關卡、設計脈絡匯入與倉庫檢查工具的測試；完整清單與最新數字以 `bash tools/verify.sh` 輸出為準 |

### 失敗處理

每個外部 skill 依賴都有明確降級行為：

| Skill | 降級方式 |
|-------|---------|
| design-review | 純 anti-slop 三層掃描 + 人工確認 |
| design-consultation | shortcut 路徑（主腦快速寫 DESIGN.md） |
| awesome-design-md | 永久可選，跳過參考比對 |
| frontend-slides / frontend-design | 主腦直接寫 HTML/components |

npx 外部依賴有 vendored tarball fallback（308KB），html2video 有 Playwright + FFmpeg 退化方案。

---

## 版本歷程

| 版本 | 日期 | 重點 |
|------|------|------|
| v1.0 | 2026-04 | 基礎 7 階段 pipeline |
| v1.1 | 2026-04 | scaffold 元件庫建立 |
| v1.2 | 2026-04 | anti-slop 雙層掃描 + design-context-import |
| v1.3 | 2026-04 | mode-conditional + async 訊息通道模式 |
| v1.4 | 2026-04 | 字體配對 + Content Fidelity Lock + chart 元件 + consulting preset |
| v1.5 | 2026-04 | PPTX 語義翻譯 + 品牌資產 + tweaks + 場景模板 + 設計哲學庫 |
| v1.6 | 2026-05 | PPTX 品質強化（Stacking Context DFS / Rich Text / Border 映射） |
| v1.7 | 2026-05 | HTML→MP4 + 7 sins CSS token-aware + 9-section schema + 品牌模板 ×5 + craft rules + Stage 0 意圖判定 |

---

## 常見問題

**Q: 如果沒有安裝 Playwright 怎麼辦？**
A: pdf-export 和 export-deck-pptx 需要 Playwright。在工作目錄執行 `npm install playwright` 或安裝為全域套件。

**Q: HyperFrames 需要額外安裝嗎？**
A: 是的，執行 `npm install -g hyperframes`。需要 Node.js ≥ 22 和 FFmpeg。若未安裝，html2video 會自動退化為 Playwright 截圖 + FFmpeg 合成。

**Q: DESIGN.md 必須符合什麼格式？**
A: Google design.md YAML frontmatter + 9 section Markdown body。Stage 3 會自動產出符合格式的 DESIGN.md，並用 `npx @google/design.md lint` 驗證。

**Q: 可以只跑 anti-slop 掃描不跑完整 pipeline 嗎？**
A: 可以，直接使用 `/anti-slop-review` skill 或執行 `python3 scan.py <target>`。

**Q: 中文字體在 PPTX 中如何處理？**
A: html2pptx 預設將 Noto Sans TC 映射為微軟正黑體（`--font-map` 可自訂）。PPTX 開啟端需安裝對應字體。

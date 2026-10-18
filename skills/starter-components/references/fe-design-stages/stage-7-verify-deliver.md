> 用途：fe-design pipeline 第 7 階段驗證與交付完整規格。
> 來源：自 fe-design.md v1.8.3 第 733–982 行拆出，2026-08-27。
> 本檔由 ~/.claude/commands/fe-design.md 於該階段以 Read 載入；修改本檔等於修改 pipeline。
> 範圍：只承接原主檔第 7 階段內容。

### [7/7] ✅ 驗證與交付

| Mode | 交付物 |
|---|---|
| `deck` | `delivery/deck.html`（Playwright 投影驗證 OK）+ `delivery/deck.pdf`（**viewport-matching 1920×1080 預設**，見下 §PDF）+ `delivery/deck-standalone.html`（`tools/standalone-export.mjs` inline）+ `delivery/deck.pptx`（見下方步驟 4）+ `delivery/deck.mp4`（可選，見下方步驟 6）|
| `page` | `delivery/page.html`（**a4-portrait PDF 預設**，見下 §PDF）+ `delivery/page-standalone.html` |
| `app` | `delivery/components/` 完整目錄樹 + `delivery/integration-guide.md` |
| `system` | `delivery/.design/DESIGN.md`（必交）+ `delivery/.design/design_tokens.json` + `delivery/.design/tailwind.theme.extend.js`（後二者由步驟 5 export 產生）|
| `migrate` | `delivery/migration-plan.md` + `delivery/patches/*.diff` |

#### 管線輸入隔離規範（v1.3.1 §18.3.1，MED #3 修補）

`deck-standalone.html`（含 inline base64 字型，可達 45 MB）**僅作最終離線封裝交付物**，**不可作為下游處理的中繼輸入檔**。

| 步驟 | 輸入檔 | 禁止輸入 |
|---|---|---|
| 1. Playwright viewport / interaction smoke test | `delivery/deck.html`（外部 fonts，60 KB 級）| `deck-standalone.html`（45 MB 會嚴重拖慢 Playwright + page.evaluate）|
| 2. PDF 列印（@media print）| `delivery/deck.html` | `deck-standalone.html`（PDF 引擎需 fetch font 不需 inline）|
| 3. 截圖（slide-NN.png）| `delivery/deck.html` + Playwright 雙字型 cache 預熱 | `deck-standalone.html` |
| 4. PPTX 產出（v1.5 語義級 adapter `export-deck-pptx.mjs`）| `delivery/deck.html`（Playwright DOM 遍歷）| `deck-standalone.html`（base64 inline 會拖慢 Playwright）|
| 5. **零外部依賴驗收** | `delivery/deck-standalone.html`（**唯一例外**）| - |
| 6. 最終交付封裝 | `delivery/deck-standalone.html` 直接給客戶 | - |

違反此規範將導致 Playwright timeout / PDF 緩慢 / PPTX adapter 卡死。

#### 驗證 / 產出流程（依 mode 條件執行）

1. 用 Playwright 寫一支簡短的 smoke test 對 deck/page/app 做 viewport / interaction smoke test —— **以 `delivery/deck.html` 為輸入**（不用 standalone）
2. **零外部依賴驗證**：**僅本步驟**對 `deck-standalone.html` 做斷網測試（fetch override 攔所有 outbound request → 確認 0 個外部呼叫）
3. **產 metadata**：`delivery/build-metadata.json`（v1.3.1 P5.8 schema 區分 viewport / pdf.page_size / physical_paper_size / pptx.text_editable）：
   ```json
   {
     "brief": "<…>",
     "mode": "deck",
     "build_timestamp": "2026-04-26T18:30:00+08:00",
     "scaffolds": ["deck_stage.js"],
     "deck": {
       "viewport": { "width": 1920, "height": 1080, "unit": "px" },
       "html": "delivery/deck.html",
       "standalone": "delivery/deck-standalone.html"
     },
     "pdf": {
       "path": "delivery/deck.pdf",
       "format": "viewport",
       "viewport_px": { "width": 1920, "height": 1080 },
       "page_size_pt": { "width": 1440, "height": 810, "note": "PDF point = px ÷ 96 dpi × 72 pt/in；1920×1080 viewport → 1440×810 pt（無 A4 縮放）" },
       "page_count": 13,
       "note": "v1.4-short §24.5 P6.4：deck mode 預設 viewport-matching；明確指定 width/height 而非 format:A4，避免 chromium 自動 fit-to-A4 壓縮 wide gantt/table"
     },
     "pptx": {
       "path": "delivery/deck.pptx",
       "mode": "semantic",
       "text_editable": true,
       "layout": "LAYOUT_WIDE",
       "layout_size_pt": { "width": 960, "height": 540 },
       "pptxgenjs_version": "4.0.1",
       "font_map": { "Noto Sans TC": "微軟正黑體" },
       "per_slide_stats": [
         { "slide": 1, "semantic_elements": 12, "fallback_elements": 1, "semantic_ratio": 0.923, "core_text_semantic": true }
       ]
     },
     "fidelity_lock": {
       "facts_table_count": 7,
       "positive_match_passed": true,
       "reverse_check_provider": "<另一個模型>",
       "reverse_check_unknown_count": 4,
       "verdict": "NEEDS_HUMAN_REVIEW",
       "fact_check_json": "verify/fact-check.json",
       "note": "v1.4-short §24.3 P6.2：deck/page mode shortcut 必跑；verdict=FAIL 阻斷 ship、verdict=NEEDS_HUMAN_REVIEW 需使用者/主腦複核 unknown 後才結案"
     },
     "lint_warnings_unresolved": 0,
     "async_timeout_advances": []
   }
   ```

   **欄位條件**：`fidelity_lock` 為 deck/page mode 必填；app/system/migrate mode 可省略。`verdict=FAIL` 時 ship gate 阻斷；`verdict=NEEDS_HUMAN_REVIEW` 時 build-metadata 額外加 `requires_human_review: true` 提示最終 Checkpoint 必須由人工逐項確認 unknown entities 後才能 ✅。

   **app mode 最小 metadata**：
   ```json
   {
     "brief": "<…>",
     "mode": "app",
     "build_timestamp": "2026-05-24T18:00:00+08:00",
     "scaffolds": ["design_canvas.jsx", "ios_frame.jsx"],
     "components": {
       "entry": "delivery/components/index.tsx",
       "sub_components": ["Header.tsx", "Sidebar.tsx"],
       "total_files": 5,
       "total_loc": 420
     },
     "lint_warnings_unresolved": 0
   }
   ```

   **system mode 最小 metadata**：
   ```json
   {
     "brief": "<…>",
     "mode": "system",
     "build_timestamp": "2026-05-24T18:00:00+08:00",
     "design_md": "delivery/.design/DESIGN.md",
     "tokens_export": {
       "dtcg": "delivery/.design/design_tokens.json",
       "tailwind": "delivery/.design/tailwind.theme.extend.js",
       "status": "success"
     },
     "lint_warnings_unresolved": 0
   }
   ```

   **migrate mode 最小 metadata**：
   ```json
   {
     "brief": "<…>",
     "mode": "migrate",
     "build_timestamp": "2026-05-24T18:00:00+08:00",
     "migration": {
       "plan": "delivery/migration-plan.md",
       "patches": ["delivery/patches/001-colors.diff", "delivery/patches/002-typography.diff"],
       "patch_count": 2
     },
     "lint_warnings_unresolved": 0
   }
   ```
4. **PDF 產出 — viewport-matching 預設**（v1.4-short §24.5 P6.4）：

   `~/.claude/skills/starter-components/tools/pdf-export.mjs --input <html> --output <pdf> --pdf-format <fmt>`

   | Mode | 預設 `--pdf-format` | 行為 |
   |---|---|---|
   | `deck` | `viewport`（1920×1080）| Playwright `page.pdf({width:'1920px', height:'1080px', preferCSSPageSize:false})`，wide gantt / table 不被壓縮；**禁用** `format:'A4'`（chromium 96 dpi 縮放會把 1920×1080 壓成 1440×810）|
   | `page` | **雙 PDF 預設**（v1.4-short §24.7 P6.6）：pipeline 兩次呼叫 `pdf-export.mjs`，分別產 `page-a4.pdf` (`--pdf-format a4-portrait`) + `page-viewport.pdf` (`--pdf-format viewport`) | A4 給 reading print 後閱讀；viewport 給 mobile mock 預覽 / 大人提平台等 fixed aspect ratio 場景。**`pdf-export.mjs` 本身不知道「page mode」概念**，只看 `--pdf-format`，雙產出是 pipeline 層責任（單一職責，避免工具耦合）|
   | `app` | — | 不產 PDF |

   `--pdf-format` 旗標三選一：`viewport` / `a4-landscape` / `a4-portrait`。
   build-metadata.json 的 `pdf.format` 必須與實際呼叫一致；deck mode 走 A4 需有理由（客戶指定列印）並寫入 metadata。

   **page mode pipeline script template**（§24.7 P6.6）：

   ```bash
   PDF_TOOL=~/.claude/skills/starter-components/tools/pdf-export.mjs

   # A4 reading 版（print friendly）
   node $PDF_TOOL --input delivery/page.html --output delivery/page-a4.pdf \
     --pdf-format a4-portrait

   # viewport 截圖版（mobile mock 預覽用）
   node $PDF_TOOL --input delivery/page.html --output delivery/page-viewport.pdf \
     --pdf-format viewport
   ```

   build-metadata.json `pdf` 欄位必為 page mode 雙 PDF 列出兩筆：

   ```json
   "pdf": {
     "page-a4.pdf": { "format": "a4-portrait" },
     "page-viewport.pdf": { "format": "viewport", "viewport": { "w": 1920, "h": 1080 } }
   }
   ```

   **驗收**：（i）pipeline 真的呼叫兩次（grep build log）；（ii）`pdf-export.mjs` 源碼**不含** `page mode` / `mode === 'page'` 等字串（grep 確認解耦合）；（iii）兩份 PDF 各自由獨立 invocation 產出，不互相依賴。

   #### Visual Diff Report — deck mode 多次迭代可選工具（v1.4-short §24.4 P6.3）

   當同一 deck 案有多版（v1 / v2 / v3 …）並存（典型情境：客戶反饋 → 重做 → 比較進步），可選跑 visual-diff 出 side-by-side 報告：

   `~/.claude/skills/starter-components/tools/visual-diff.mjs --base <html> --target <html> --out <dir> [flags]`

   | 旗標 | 說明 |
   |---|---|
   | `--pages all\|1-5,10` | default all；接受逗號 + 範圍 |
   | `--threshold 0-1` | pixelmatch 像素差異閾值（default 0.1）|
   | `--diff-ratio-warn 0-1` | 單頁差異比例超過此值即標 warn（default 0.01）|
   | `--base-nav-strategy / --target-nav-strategy` | `deck`（`window.__deck.goto(i)`）/ `scroll`（`.slide` locator）/ `url-hash`；可分別指定（不同版本 navigation API 通常不一致）|
   | `--base-nav-selector / --target-nav-selector` | scroll 策略 CSS selector（default `.slide`）|

   **輸出**：`<out>/{base,target,diff}/slide-NN.png` × N + `diff-summary.json` + `visual-diff-report.html`（client-side render，可直接 `open`）

   **Exit code**：
   - `0` — 全頁 OK（無 warn 無 skip）
   - `2` — 有 warn（差異超閾值）或 skip（截圖失敗 / size mismatch / 頁數不匹配）
   - `1` — 流程錯誤

   **使用時機**：deck mode v1 ship 後客戶反饋 → 重做 v2 → 對 v1 / v2 跑 visual-diff 證明改善有實質視覺差異；非例行步驟。

5. **deck mode PPTX 產出**（v1.5 P7.1a/1b 語義級翻譯器）：

   ```bash
   PPTX_TOOL=~/.claude/skills/starter-components/tools/export-deck-pptx.mjs

   node $PPTX_TOOL --input delivery/deck.html --output delivery/deck.pptx \
     --metadata delivery/build-metadata.json
   ```

   - 預設 `--pptx-mode semantic`：Playwright DOM 遍歷 → pptxgenjs 逐元素翻譯，文字框可編輯
   - 退回 `--pptx-mode image`：語義翻譯失敗時自動降級，或由使用者 `--pptx-mode image` 手動指定
   - `--font-map <json>`：自訂 CJK 字體映射（預設 Noto Sans TC → 微軟正黑體）
   - `--metadata` 指定時自動更新 build-metadata.json 的 `pptx` 欄位
   - HTML 約束文件：`Read ~/.claude/skills/starter-components/references/editable-pptx.md`（7 條約束 + 畫布策略 + 降級路徑）
   - 若 brief 指定需 PPTX 交付 → Stage 5 實作時自動套用 7 條 HTML 約束（禁 CSS transform 排版 / 禁 gradient 背景 / 文字必須在可識別 DOM 節點）

   **PPTX fidelity/editability 分級（v1.8 P10.6）**：HTML 為視覺母版與主要交付；PPTX 依需求走三級，交付時明示等級，不把翻譯器當像素級還原器：

   | Tier | 路線 | fidelity | editability | 適用 |
   |---|---|---|---|---|
   | A `semantic-translated` | export-deck-pptx.mjs 語義翻譯 | 中（editorial 排版接受字距/換行/定位偏差） | 高（文字框可編輯） | 客戶要改字的相容版 |
   | B `image-fallback` | `--pptx-mode image` | 高（像素級） | 低（整頁圖） | 只投影不編輯 |
   | C `native-rebuilt` | PptxGenJS 原生重建＋PDF/contact-sheet QA | 高 | 高 | PPTX 是核心交付且高可編輯；**另行規劃**，複雜版型須落在 PptxGenJS 支援的格線與元件內 |

   - build-metadata.json `pptx` 欄位加 `"fidelity_tier": "A|B|C"`；最終 Checkpoint 必向使用者明示所選 tier 與取捨。
6. **deck mode MP4 導出**（v1.7 P9.2/P9.3，條件觸發）：

   **觸發條件**（滿足任一即觸發，僅 deck mode）：
   - 使用者明確要求「轉影片」/「output video」/「promo clip」/「MP4」
   - 使用者在最終 Checkpoint 選擇「+ 匯出 MP4」

   **非 deck mode 攔截**：若 page/app/system/migrate mode 的 brief 含影片相關詞，在最終 Checkpoint 明確提示「MP4 導出僅適用 deck mode，若需影片請切換 mode 或另行處理」

   ```bash
   VIDEO_TOOL=~/.claude/skills/starter-components/tools/html2video.mjs

   node $VIDEO_TOOL --input delivery/deck.html --output delivery/deck.mp4 \
     --slide-selector "section.slide" --fps 30
   ```

   - 引擎：HyperFrames v0.6.40+（Apache 2.0）→ 逐幀截取 + FFmpeg 編碼
   - 退化方案：HyperFrames 不可用時自動退化為 Playwright 截圖 + FFmpeg 合成（無動畫）
   - 解析度：預設 1920×1080（viewport-matching，與 PDF 一致）
   - 時長：預設 slide 數 × 5 秒，可用 `--duration` 覆蓋
   - build-metadata.json 加欄位：
     ```json
     "mp4": {
       "path": "delivery/deck.mp4",
       "engine": "hyperframes",
       "hyperframes_version": "0.6.40",
       "duration_seconds": 15,
       "fps": 30,
       "resolution": "1920x1080"
     }
     ```
   - **不適用**：page / app / system / migrate mode
   - **管線輸入隔離**：MP4 用 `delivery/deck.html`（非 standalone），與 PPTX 一致

7. **system mode token export**（依規劃書 IV8）：必跑兩條
   - `npx @google/design.md@0.1.1 export <project_root>/.design/DESIGN.md --format dtcg > delivery/.design/design_tokens.json`
   - `npx @google/design.md@0.1.1 export <project_root>/.design/DESIGN.md --format tailwind > delivery/.design/tailwind.theme.extend.js`
   - 任一 export 失敗 → 沿用 anti-slop-review 的 vendored fallback（見「失敗處理」），仍失敗則寫 `tokens_export_status: "failed"` 並警示

8. **deck mode 機械關卡重跑與交付 metadata**：只適用 deck mode；**本步不過，最終 Checkpoint 不得呈報結案**。
   metadata 必含完整 brief、pending_decisions、每份 HTML 的 deck-gates 結果與退出碼、輔助詞表每處保留理由。deck-gates 的署名與變體規則改由設定檔定義（見 `skills/starter-components/scripts/` 的設定檔），預設不檢查署名。封裝後 deck.html 與 deck-standalone.html 各產同名 `.gates.json`，各跑 `bash ~/.claude/skills/starter-components/scripts/deck-gates.sh <成品.html> <參數>`（參數依設定檔）；任何非零不得交付。未確認的決議不得標成已確認，回報殘餘狀態。

**最終 Checkpoint**：第 8 步 deck-gates 全數 exit=0（或非 deck mode）後列出 delivery/ 內容 → 等 ✅ 結案 / 🔄 微調

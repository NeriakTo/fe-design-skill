# Rendered QA — Contact Sheet 先行、Optical Pass 與渲染後硬 Gate

> 版本：v1.8 P10.3/P10.5
> 觸發時機：Stage 5 工序（contact-sheet 先行＋Optical Pass）與 Stage 6 渲染後四道 Gate
> 核心命題：源碼掃描抓不到視覺問題；QA 必須看渲染結果。

---

## 1. Contact Sheet 先行工序（Stage 5，deck mode）

**工序反轉：先產全副低保真、審節奏，後精修單頁。** 逐頁精修再回頭看整體＝返工。

1. 依 slide plan 快速產出全部頁面的低保真版（版型骨架＋真標題＋灰塊佔位圖）。
2. 渲染 contact sheet：Playwright 逐頁截圖 → montage 成一張格狀總覽（或用 deck overview 模式截圖）。
3. **節奏審查**（過了才准精修）：
   - 單一版型連續 ≤2 頁（表格連發例外，需理由）。
   - 全副版型重複率 ≤25%（同版型頁數 / 總頁數）。
   - 每 4 頁至少一次構圖轉折：全幅↔留白、深底↔淺底、圖像頁↔排版頁。
   - 情緒曲線可見：至少一個高峰頁；首尾呼應成立。
   - 標題塊、頁碼徽章、footer 位置跨頁一致。
4. 節奏不過 → 改 slide plan 換版型，**不是**加裝飾補救。

## 2. Optical Pass（Stage 5 精修完成後，逐頁）

中文微排版檢查——這一層多數同類工具沒做全（例如封面副標「位置」孤字斷行），是拉開品質差距的地方：

| 檢項 | 標準 |
|---|---|
| 中文斷行 | 標題與重點句不得出現 1–2 字孤行（孤字）；手動 `<br>` 或改寫句長 |
| 標點懸掛 | 行首不得出現「，。、」；用 `text-wrap: balance` 或斷句調整 |
| 視覺置中 | 大標題區塊看起來置中（optical center），非只有數學置中 |
| 基線對齊 | 並排卡片的標題/內文基線對齊；中英混排基線不跳動 |
| 圖文張力 | 文字塊與插畫主體不搶焦點；視線動線單一入口 |
| 溢出 | 任何元素不得溢出 slide 邊界或壓到 96px safe area |

## 3. Stage 6 渲染後四道 Gate（deck mode 必跑，依序）

全部掛在 v1.7 既有 3-attempt 斷路器之下（單一 gate 修 3 次仍 fail → 停止、記錄、轉人審）。

### Gate 1 — Contact-sheet Rhythm（複跑第 1 節標準）

精修後重產 contact sheet 再審一次（精修常把節奏改掉）。輸出 `qa/contact_sheet_vNNN.png` + 審查結論寫入 `qa/visual_review_vNNN.md`。

### Gate 2 — Typography / Overflow 自動量測

Playwright `page.evaluate` 逐頁量測，輸出 `qa/typography_audit_vNNN.json`：

- 最小字級：投影內文 <28px、註記 <22px → FAIL（以 computed style 抓實際 px）。
- 同層級字差 >2px → WARN。
- 溢出偵測：任何 descendant bounding box 超出 slide bounds → FAIL。
- 行長：標題 >14 CJK/行 → WARN。
- 對齊：同 class 卡片 left edge 偏差 >2px → WARN。

### Gate 3 — 100% 截圖人工評審 ＋ 渲染後 Slop Diagnostic

逐頁截圖全數過眼（不抽樣），對照 10 項渲染後 slop 指標（源自視覺審查實務，與源碼層 19 tropes 互補）：

1. tech gradient（無來由的科技感漸層）
2. generic indigo（預設靛藍/紫藍主色）
3. repetitive feature grid（等寬卡片格連發）
4. accent rails（裝飾性側邊色條）
5. glass blur（毛玻璃濫用）
6. monument stats（超大數字紀念碑排版濫用）
7. icon toppers（每卡頂一顆 icon）
8. center-stack dependence（頁頁置中堆疊）
9. default Inter（未依 contract 換字體）
10. surface mismatch（卡片底色與主背景體系脫節）

輸出：`qa/visual_review_vNNN.md` 必含「Slop diagnostic: N/10」＋逐項說明；N>0 → 修復後重跑。

### Gate 4 — Viewport Fit 實測（v1.8.2）

前三 gate 全在固定 1920×1080 渲染，「換視窗尺寸會不會爆」是覆蓋盲區——scaffold 被繞過、無縮放邏輯時三 gate 照樣全綠，交付 HTML 在瀏覽器直接溢出（實務上出現過）。

測試矩陣（全組合必須 PASS）：
- 視窗：至少 1440×900＋1280×800（非 1920）
- JS 開／關（關＝模擬 CSP／sandbox iframe 下 inline script 不執行；縮放需有 CSS fallback，如 `zoom:var(--fitzoom,calc(100vw / 1920px))`）
- 目標檔：`deck.html` 與 `delivery/deck-standalone.html` 皆測（standalone 才是交付物；inline builder 漏帶 script 時只測源檔＝假綠）

判定：
1. 水平無溢出：`documentElement.scrollWidth ≤ innerWidth + 2`
2. 逐頁邊界：每張 slide 的 `rect.left/right` 落在 viewport ±2px 內（只量第一張＝盲區）
3. 量測對象消失（slide 數 0／deck 容器不存在）＝FAIL（防 selector 改名假綠）
4. print 安全：`emulateMedia('print')`＋1920×1080 下 deck 容器 computed zoom 必須為 1（pdf-export 走 print media，縮放不得滲入）

報告 `qa/viewport_fit_report.json` 必記錄：實際 computed zoom、逐情境 scrollWidth／edgeViolations／slideCount。已知限制：單引擎 Chromium（WebKit/Firefox binary 未裝，deferred backlog）；行動裝置 pinch／visualViewport 不在 deck 交付情境（rejected，桌面 headless 下該斷言恆真＝儀式性檢查）。

## 4. C2 人審包

Stage 6 結束的 C2 checkpoint，deck mode 必呈：contact sheet 圖 + typography audit 摘要 + slop diagnostic 分數 + 未解 issue 清單。使用者 ✅ 才進 Stage 7 交付。

## 4.5 首案實戰檢核（實務經驗，每案必查）

1. **PDF spill 頁**：print 模式下 `body` 預設 8px margin 會把第一頁內容推擠溢出，多產生一頁只有髮絲線的空白頁。每個 deck 案 CSS 必含 `@media print{html,body{margin:0;padding:0}}`；匯出後 `pdfinfo` 驗頁數＝slide 數。
2. **雙頁碼**：`deck_stage.js` 有內建右下角計數器；案內若自訂頁碼元件，必須 `--deck-counter-bg:transparent; --deck-counter-fg:transparent` 關閉內建，否則兩個頁碼疊在角落。
3. **Gate 2 量測必須逐頁 goto**：deck-stage 會隱藏非當前 slide（bounding box 為 0），一次性掃全 DOM 只會量到當前頁——量測迴圈要 `window.__deck.goto(i)` 後量當前頁，否則假 PASS。
4. **工具鏈**：`pdf-export.mjs`／`standalone-export.mjs` 需 playwright；全域安裝時用 `NODE_PATH=$(npm root -g)` 前綴執行；`--input` 只吃檔案路徑不吃 URL。

## 5. 與既有機制的關係

- anti-slop 三層（lint / 19 tropes / 7 sins）照跑——它們掃源碼，本文件審渲染，互補不取代。
- design-review（gstack）互動關卡照跑，本文件的 Gate 3 給它渲染截圖當輸入。
- 量化評審（design-critique.md 5 維度）仍為可選加值項。

---
description: 前端設計 pipeline：簡報（deck）、網頁（page）、應用介面（app）、設計系統（system）、改版遷移（migrate）五種模式，七階段含兩次人審，交付前跑去 AI 味（anti-slop）掃描與渲染後檢查。要做簡報、頁面、介面或設計系統時使用；單頁白話說明可改用外部的 eli5 技能（anthropics/claude-plugins-community，選用）。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
---

# /fe-design

對前端設計需求啟動七階段 pipeline；各階段詳細規格見 `~/.claude/skills/starter-components/references/fe-design-stages/`（章節編號的說明見倉庫 README）。

> **外部技能說明**：本流程引用的 gstack（design-review、design-consultation）、frontend-design、frontend-slides、awesome-design-md 等皆為選用的外部技能，不在本倉庫；未安裝時略過該步驟（降級規則見「Skill 降級表」）。

> **設計哲學**：anti-slop、lint、fact lock 負責防爛；Visual Thesis、美術契約、contact sheet 先行與渲染後 QA 負責造好。通過 lint ≠ 通過 art direction。

> **模型移轉性**：本 pipeline 品質三支柱中，機械 gate（lint／字級量測／fact-check／pdfinfo 頁數）與工具鏈（pdf-export／standalone-export／browse 渲染／生圖工具產圖）**不依賴主模型**；品味層（Visual Thesis 命名、文案 voice、Optical Pass 眼力）依模型而異。主模型的品味層較弱時，建議三條配套，每次換主模型重測這三條是否仍需要：① C1／C2 兩個人審點從速審改嚴審（品味兜底交給人）；② Stage 2 建議請另一個模型共筆發想概念；③ 動工前必讀 `deck-art-direction.md` 與 `rendered-qa.md`，照其中的工序逐步執行，不跳步。
> **進場條件**：動工時 context 已偏高（過半）者，**禁止在同 session 尾端直跑 deck pipeline**，必須分段或換 fresh session 用完整 context 跑。實務經驗：在長 context 尾端容易偷工 contact sheet／Optical Pass／qa 產物，造成頁間品質不均。deck mode 渲染後的對抗式審查見 §[6/7]（可選，建議做）。

## 用法

```
/fe-design [mode] [brief] [flags]
/fe-design --resume
```

- `mode`（可選）：`deck` / `page` / `app` / `system` / `migrate`
  未指定時進入互動式 mode 選擇（[0/7] 階段）
- `brief`（可選）：一句話描述需求，未指定時進入互動澄清（5 問）
- `--resume`（特殊旗標）：與 `mode` / `brief` **互斥**；觸發中斷恢復流程，不走參數 parse（見「中斷恢復」章節）

### Flags（v1.3.1 新增）

| Flag | 預設 | 用途 |
|---|---|---|
| `--async-timeout <minutes>` | 5 | async 模式下 stage checkpoint 等待時間（§20.3）|
| `--async-default <accept\|skip\|abort>` | accept | timeout 後行為（accept=取首選 / skip=跳過 / abort=暫停）|
| `--full-design-consultation` | off | deck/page/app mode 強制走 design-consultation 完整 6-Phase（§19.2）|
| `--shortcut` | off | system mode 強制走主腦快速寫（會發 warning）（§19.2）|

## 範例

- `/fe-design deck "客戶 4/29 啟動會議"` — 完整參數，3 快題後直接 pipeline
- `/fe-design page "課程 landing"` — page mode + 互動澄清剩餘 4 問
- `/fe-design system` — 對既有 codebase 抽 design system，跳過 stage 4-5
- `/fe-design` — 全互動，先選 mode 再問 brief
- `/fe-design --resume` — 從 `.checkpoints/` 恢復前次中斷的 pipeline

## 解析行為

收到指令時，**Claude 必須**：

0. **`--resume` 短路特判**：若 `$ARGUMENTS` 等於 `--resume`（trim 後完全相等）→ 直接跳到「中斷恢復」章節，**不走** mode/brief parse；其他 `--xxx` 旗標見「Flags」章節（共 4 個）+ `--resume`。未列名旗標 → 回報「unknown flag」並列出合法用法。
0.5. **async 模式偵測**（v1.3.1 §20.2）：
   - 啟動來源含訊息通道標記（例如聊天頻道轉入的指令）→ **async（訊息通道）模式**
   - 啟動參數含 `--async-timeout <minutes>` → **async（顯式）模式**
   - 否則為 **sync 模式**（TTY 互動式 / `claude` REPL）
   - **若判定為 async 模式**：在 [1/7] 開始前必送一則精簡通知訊息（§20.3.1）：
     ```
     🤖 fe-design async 模式啟動（5 min timeout 自動推進；連續 3 次將暫停）
     詳細規則：/fe-design --help 或本規劃書 §20.3
     ```
   - **規則覆寫聲明**（v1.3.1 §20.2.1）：v1.2.2 §5.3「30 min 預設超時轉 draft」**僅 sync 模式生效**；async 模式由本契約覆寫。
1. **`project_root` 解析**：在 git repo 內 → 取 `git rev-parse --show-toplevel`；不在 git 內 → 取 `cwd`（current working directory）。整份指令一律使用 `<project_root>` 為唯一變數名稱（不再有 `<user-project>` / `<project-root>` / `<project>` 等舊別名）。
1.5. **case dir 隔離 hint**（v1.3.1 P5.6）：若 `<project_root>` 偵測為共享工作目錄（特徵：根目錄含 `knowledge-base/` 或 `_standards/`，或 `<project_root>` 是多個案子共用的工作目錄）→ 主腦主動建議：
   ```
   ⚠ 偵測到當前 project_root 為多案共用的工作目錄
   建議在子目錄做 git init 隔離，避免 .checkpoints/ delivery/ 等中間檔污染。
   推薦結構：
     <共用工作目錄>/design-cases/<case-name>/
   建議先執行：
     mkdir -p <共用工作目錄>/design-cases/<case-name> && cd $_
     git init && git commit --allow-empty -m "init: <case-name>"
   ```
   使用者批准 → 主腦改用該目錄為 `<project_root>` 並重新解析。
   使用者拒絕 → 警示後繼續，但禁止寫 `<project_root>/.checkpoints/`，改寫 `<project_root>/.fe-design-cache/<ISO timestamp>/`。
2. parse `$ARGUMENTS` 拆出 `mode` / `brief` / flags
3. 若 `mode` 未指定 → **走 Stage 0 意圖判定**（見下方「Stage 0」段）：
   - 有把握 → 推薦推斷結果 + 理由，AskUserQuestion 確認（推薦選項置首，附 `(Recommended)`；其餘 4 mode 列第二起）
   - 兩可或沒有訊號 → AskUserQuestion 列 5 種 mode + 簡短說明
   - async 模式 timeout 預設：有把握取推斷結果；兩可取 `deck`；沒有訊號就暫停等回覆
4. 若 `brief` 未指定 → AskUserQuestion 問 5 題（用途/受眾/品牌參考/輸出格式/時程）
5. 若兩者都指定 → 直接 [1/7] 階段問 3 快題（聽眾/時長/品牌基調）
6. **每階段完成後**主動停下、彙整本階段產出、等使用者回覆 ✅ 繼續 / 🔄 修正本階段 / ⏪ 回上一階段（async 模式行為見「Async checkpoint 行為」段）
7. C1（stage 3 後）和 C2（stage 6 後）自動觸發 Context Summary & Clear（含 async timeout 推進歷史表，§20.3.3）

### Async checkpoint 行為（v1.3.1 §20.3）

每個 [N/7] checkpoint 在 async 模式下走以下契約：

| 互動 | sync 模式 | async 模式 |
|---|---|---|
| AskUserQuestion 多選 | 等到回覆為止 | timeout (`--async-timeout`，預設 5 min) → 取第一個選項 |
| 是非題（✅繼續 / 🔄修正 / ⏪回上）| 等到回覆為止 | timeout → 取 ✅繼續 |
| 自由文字題 | 等到回覆為止 | timeout → 以 brief 為基礎合理推斷 |
| 30 min 無回覆 | 寫 draft + memory checkpoint（v1.2.2 §5.3）| **不適用**（已被 §20.2.1 覆寫）|
| 5 min 無回覆 | 等到回覆為止 | 走預設值 + 記錄到 timeout 推進歷史 |

每次 timeout 推進後，主腦在 stage 完成訊息中明示：「⏱ stage [N/7] 走 timeout default 推進，已記錄到 timeout 推進歷史」。

### Async 連續 timeout 安全閥（v1.3.1 §20.3.4）

主腦記錄「連續 timeout 推進的 stage 數」。當數值 ≥ **3** → 主動暫停，發送：

```
⚠ 連續 3 個 stage 走 timeout default 推進
（[2/7] 風格 / [3/7] 設計系統 / 🧹 C1 通過）

擔心你不在線上或 brief 偏離，主動暫停 stage 4。
請回覆：
- ✅ 繼續推進
- ⏪ 回 [2/7] 重新討論風格
- ⏸ 暫停 pipeline，存 checkpoint
```

重置條件：使用者明確回覆任何非 timeout-推進的選擇 → 計數歸零。

---

## Stage 0 — 意圖判定（v1.7 Tier 3）

當使用者未指定 `mode` 但有提供 `brief` 時，主腦依以下訊號推斷最可能的 mode。

### 訊號表

| Mode | 關鍵詞訊號（brief 文字比對，最長匹配優先） | 專案結構訊號 |
|---|---|---|
| `deck` | 簡報、PPT、PPTX、投影片、slide、pitch、deck、課程簡報、報告、會議、啟動、kickoff、提案、presentation、fullday、培訓、教材 | 無既有 codebase |
| `page` | landing page、頁面、官網、blog、文章、說明頁、作品集、portfolio、單頁、介紹頁、one-pager、課程頁 | 存在 index.html 但無 React/Vue 框架 |
| `app` | app、應用程式、後台、dashboard、管理介面、UI 元件、component、面板、interface、表單系統 | 偵測到 React/Next.js/Vue（package.json 含 react/next/vue） |
| `system` | design system、設計系統、design token、品牌規範、style guide、主題規範 | 存在 `.design/DESIGN.md` 或 `design-tokens` 目錄 |
| `migrate` | migrate、遷移、改版、升級設計、重構設計、refactor design、替換設計、redesign | 存在 `.design/DESIGN.md` + 既有元件程式碼 |

### 匹配規則

- **匹配方式**：以空格/標點為邊界做 token-level 比對（非子字串）
- **最長匹配優先**：「課程簡報」命中 deck 而非同時命中 deck（課程）和 page（課程頁）
- **否定偵測**：brief 含「不要/排除/非」+ 關鍵詞 → 該詞不計分

### 推斷規則

依 brief 用詞（上表關鍵詞，否定語境不算）與專案結構訊號，判斷最可能的 mode。有把握時推薦一個並寫出依據；兩個 mode 都說得通或沒有訊號時，列出五種讓使用者選。推斷錯的代價高於多問一題，拿不準就問。

### 推薦格式

有把握時，AskUserQuestion 呈現：

```
根據 brief「{brief}」推斷 mode = {mode}
理由：{命中的關鍵詞} + {專案結構訊號}
```

選項：推薦 mode 置首 + 剩餘 4 mode。使用者可選其他 mode 覆蓋推斷。

### 安全閥

- 推斷結果**不跳過 Stage 1 澄清**（仍需確認受眾/時長/品牌基調）
- 專案結構偵測限輕量操作（ls + grep package.json），不做深度 AST 分析

---

## 7 階段 Pipeline（§5.1）

### [1/7] 📋 澄清

**Deck 第一步先確認簡報用途**：先確認簡報用途與署名需求，再問下列澄清題。deck-gates 的署名與變體規則改由設定檔定義（見 `skills/starter-components/scripts/` 的設定檔），預設不檢查署名；需要署名檢查時自行在設定檔指定。

**設計參考文件索引預載**（v1.5 P7.13）：Stage 1 開始前，`Read ~/.claude/skills/starter-components/references/INDEX.md` 載入設計參考文件索引，後續 stage 依需要載入個別文件。

| 條件 | 行為 |
|---|---|
| 已有 mode + brief | 問 5 快題：受眾、受眾先驗（v1.8.3 P11.1）、時長、品牌基調、字體配對方案（v1.4 §24.2.1，deck/page mode 必問；app/system 可選）|
| 已有 mode 無 brief | 問 7 題：用途 / 受眾 / 受眾先驗 / 品牌參考 / 輸出格式 / 時程 / 字體配對方案 |
| 兩者皆無 | 先選 mode（[0/7]）→ 再問 7 題 |

#### 讀者先驗（v1.8.3 P11.1 — deck/page mode 必問；app/system 可選）

「受眾」問的是他們是誰，「受眾先驗」問的是他們對本次主題懂多少。兩題分開問，因為同一群人對不同主題的先驗不同（廠長對產線很熟、對 AI 一無所知）。

| 值 | 定義 | 對後續階段的影響 |
|---|---|---|
| `zero` ⭐ | 聽眾對主題一無所知（通識課、對外簡報、跨領域報告） | 啟用 deck-art-direction.md §2.5.2 全套：每頁一個新概念、術語同頁用生活比喻講清楚、圖先於字、DESIGN.md 加 `## Terms` 術語對照表（Lock 4） |
| `practitioner` | 聽眾做這行但不做這題（內部跨部門、客戶的工程師） | 術語可用但首次出現要白話帶過一句；不加 Terms 表 |
| `expert` | 聽眾就是本題專家（技術評審、同業） | 不限制術語密度；標題仍守 noun-only 禁令 |

**async timeout 預設**：deck 依 brief 判斷，page 為 `zero`——寧可講得太白，不可講得太深（常見情境：聽眾是跨部門一般員工，通識角度）。但 brief 或「受眾」答案已明示專家聽眾（「給 RD 評審」「同業交流」）時取 `practitioner` / `expert`，不強制 `zero`。

**來源**：eli5 skill 的一句話核心——「把讀者當成對這個主題一無所知的人，用大圖、少字解釋」（`anthropics/claude-plugins-community` 的 `eli5/skills/eli5/SKILL.md`）。與文案 register 互不重疊：register 管口氣，先驗管讀者懂多少，兩者相乘（例：企業通識課＝educational-warm × zero；給不懂 AI 的老闆做顧問提案＝consulting × zero）。

#### 用途類型（v1.9 — 全模式必定）

用途類型決定後續載入哪些品質規則（見 Craft Rules 動態注入）。mode 只給預設值，由主導的模型在本階段依 brief 的主要任務確認或改判，並寫一句理由。

| 類型 | 判定依據 | mode 預設 | 套用的品質規則 |
|---|---|---|---|
| `showcase` 展示型 | 主要任務是理解敘事、認識品牌、閱讀提案或活動內容 | deck、page | 共同四模組＋`taste-layout` |
| `utility` 實用型 | 主要任務是查詢、比較、編輯、監控或反覆操作 | app、system、migrate | 共同四模組＋`interaction` |
| `mixed` 混合 | 同一頁有敘事區與工作區 | 依頁面判定 | 共同四模組；`taste-layout` 只作用於明列的展示區，`interaction` 只作用於明列的工作區 |

邊界：企業網站不等於實用型（公司介紹是展示，登入後的報表才是實用）；簡報屬展示型，但仍受投影字級、固定畫布與匯出限制，不套網站的區塊間距；設計系統與改版依它服務的頁面判定。

**async timeout 預設**：取 mode 預設值。

#### 字體配對方案（v1.4 §24.2 — deck/page mode 必問；app/system 可選）

| 方案 | 標題 | 內文 | 適用 |
|---|---|---|---|
| A 西方 consulting | 明體（Source Serif 4 + Noto Serif TC） | 黑體（Inter + Noto Sans TC） | **僅當主受眾為英文用戶** |
| B 全黑體 + 字重對比 ⭐ | 黑體 800-900 重（Inter + Noto Sans TC） | 黑體 400-500 重 | **中文簡報通用，預設首選** |
| C 全明體 + 字重對比 | 明體 700 重 | 明體 400 重 | 年報 / 學術 / editorial |
| D 全黑體 + 不同字族 | 思源黑體 Bold | 文鼎黑 / 源樣黑 | 進階質感 |

**async timeout 預設**：B（中文受眾通用）

**重要**：禁止「明體標題 + 黑體內文」混搭（違反中文界基本法則 — justfont 等權威）。anti-slop trope-17 會自動掃描攔截。

**design-tokens-presets 對應**：
- A → `~/.claude/skills/starter-components/design-tokens-presets/mixed-bilingual.css`
- B → `consulting-mono-sans.css`（預設）
- C → `editorial-serif.css`
- D → `premium-mixed-sans.css`

**輸出**：`brief.json`（記憶體中的物件，不寫檔；存到階段 7 的 delivery metadata，deck 另含 `variant: "課程（客戶輔導）" | "提案" | "內訓" | "個人品牌"`、`signature`、`palette`、`wording_rules`、`output_formats`、`content_thresholds`、`pending_decisions`；含 `font_pairing: "A" | "B" | "C" | "D"`、`reader_prior: "zero" | "practitioner" | "expert"`、`usage_type: "showcase" | "utility" | "mixed"` 與 `usage_type_reason` 欄位）

**品牌資產觸發**（v1.5 P7.3）：若 brief 涉及具體品牌（使用者提了公司名/產品名/客戶名），在 Stage 1 結束前觸發核心資產協議。Read `~/.claude/skills/starter-components/references/brand-asset-protocol.md` 載入 5 步流程（問→搜→下載→驗證→固化 brand-spec.md）。產出的 `brand-spec.md` 供 Stage 3 Content Fidelity Lock 引用。

**Checkpoint**：彙整使用者回答 → 等 ✅ 繼續

---

### [2/7] 🎨 風格定位

**品質規則先讀**（v1.9）：進入風格定位前，依 Stage 1 的用途類型載入預設 craft 模組（見下方 Craft Rules 動態注入），讓品質限制參與方向形成，不等 DESIGN.md 寫完才讀。

呼叫順序：

1. **Skill `awesome-design-md`**（若有安裝）— 比對 brief 與 design library 找 3 個最相近的參考案例
2. **Skill `frontend-design`** — 取出對應的 aesthetic-direction 模板

**設計方向顧問 Fallback**（v1.5 P7.2）：若無品牌 context 且 brief 模糊（「做個好看的」「幫我設計」「不知道要什麼風格」），觸發設計方向顧問模式。Read `~/.claude/skills/starter-components/references/design-philosophies.md` 載入 20 種設計哲學 × 5 流派 + 4 Phase 顧問流程。推薦 3 個差異化方向（**必須來自 3 個不同流派**），使用者選定後回到 Stage 3。

**場景模板推薦**（v1.5 P7.11）：顧問模式推薦設計方向時，一併 `Read ~/.claude/skills/starter-components/references/scene-templates.md` 推薦適用的場景模板（deck 10 種 / page 7 種 / app 5 種），按選定哲學流派篩選 3-5 個最適合的場景。

**跳過條件**：已有明確風格參考 / 使用者已說清方向 / 小修改（Visual Thesis 不受跳過條件影響，deck/page mode 必交）

#### 客戶素材盤點（試行，展示型 deck/page；app mode 另見本節末）

立視覺主張之前，先從已提供的資料列出這個客戶或這堂課才有的東西。來源：taste-skill v2 盤點步驟。

1. **列什麼**：建議 3 到 5 項，不設下限——真實案例、工作物件（表單、看板、晨會流程）、流程限制（輪值、每週結算、離線作業）、受眾情境、客戶的專有用語。每項註明來源（brief、客戶檔案、會議紀錄）與打算用在哪個母題或哪一頁。沒有合適素材就寫出缺口，不湊數、不編造。
2. **接到視覺主張**：隱喻與三個母題至少一項由這張清單衍生，並寫出對應關係。
3. **替換測試**：把客戶或課程換成同業或上一堂課，概念與母題若仍完全適用，判定為通用樣板，退回重寫。
4. **驗收看有沒有改變成品**：視覺主張指得出素材來源、slide plan 指得出使用位置；只列清單沒影響設計，不算完成。
5. **試行範圍**：先用在下一份課程簡報，效果寫進製作紀錄後再定稿。固定色盤與字體不受影響，盤點只影響案例、圖解、母題與敘事。

**輸出**：併入 `aesthetic-direction.md`，放在 Visual Thesis 段之前。

**app mode 的業務物件盤點**：不套上面的隱喻、母題、替換測試與試行範圍，只盤點三件，寫進 DESIGN.md：
1. 畫面處理的業務物件與欄位，數值附單位。
2. 客戶的專有用語：標籤與空白狀態用「待客戶回覆」「停機中」這類用語，不用「項目」「紀錄」「狀態」這類通用名詞。
3. 能支援工作的元件（例如能源的用電流向、物業的待處理報修佇列）。不要求每個產品都發明獨有元件；平台色票與字體已固定的專案照平台，不另從產品世界取底色與字體。

#### Visual Thesis（v1.8 P10.1，deck/page mode 必交）

風格方向選定後、進 Stage 3 前，必須立「視覺主張」：具名概念（≤10 字）＋一句隱喻＋三個母題＋情緒曲線＋首尾呼應方式。規格與範本 → `Read ~/.claude/skills/starter-components/references/deck-art-direction.md` §1。

- **Gate**：後續任何視覺決策（配色/版型/插畫/元件）必須能一句話回扣概念名，否則不得進 Stage 3。
- **跨模型共筆（可選）**：概念發想可請另一個模型（不同廠牌更好）取 2-3 個候選概念，主腦裁決後落檔，並記下候選與裁決理由。
- 有風格沒故事＝通用模板——aesthetic direction 只回答「長什麼樣」，Visual Thesis 回答「為什麼長這樣」。

**輸出**：`reference-list.md` + `aesthetic-direction.md` + Visual Thesis 段（併入 aesthetic-direction.md 或獨立 `visual-thesis.md`）

**Checkpoint**：列 3 個風格選項給使用者選 + 呈客戶素材盤點（試行）與 Visual Thesis 五欄 → 等 ✅ 確認方向

---

### [3/7] 📐 設計系統（v1.3.1 §19 mode-conditional）

#### 資料頁設計依據預載（v1.8.4，page/app mode 條件式；依據 v1.1）
page 或 app mode 且 brief 屬資料頁／儀表板／營運後台／清單頁（訊號詞：KPI、報表、趨勢、清單、篩選、匯出、後台、看板、dashboard）時觸發。
寫 DESIGN.md 前先 `Read ~/.claude/skills/starter-components/references/info-dashboard-basis.md`。
依其第一、二節設計密度型後台，加五項必備元素：數字等寬右對齊、資料新鮮度註記、漲跌與狀態不靠色塊當唯一訊號、清單頁四件套（期間切換、附筆數篩選、匯出、分頁）、資料誠實（零與缺值、變化值、比較基準、合計對得上）。
寫 DESIGN.md 前另在筆記寫三行：這個畫面先回答的問題、今天資料裡最需要注意的一件事、最常做的動作放在哪裡。驗收看資訊層級能不能讓使用者先找到答案，不規定哪個區塊面積最大。
對外介紹頁走其第五節克制路線。
專案若已有定版的模組級畫面規範（例如能源管理模組的畫面呈現規範），一律以該規範為準，本依據只補充。
deck mode 不觸發。

#### Mode 行為表（§19.2）

| Mode | 預設路徑 | 行為描述 | Override flag |
|---|---|---|---|
| `deck` | **shortcut**（主腦快速寫）| 依 brief 選用 `starters/` 內對應的 `DESIGN.md` 作為基底（可用 starter：chenxi-liuli、chenxi-liuli-light、consulting-professional、corporate-warm、editorial-minimal、tech-dark）。再依 brief + aesthetic-direction.md 補齊 `.design/DESIGN.md`（Google YAML frontmatter + `## Framework Context` + `## Components`）+ lint | `--full-design-consultation` |
| `page` | **shortcut**（主腦快速寫）| 同上 | `--full-design-consultation` |
| `app` | **shortcut**（主腦較重寫）| 主腦讀 brief + framework_context → 寫 DESIGN.md + 列入 `## Components` 主要 component variants | `--full-design-consultation`（建議用於長期維護產品）|
| `system` | **必跑 design-consultation 6-Phase**（選用的外部技能，未安裝時略過：已安裝則 `Read ~/.claude/skills/gstack/design-consultation/SKILL.md` 照做） | 完整 Phase 0 preamble + Phase 1 product context + Phase 2 research + Phase 3 SAFE/RISK + Phase 4 drill-down（條件式）+ Phase 5 preview HTML + Phase 6 DESIGN.md | `--shortcut`（需發 warning：「shortcut 將跳過 visual artifact 生成，僅建議用於迭代既有 design system」）|
| `migrate` | **主腦比對** | 目前沒有對應技能；主腦讀既有 `.design/DESIGN.md` 與新 spec，產 `migration-plan.md` | — |

#### Shortcut 路徑必跑的最低品質門檻（§19.3 三項）

走 shortcut 路徑時 **仍須** 完成：

1. **DESIGN.md 結構符合 9-section schema**（v1.7 P9.6）：YAML frontmatter 符合 Google lint + Markdown body 9 section（Visual Theme / Color Palette / Typography / Components / Layout / Depth & Motion / Do & Don't / Responsive / Agent Prompt Guide）順序正確。參照 `references/design-md-schema.md`
2. **跑 anti-slop-review lint**：`npx @google/design.md@0.1.1 lint .design/DESIGN.md` → 0 critical / 0 warning（warning 必修）
3. **C1 摘要包含「跳過 design-consultation 的理由」**：寫入 `.checkpoints/1-to-3.md`

#### Art Direction Contract + Slide Plan（v1.8 P10.2，deck mode 必交；page mode 縮減版）

DESIGN.md 管 token 合法性，contract 管美術意圖——兩者並存。完整規格 → `Read ~/.claude/skills/starter-components/references/deck-art-direction.md` §2/§3。

1. **`.design/art-direction.md`**：Typography Scale 鎖定（封面 72–96px / 頁標 48–64px / 投影內文 ≥28px / 註記 ≥22px；同層級字差 ≤2px；禁縮字塞內容）＋ 語意色盤（5–7 色一色一義、主色支配、語意互斥）＋ Layout Primitives（8–10 種版型詞彙，Stage 5 只准用清單內版型）＋ 元件詞彙 ＋ 文案 register（consulting / educational-warm / product）＋ 讀者先驗（zero / practitioner / expert，承 Stage 1 brief，§2.5.2）＋ Keep/Change/Do-not-copy。
2. **`working/slide_plan_v001.md`**：每頁列版型（必須來自 primitives 清單）＋標題＋存在目的＋插畫需求。節奏預檢：單一版型連續 ≤2 頁、每 4 頁一次構圖轉折、情緒曲線有高峰＋首尾呼應。reader_prior = zero 時另守 §3 Gate 4：每頁只引入一個新概念、每頁有圖像位置（v1.8.3 P11.2）。
3. **Gate**：contract 色盤與 DESIGN.md token 值一致（alias 接線）；slide plan 每頁能回扣 Visual Thesis。
   - **page mode 區塊大綱（2026-10-18）**：縮減版 contract 要附區塊大綱，每個區塊寫一行「主張＋證據」（這一區要讓讀者相信什麼、憑什麼）；寫不出主張的區塊刪掉，避免照抄「主視覺、標誌牆、三個特色、見證、價格、行動按鈕」的固定順序。簡報不加這道關卡，沿用 slide plan 的「存在目的」與內容忠實度鎖定。
4. **C1 人審包**（deck mode）：客戶素材盤點（試行）＋Visual Thesis 五欄＋contract 色盤表＋primitives 清單＋slide plan 全文（reader_prior = zero 時加 `## Terms` 術語對照表），使用者 ✅ 才准進 Stage 4——設計前審一次，比交付後重做便宜十倍。

#### Lint 自動修復斷路器（§19.3.1）

第 2 項可能遇 contrast / orphaned token / broken ref 等需迭代修補的 warning。為避免無限迴圈耗盡 token：

- **3-attempt 上限**：對單一 warning 嘗試自動修復最多 3 次
- 超過 3 次仍 fail → 立即停止、保留當前 warning、寫入 C1 摘要的「未解 lint warning 清單」（含 warning code / message / 嘗試過的修復策略）
- **轉交人類決定**：
  - sync 模式：AskUserQuestion 列出剩餘 warning + 建議「✅ 接受並進 stage 4 / 🔄 暫停由我手動改 / ⏪ 改走 --full-design-consultation 重來」
  - async 模式：依 §20.3 預設取 ✅ 接受並進 stage 4，但 timeout 推進記錄中明確標註「**含未解 lint warning N 條**」加重提示
- **C1 摘要硬性要求**：含「未解 warning 數」欄位（即使為 0）

#### Full skill chain 路徑必產的 visual artifact（§19.4）

mode = `system` 或使用 `--full-design-consultation` 時，**必產**：

1. `.design/preview.html`（design-consultation Phase 5 自包含 + fonts + palette + components + mockups + light/dark）
2. `.design/preview-light.png` + `.design/preview-dark.png`（Playwright 截圖）
3. `.design/design-proposal.md`（Phase 3 SAFE/RISK breakdown，至少 3 risks）

若 Phase 5 preview 失敗 → checkpoint 警示但不阻斷，標註 `visual_artifact_status: "failed"`。

**輸出**：`.design/DESIGN.md`（Google design.md 格式 + `## Framework Context` section + `## Components` 不可空）

**Checkpoint**：展示 DESIGN.md 摘要 → 等 ✅ 確認（async 模式：5 min timeout → 取 ✅，但若有未解 lint warning 必標註）

#### Content Fidelity Lock（v1.4-short §24.3 P6.2，deck / page mode shortcut 必跑）

`deck` / `page` mode shortcut 路徑寫 DESIGN.md / index.html 時，**事實層必須 lock**，避免主腦在 Stage 3 改寫客戶名 / 產品名 / 數字（實務上曾發生改寫導致失真）。

**Lock 1 — Source-of-Truth 引用清單**：DESIGN.md 開頭加 `## Sources` 段，列本案資料源（客戶提供文件路徑 / 報價單 / SOW / 對話節錄含時間戳）。

**Deck 署名接線**：deck-gates 的署名與變體規則改由設定檔定義（見 `skills/starter-components/scripts/` 的設定檔），預設不檢查署名。若設定檔啟用署名檢查，把實際必有署名寫進 Facts，禁用字串寫 `## Forbidden Strings`，並同步產 `<成品.html>.gates.json`；未定署名只記為待確認，不把佔位輸出到成品。

**Lock 2 — 事實層條目對照表**：DESIGN.md 加 `## Facts` 段，三欄 Markdown table（`類型 | 內容 | 來源`）：

```markdown
## Facts

| 類型 | 內容 | 來源 |
|---|---|---|
| 客戶 PM | 王小明 | 客戶提供文件 line 12 |
| 機聯網主機 | 工業電腦 IPC | 報價單 line 8 |
| 啟動日期 | 2026-04-29 | 會議紀錄 |
```

主腦在寫 index.html 時**必須引用 Facts 表格條目**，禁止繞過寫不同的字。

**Lock 3 — fact-check.mjs cross-check**（Stage 3 結束前必跑）：

```bash
node ~/.claude/skills/starter-components/tools/fact-check.mjs \
  --design .design/DESIGN.md \
  --html index.html \
  --output verify/fact-check.json \
  --llm-provider gemini   # 或 codex / none
```

工具兩段：
- **Part A — Positive match（純字串可驗，必跑）**：parse Facts 表格 → grep `htmlToPlainText(html)` 確認所有條目均出現。缺漏 → finding（severity: high）。
- **Part B — Reverse check via LLM（NLP entity extraction，必跑）**：spawn Gemini / Codex CLI 抽 HTML 中所有人名 / 公司名 / 產品名 / 具體日期 / 金額數字，比對 Facts 表，列出「在 HTML 但不在 Facts」的 entity（severity: med，給人複核）。
- 結果寫入 `verify/fact-check.json`：含 `positive_match` + `reverse_check` + `verdict`（PASS / FAIL / NEEDS_HUMAN_REVIEW）+ exit code（0 / 1 / 2）。

**Verdict 行為**：
- Part A FAIL（exit 1）→ 主腦補資料 → 再跑 → 直到 A PASS
- Part B unknown 列 → 不直接 fail（exit 2 NEEDS_HUMAN_REVIEW），但**要求使用者 / 主腦逐項確認後才結束 Stage 3**
- LLM 失敗（network / parse 錯）→ verdict NEEDS_HUMAN_REVIEW（不阻斷 pipeline）

**Lock 4 — 術語對照表（v1.8.3 P11.3，reader_prior = zero 時必加；其他值可省）**：DESIGN.md 加 `## Terms` 段，三欄 Markdown table（`術語 | 白話說法（同頁使用的比喻） | 首次出現頁`）。規則：

- 簡報正文出現的每個專業術語、縮寫、英文工程用語都要有一列；白話說法必須在術語首次出現的同一頁可見，不得只放講者備註。
- 一頁只准新增一列（每頁一個新概念）；同頁要引入第二個術語＝拆頁，或改用比喻不點名術語。
- 本輪為人審項目：C1 與 Stage 6 逐頁對照 Terms 表，不跑腳本。日後若加機械輔助，只做「術語有沒有列入表」的 grep 提示，合不合格仍由人判——字串比對當 gate 會被反話繞過且每加嚴一次就多誤殺（實務經驗）。

**Build-metadata 加欄位**（Stage 5 寫入時）：

```json
"fidelity_lock": {
  "facts_table_count": 7,
  "positive_match_passed": true,
  "reverse_check_provider": "<另一個模型>",
  "reverse_check_unknown_count": 4,
  "verdict": "NEEDS_HUMAN_REVIEW",
  "fact_check_json": "verify/fact-check.json"
}
```

`system` / `app` mode 走完整 design-consultation，不適用本段（`system` 設計層審查內建較重事實層機制；`app` brief 偏 product 不偏事實複述）。`migrate` mode 同 system 例外。

#### Craft Rules 動態注入（v1.9，取代 v1.7 的寫法）

載入分兩次：

1. **Stage 2 開始前**：依 Stage 1 的用途類型載入預設模組。
	1. 共同四模組，每個用途類型都載入：`anti-ai-slop`、`typography`、`color`、`motion`。
	2. 展示型再加 `taste-layout`；實用型再加 `interaction`。混合頁兩者都載入，`taste-layout` 只作用於明列的展示區，`interaction` 只作用於明列的工作區。展示型不載入 `interaction`，實用型不載入 `taste-layout`。
2. **Stage 3 寫完 DESIGN.md 後**：讀 `.design/DESIGN.md` frontmatter 的 `craft.requires`，補載預設清單以外的模組。`craft.requires` 只能增加，不能用空陣列或漏列移除共同四模組；名稱不在可用模組裡就顯示錯誤並停下，不安靜略過。
3. 載入的規則在 Stage 5 實作與 Stage 6 品質檢核都是約束。模組裡寫明「只適用某類型或某輸出」的條款，照它的適用範圍執行。
4. 載入 `motion` 不代表一定要做動畫；靜態輸出可標「不適用」，但要確認內容不依賴動畫才看得到。

**可用模組**：`anti-ai-slop`（7 sins＋延伸）／`typography`（字體配對與層級）／`color`（對比度、語義色與表面層次）／`motion`（動態用途、時長、減少動態替代）／`taste-layout`（展示型的版面參考）／`interaction`（互動決策：選項精簡、結尾優先、沿用慣例、事實紀錄不預填、提醒只講真實後果）
**索引**：`~/.claude/skills/starter-components/craft/INDEX.md`

**C1 摘要加欄位**：`usage_type`、`usage_type_reason`、`craft_rules_loaded`（實際載入清單）、`craft_not_applicable`（不適用的條款與理由）。

---

### 🧹 C1 — Context Summary & Clear（§5.4）

觸發時機：stage 3 結束。

**動作**：
1. 摘要階段 1-3 為 ≤ 500 字 Markdown，寫入 `<project_root>/.checkpoints/1-to-3.md`
2. 內容包含：
   - 最終 mode + brief
   - 用途類型與理由、實際載入的 craft 模組與不適用的條款（v1.9）
   - 選定風格名稱 + 3 個關鍵設計理由
   - DESIGN.md 路徑 + framework_context 摘要（react / next / tailwind 版本）
   - **shortcut 路徑紀錄**（v1.3.1 §19.3 第 3 項）：若 stage 3 走 shortcut → 寫入「跳過 design-consultation 的理由」（mode = deck/page/app + brief 性質）
   - **未解 lint warning 數**（v1.3.1 §19.3.1 必填）：即使為 0 也寫；> 0 時列每條 warning code + 嘗試過的修復策略
   - **async timeout 推進歷史**（若有，v1.3.1 §20.3.3）：表列哪幾個 [N/7] stage 走 timeout default + 預設值內容
3. 保留：決策結果（選定風格、最終 tokens、framework_context、user 偏好、未解 lint warning、timeout 推進歷史）

**冷啟動 resume**：使用者中斷後 `/fe-design --resume` → 讀 `.checkpoints/1-to-3.md` 恢復脈絡。

---

### [4/7] 🧱 Scaffold 初始化

本階段完整規格已拆至子檔（v1.8.4 拆檔，2026-08-27）。進入本階段時先 `Read ~/.claude/skills/starter-components/references/fe-design-stages/stage-4-scaffold.md` 載入全文再執行。

---

### [5/7] ✍️ 實作

依 mode 呼叫主力 skill：

| Mode | 主力 Skill | 輸出 |
|---|---|---|
| `deck` | `Skill frontend-slides`（簡報字級以所選 preset 的固定 px 為準；frontend-slides 只借控制器與版面規則，其 vw 字級不用，clamp 亦不用） | `index.html`（≥ 12 slides）+ `styles.css` + `scripts.js`（若需）|
| `page` | `Skill frontend-design` | `index.html`（responsive）+ component 拆分（若 ≥ 3 區塊）|
| `app` | `Skill frontend-design` | `components/*.tsx` 多檔（含 entry + sub-components）|
| `system` | （跳過）| — |
| `migrate` | 主腦依 `migration-plan.md` 直接改 | `migration-plan.md` + diff patches |

#### Deck mode 工序反轉：Contact Sheet 先行（v1.8 P10.3）

**先產全副低保真、審節奏，後精修單頁**——逐頁精修再回頭看整體＝返工。完整規格 → `Read ~/.claude/skills/starter-components/references/rendered-qa.md` §1。

1. 依 slide plan 產全部頁面低保真版（版型骨架＋真標題＋灰塊佔位圖）→ Playwright 截圖拼 contact sheet。
2. 節奏審查通過才准精修：版型連續 ≤2 頁、全副重複率 ≤25%、每 4 頁一次構圖轉折、標題塊/頁碼位置跨頁一致。
3. 節奏不過 → 回改 slide plan 換版型，不是加裝飾補救。

#### Deck mode 產圖工序（v1.8 P10.4，可選）

slide plan 標記插畫需求的頁面，可用你手邊的生圖工具產圖。完整規格 → `Read ~/.claude/skills/starter-components/references/imagegen-direction.md`。

- **鐵律**：圖片不承擔理解、情緒或節奏功能就不生成。全幅插畫每 20 頁限 2–4 張（封面/章節轉場/情緒高峰/結尾）。
- contract → style tokens（媒材/筆觸/色盤/光線/人物比例/鏡位/留白方向/禁用項）→ 每張 prompt <350 字元、圖內零中文字。
- 產圖：用你手邊的生圖工具；提示詞要求工具原文照送、只產一次、不准自行修圖。資產落 `assets/image2/s{NN}_{purpose}_v{版本}.png` ＋ 同名 `.prompt.txt`。
- Gate：Read 逐張驗收＋全副色溫筆觸一致性並排比對；單張重跑上限 3 次，超過改排版方案。

#### Deck mode Optical Pass（v1.8 P10.3，精修完成後逐頁）

中文微排版檢查——渲染後逐頁修：中文孤字斷行、行首標點懸掛、視覺置中（optical center）、並排基線對齊、圖文張力、safe area 溢出。檢項表 → `rendered-qa.md` §2。

#### app mode 子組件拆分策略（§10 P3.6）

當 mode = `app` 且實作中：

1. 偵測單一組件 `.tsx` 行數即將超過 **300 行**（含 imports / 註解；不含外部 type definition）
2. 觸發 AskUserQuestion：
   - 列出建議的拆分點（依職責切：data fetch / business logic / presentation / sub-component）
   - 預覽拆分後的目錄樹（`components/<name>/index.tsx` + `<name>.types.ts` + `<name>.hooks.ts` + `<name>.parts/*.tsx`）
3. 等使用者 ✅ 批准 → 才拆
4. 使用者拒絕 → 繼續單檔但在檔案頂部加 JSX-合法的 JS 區塊註解 `/* TODO: refactor (>300 lines) — 使用者拒拆分於 <ISO timestamp> */`（**禁用 HTML 註解 `<!-- -->`，TSX 內非合法 token；若不便落在組件檔，則改寫 sidecar `<components>/<name>.refactor-notes.md`**）

**Junior Designer 雙階段**（v1.5 P7.6）：

觸發條件（非所有案都需要）：
- 新品牌 / 首次合作 → 強制 Junior pass
- 小修改 / 已有前版 / 使用者說「直接做」 → 跳過
- async 訊息通道模式 → 跳過（timeout 推進會卡住互動）

若觸發：
- **[5a/7] Junior pass**：
  - 寫 assumptions 列表（「我理解你要...」）
  - 寫 placeholders（灰色方塊 + 文字標籤代替真實內容）
  - 寫 reasoning comments（「選這個布局因為...」）
  - **Checkpoint**：show 給使用者，等 ✅ → 進入 Full pass / 🔄 修正方向
- **[5b/7] Full pass**：
  - 填入真實內容、做 variations
  - 加 Tweaks（見下方）
  - 中途再 show 一次進度
  - **Checkpoint**：最終確認

若跳過 → 直接走 Full pass（現有行為）。

**Tweaks 即時變體**（v1.5 P7.4）：Stage 5 實作時，主腦預設為每案加 2-3 個 tweaks（除非使用者拒絕）。使用 `scaffolds/tweaks_panel.mjs`，參照 `references/tweaks-system.md`。deck mode：配色 + 字級 + 密度；page mode：配色 + layout；app mode：light/dark + 字級。

**真圖優先策略**（v1.5 P7.9）：app/page mode 實作時若 brief 涉及 UI mock、landing page、demo 或 prototype，`Read ~/.claude/skills/starter-components/references/image-sourcing.md` 載入真圖搜尋策略，優先使用客戶品牌資產或 Unsplash/Pexels 免費商用圖，禁止在正式交付物使用 placeholder。

**動畫設計語法**（v1.5 P7.10）：deck mode 實作需要動畫場景（slide 進場、數據揭示、重點強調）時，`Read ~/.claude/skills/starter-components/references/animation-design.md` 載入時間函數 / 持續時間指引 / 效能避坑 / PPTX 相容性注意事項。

**PPTX 約束預載**（v1.5 P7.1a）：若 brief 指定需 PPTX 交付 → 實作前 `Read ~/.claude/skills/starter-components/references/editable-pptx.md` 載入 7 條 HTML 約束，確保產出的 HTML 對語義級翻譯器友善。

**Checkpoint**：列出實作檔案清單 + LoC 統計 → 等 ✅ 繼續

---

### [6/7] 🔍 品質檢核

**Deck mode 必跑機械關卡**：`bash ~/.claude/skills/starter-components/scripts/deck-gates.sh delivery/deck.html <變體> [--config <設定檔>]`，變體取設定檔 `variants` 裡的名稱（預設設定 `scripts/deck-gates.config.json` 提供「提案」「課程」「內訓」「個人品牌」四個不檢查署名的變體）；**非零即擋交付**，修正後重跑。檢查簡體字（opencc 七組過度轉換例外）、AI 標註、硬用詞及 h1–h3 句首或句中的疑問詞（署名檢查依設定檔）；兩支輔助詞表另列位置，命中不擋但交付說明逐處附保留理由。兩份 HTML 各跑，報告附退出碼；工具執行失敗不能視為 PASS。


兩道關卡（順序固定）：

1. **自動關卡** — 跑 `/anti-slop <project_root> --recursive`：
   - 第一層 `npx @google/design.md@0.1.1 lint`（8 條結構規則）
   - 第二層 `scan.py`（22 條繁中 trope，含 v1.4 新增 trope-17 字體配對、v1.9 新增 trope-18 全屬性過渡與 trope-19 減少動態候選；4 條結構型規則列為未實作）
   - 第三層 `scan.py scan_seven_sins()`（7 sins P0 硬擋，v1.7 P9.4a/b 新增，CSS token-aware）：
     - Sin #1 Tailwind indigo escape（token-aware）
     - Sin #2 Two-stop trust gradient
     - Sin #3 Emoji as feature icons
     - Sin #4 Font conflict（token-aware，依賴 token_resolver.py）
     - Sin #5 Rounded card + colored left-border
     - Sin #6 Invented metrics
     - Sin #7 Filler copy（lorem ipsum / placeholder）
   - 嚴重度 ≥ warning 直接列入待修；7 sins 為 P0 severity 必修
2. **互動關卡** — （選用的外部技能，未安裝時略過此步）已安裝則 `Read ~/.claude/skills/gstack/design-review/SKILL.md` 並照做：
   - **進入前必做**：`Read ~/.claude/skills/anti-slop-review/trope-catalog.md` 載入 22 條 trope 名稱+破解法到 working memory（取代 P3.8 原規劃的 symlink 機制 — design-review 為 AUTO-GENERATED 不可直接改檔）
   - 對 critical / warning finding 做設計師視角複核（融合 trope catalog + 7 sins 視角）
   - 輸出 patch suggestion
   - **讀者先驗人審**（v1.8.3 P11.3，reader_prior = zero 時必做）：逐頁對照 DESIGN.md `## Terms` 表——每個術語同頁有白話說法、每頁新概念 ≤1、每頁有圖像位置、可見文字一眼讀完（建議 ≤40 CJK，不含標題；超過即拆頁或改圖）。不跑腳本，結果寫入 C2 摘要 `reader_prior_audit` 欄位（PASS，或待修頁碼清單）。

3. **量化評審**（v1.5 P7.5，可選）— 使用者請求「評審」「打分」或主腦主動質檢時觸發。Read `~/.claude/skills/starter-components/references/design-critique.md` 載入 5 維度評審框架（哲學一致性 20% / 視覺層級 25% / 細節執行 25% / 功能性 20% / 創新性 10%）。使用 `scaffolds/radar_chart.mjs` 產 SVG 雷達圖。輸出 Keep / Fix / Quick Wins。

#### 網頁與應用介面的渲染檢查（v1.9，page／app mode 必跑）

源碼掃描證明不了實際體驗，這一節補上 page 與 app 的渲染檢查，不另立「精緻度流程」。結果分三類寫進報告：程式檢查通過、人看通過、未驗證（附原因）。

1. **掃描範圍要寫清楚**：檢查器的目錄掃描收 `.md`、`.mdx`、`.html`、`.htm`、`.jsx`、`.tsx`、`.css`、`.scss`、`.js`、`.mjs`、`.ts`、`.vue`、`.svelte`，並排除 `node_modules`、`dist`、`build` 等依賴與產物目錄；trope-18 抓 `transition: all` 與 Tailwind `transition-all`，trope-19 標出「有動畫卻沒有減少動態宣告」的候選檔（要在瀏覽器確認）。4 條結構型規則（trope-03、13、15、16）尚未實作，報告會列為「未實作、未檢查」，這幾項要靠渲染檢查與人看補上。交付報告要寫明掃描範圍與沒有自動檢查到的項目；掃不到不能算通過。
2. **瀏覽器量測**：至少 1440×900 與 390×844 兩種寬度，確認沒有水平捲動、文字沒有被裁切、主要內容可見；切換 `prefers-reduced-motion: reduce` 後內容仍能閱讀與操作；可關閉的元件（對話框、抽屜、選單）開、關、重開與中途中斷後狀態正確。
3. **人看渲染結果**：留白節奏、層級、構圖與背景、動態是否交代因果，對照已載入的 craft 規則判斷；不以效果數量或固定數值代替判斷。
4. **操作文案**：操作按鈕是否清楚表達動作、有沒有沒資訊價值的裝飾眉標，由人審判定，程式只提供候選。

#### 渲染後四道 Gate（v1.8 P10.5，deck mode 必跑，依序）

源碼掃描抓不到視覺問題——三 gate 全部看渲染結果，全部掛 §19.3.1 的 3-attempt 斷路器。完整規格 → `Read ~/.claude/skills/starter-components/references/rendered-qa.md` §3。

1. **Gate 1 — Contact-sheet Rhythm 複審**：精修後重產 contact sheet 再審一次（精修常把節奏改掉）→ `qa/contact_sheet_vNNN.png`。
2. **Gate 2 — Typography/Overflow 自動量測**：Playwright 逐頁量測 computed style → `qa/typography_audit_vNNN.json`。內文 <28px、溢出 slide bounds → FAIL；同層級字差 >2px、行長超標、對齊偏差 >2px → WARN。
3. **Gate 3 — 100% 截圖人工評審＋渲染後 Slop Diagnostic**：逐頁截圖全數過眼（不抽樣），對照 10 項渲染後 slop 指標（tech gradient / generic indigo / repetitive feature grid / accent rails / glass blur / monument stats / icon toppers / center-stack / default Inter / surface mismatch）→ `qa/visual_review_vNNN.md` 必含「Slop diagnostic: N/10」，N>0 修復重跑。
4. **Gate 4 — Viewport Fit 實測**：非 1920 視窗實測（至少 1440×900＋1280×800）× JS 開/關 × `deck.html`＋`delivery/deck-standalone.html`：水平無溢出、逐頁 slide rect 落在 viewport 內；另驗 print 安全（`emulateMedia('print')` 下 deck 容器 computed zoom 必須為 1，保護 pdf-export）。量測對象消失（slide 數 0／deck 容器不存在）＝FAIL，防 selector 改名造成假通過 → `qa/viewport_fit_report.json`。完整規格 → `rendered-qa.md` §3。

與既有機制關係：anti-slop 三層掃源碼照跑，硬 gate 審渲染，互補不取代；design-review 互動關卡以 Gate 3 的截圖為輸入。

**Scaffold 繞過強制留痕**：deck mode 未採 starter scaffold（`build-metadata.json` 的 `scaffolds` 為自製或空值）時，必須附 Gate 4 通過紀錄＋等效縮放實作說明，缺一＝交付 FAIL。實務經驗：繞過 scaffold 又未補縮放時，其餘 gate 全部通過仍可能在瀏覽器溢出。

**渲染後對抗式審查（可選，建議做）**：deck mode 交付前，可請另一個模型（不同廠牌更好）對「本次改動＋新增 gate 腳本」做對抗式審查，把審查意見與修正記錄下來（例如寫入 `build-metadata.json` 的 `cross_model_review` 欄位）；FAIL 後自修建議回送 confirm 輪（C1 瘦身格式）至 PASS 再交付。

**輸出**：`anti-slop-report.md` + 修復 diff + `qa/contact_sheet_vNNN.png` + `qa/typography_audit_vNNN.json` + `qa/visual_review_vNNN.md` + `qa/viewport_fit_report.json` +（可選）`design-critique-report.md`

**Checkpoint（C2 人審包，deck mode）**：contact sheet 圖＋typography audit 摘要＋slop diagnostic 分數＋finding 清單 → 等 ✅ 套用所有修補 / 🔄 部分修補 / ⏪ 回 stage 5

---

### 🧹 C2 — Context Summary & Clear（§5.4）

觸發時機：stage 6 結束。

**動作**：
1. 摘要階段 4-6 為 ≤ 800 字，寫入 `<project_root>/.checkpoints/4-to-6.md`
2. 內容包含：
   - scaffold 採用清單 + 對應 variant（deck/page mode 走 scaffolds 基底版時不報 fallback）
   - 最終實作檔案路徑清單（含 LoC）
   - anti-slop report 摘要（critical 數 / warning 數 / 已修 issue 清單）
   - design-review patch 是否全採納
   - **async timeout 推進歷史**（若 stage 4-6 期間有 timeout 推進）：續 C1 表單繼續記錄
3. 保留：最終實作檔案路徑、report 摘要、未修 issue（若有）、timeout 推進歷史

---

### [7/7] ✅ 驗證與交付

本階段完整規格已拆至子檔（v1.8.4 拆檔，2026-08-27）。進入本階段時先 `Read ~/.claude/skills/starter-components/references/fe-design-stages/stage-7-verify-deliver.md` 載入全文再執行。

---

## 中斷恢復（resume）

```
/fe-design --resume
```

行為：
1. 讀 `<project_root>/.checkpoints/1-to-3.md`（若存在）→ 恢復 stage 1-3 決策
2. 讀 `<project_root>/.checkpoints/4-to-6.md`（若存在）→ 恢復 stage 4-6 產出清單
3. 從最後一個未完成 stage 繼續

---

## 失敗處理

- 任一 Skill 不可用（未安裝）→ 回報缺哪個 skill + 提供 install 指令
- npx fallback：`npx @google/design.md@0.1.1` 失敗時 → **若** `~/.claude/skills/anti-slop-review/vendored/google-design.md-0.1.1.tgz` **存在則** fallback 到 vendored tarball（截至本期 P1.12 已落地，308KB）；若 vendored 缺失則直接回報 stage 失敗，不再降級
- Pipeline 中途任何錯誤 → 寫 `<project_root>/.checkpoints/error-{stage}.md` 含 stack trace + 上一個成功 stage 的 state，方便 `--resume`

### Skill 降級表

| Skill | 用途 | 降級行為 |
|---|---|---|
| `design-review`（gstack） | Stage 6 互動關卡 | 降級為純 anti-slop 三層掃描 + 人工確認。Stage 6 只跑自動關卡，跳過互動關卡，在 Checkpoint 明確標註「⚠ design-review 不可用，僅完成自動 anti-slop 三層掃描」 |
| `design-consultation` | Stage 3 full chain | 降級為 shortcut 路徑（主腦快速寫 DESIGN.md），在 C1 摘要標註「⚠ design-consultation 不可用，已走 shortcut」 |
| `awesome-design-md` | Stage 2 參考比對 | **永久可選**。不可用時跳過參考比對，直接由主腦基於 brief + starters/ 推薦風格方向 |
| `frontend-slides` | Stage 5 deck mode | 降級為主腦直接寫 HTML，在 Checkpoint 標註 |
| `frontend-design` | Stage 5 page/app mode | 降級為主腦直接寫 HTML/components，在 Checkpoint 標註 |

### migrate mode 驗證步驟

migrate mode 產出 `delivery/migration-plan.md` + `delivery/patches/*.diff` 後，必須執行：

1. **語法檢查**：每個 `.diff` 檔案用 `git apply --check` 驗證可套用（不實際套用）
2. **衝突偵測**：對目標 codebase 執行 `git apply --3way --check` 偵測衝突
3. **影響範圍統計**：`diffstat` 或等效方式列出影響檔案數 + 增刪行數
4. 結果寫入 build-metadata.json 的 `migration.validation` 欄位：
   ```json
   "validation": {
     "patches_valid": 2,
     "patches_conflict": 0,
     "files_affected": 5,
     "lines_added": 42,
     "lines_removed": 18
   }
   ```

---

## 與其他 skill 的關係

- **starter-components**：stage 4 取 scaffold
- **anti-slop-review**：stage 6 第一層
- **design-context-import**：stage 3 system mode 主任務
- **frontend-slides**：stage 5 deck mode 主任務
- **frontend-design / frontend-patterns**（選用的外部技能，未安裝時由主模型直接實作）：stage 5 page/app mode 主任務
- **design-consultation**：stage 3 新建 DESIGN.md
- **design-review**（gstack）：stage 6 第二層

# Deck Art Direction — Visual Thesis 與 Art Direction Contract

> 版本：v1.8 P10.1/P10.2；v1.8.3 P11 讀者先驗（§2.5.2／§3 Gate 4／§4）
> 觸發時機：deck / page mode Stage 2（Visual Thesis）與 Stage 3（Art Direction Contract + slide plan）
> 核心命題：anti-slop 防爛，本文件造好。通過 lint ≠ 通過 art direction。

---

## 1. Visual Thesis（Stage 2 必交，deck/page mode）

每案在選定風格方向後，必須先立「視覺主張」——一個具名概念，統攝之後所有視覺決策。有風格沒故事＝通用模板。

**先做客戶素材盤點（2026-10-18 試行）**：立視覺主張前，先列 3 到 5 項這個客戶或這堂課才有的東西（真實案例、工作物件、流程限制、受眾情境、專有用語），每項寫來源與打算用在哪個母題或哪一頁；隱喻與三個母題至少一項由此衍生。把客戶或課程換成同業或上一堂課仍完全適用，就退回重寫。完整規則見 `~/.claude/commands/fe-design.md` Stage 2「客戶素材盤點」。

```markdown
## 客戶素材盤點
| 素材 | 來源 | 用在哪裡 |
|---|---|---|
| ＿＿ | ＿＿ | ＿＿（母題／第幾頁） |
- 缺口：＿＿（沒有合適素材時寫出來，不湊數）
- 替換測試：換成＿＿仍適用嗎？＿＿
```

**必填五欄**：

```markdown
## Visual Thesis
- 概念名：＿＿（≤10 字，例：「成長地圖・Field Notes for Growing」）
- 一句隱喻：把＿＿比喻成＿＿（例：把新班級比喻成一趟共同探索）
- 三個母題：＿＿、＿＿、＿＿（貫穿全副的視覺 motif，例：路徑、紙張標籤、手繪底線）
- 情緒曲線：開場＿＿ → 中段＿＿ → 高峰＿＿ → 收尾＿＿
- 首尾呼應：封面與結尾頁如何互相呼應（例：同一條路，封面走進、結尾走遠）
```

**Gate（進 Stage 3 的門檻）**：任何後續視覺決策（配色、版型、插畫、元件）都必須能一句話回扣概念名。回扣不了的裝飾＝砍掉。

**第二意見（可選）**：概念發想可請另一個模型提 2-3 個候選概念，由主導者裁決後落檔。

## 2. Art Direction Contract（Stage 3 必交，deck mode；page mode 適用縮減版）

落檔 `<project_root>/.design/art-direction.md`，與 DESIGN.md 並存（DESIGN.md 管 token 合法性，contract 管美術意圖）。

### 2.1 Typography Scale 鎖定（投影場景）

| 層級 | 字級範圍 | 說明 |
|---|---|---|
| 封面主標 | 72–96px | 高對比粗體、窄行寬（≤12 CJK 字/行） |
| 頁面標題 | 48–64px | editorial 層級，搭配 eyebrow |
| Eyebrow / section tag | 18–24px | 字距放寬（letterspacing 0.08–0.15em），可用英文 |
| 投影內文 | ≥28px（28–34px） | **硬底線，不得靠縮字塞內容** |
| 註記 / 來源 | ≥22px | 低對比但可讀 |

- 中文 tracking 0–0.02em、行高 1.25–1.5。
- 同層級文字尺寸偏差 ≤2px（跨頁一致）。
- 內容塞不下 → 拆頁或改版型（表格/時間軸/checklist），**禁止縮字**。

### 2.2 語意色盤（一色一義）

- 5–7 色，每色附語意角色，禁止裝飾性輪替：

```markdown
| Token | 色值 | 語意 | 用在 |
|---|---|---|---|
| paper | #F2EBDD | 底 | 主背景 |
| ink | #20312B | 主體 | 內文 |
| forest | #1F5A49 | 信任與結構 | 標題、路線節點 |
| persimmon | #E56B3F | 提醒與行動 | 警示頁、CTA |
| mustard | #D8AA43 | 亮點 | 徽章、強調 |
```

- **主色支配**：每頁一色主導，不給每張卡片等權色彩。
- **語意互斥**：同一色不得跨越互斥語意（信任色不得拿去做警示）。
- 與 DESIGN.md token 的關係：contract 色盤是語意層，DESIGN.md `--color-*` 是實作層，兩邊值必須一致（alias 接線）。

### 2.3 Layout Primitives（8–10 種版型詞彙）

每案 contract 列出本副簡報允許的版型清單（從下表選＋自創），Stage 5 只准用清單內版型：

全版圖像頁 / 非對稱編輯頁 / 路線圖 / 橫向時間軸 / 環形流程 / 一天流程 / 表格頁 / 宣言頁（big statement + chips）/ 雙欄對照 / 三窗卡 / checklist 頁 / 警示頁（全色塊）/ 人物檔案頁 / 入場互動頁

### 2.4 元件詞彙與 Motion

- 元件詞彙：列 4–6 個貫穿全副的小元件（例：紙張標籤、手繪底線、圓章、路徑節點、重點貼紙）。**避免每頁都塞等寬卡片**——這是 AI deck 第一 slop。
- Motion：低調進場、尊重 `prefers-reduced-motion`；鍵盤導航照 deck_stage.js 內建。

### 2.5 文案語氣（voice register）

| Register | 適用 | 標題句式 |
|---|---|---|
| consulting | 商業提案、顧問簡報 | pyramid action title（結論句 ≤18 CJK，§24.11 全套適用） |
| educational-warm | 教學、班親會、內訓 | 教學點句（「成績是三扇窗，不是標籤」型——有觀點、有溫度，仍是結論不是名詞） |
| product | 產品發表、demo | 利益句（使用者得到什麼） |

- **noun-only 標題禁令全域不變**（「XX 概況」「XX 簡介」不准）。
- §24.11 的 `slide_action_titles[]` frontmatter + verify 腳本僅 consulting register 強制；其他 register 標題仍需通過「是結論不是 label」人審。

### 2.5.1 Facts 表寫法（Content Fidelity Lock 配套，2026-07-11 首案實證）

DESIGN.md 的 `## Facts` 表條目必須是**原子字串**——即簡報成品中逐字出現的詞（`Acme Console`、`config.yaml`、`BotFather`），不是敘述句（「Acme Console on Windows 平台」）。`fact-check.mjs` Part A 是逐字 grep：敘述句必然 0 命中假 FAIL。一列一原子，複合事實拆多列。

### 2.5.2 讀者先驗（reader prior，v1.8.3 P11，2026-08-23）

register 管「用什麼口氣說」，讀者先驗管「讀者對本題懂多少」，兩軸互不重疊、相乘使用。值承 Stage 1 brief 的 `reader_prior`，寫進 contract。

| 值 | 聽眾 | 文案與版面規則 |
|---|---|---|
| `zero` | 對主題一無所知 | 下列四條全守 |
| `practitioner` | 做這行、不做這題 | 術語首次出現白話帶一句；不強制圖先於字 |
| `expert` | 本題專家 | 只守 noun-only 禁令與 Typography Scale |

**`zero` 四條**（源自 eli5 一句話核心：把讀者當成對主題一無所知的人，用大圖、少字解釋）：
1. **每頁一個新概念**：一頁只引入一個新術語或新觀念；要講第二個就拆頁。slide plan 完整版「新概念」欄必填。
2. **術語同頁講白**：術語首次出現的同一頁，用生活比喻或一句白話說清楚，不得留到講者備註或下一頁；全部術語列入 DESIGN.md `## Terms` 表（fe-design Lock 4）。
3. **圖先於字**：每頁至少一個圖像位置（插畫、圖表、示意），primitives 挑圖像主導的版型；可見文字以一眼讀完為準（建議 ≤40 CJK，不含標題），超過就拆頁或把文字變成圖。
4. **標題不帶未定義術語**：全 register 通用；consulting 的 action title、educational-warm 的教學點句都不得含同頁未白話定義的術語。

**相乘範例**：企業通識課＝educational-warm × zero；給不懂 AI 的老闆做顧問提案＝consulting × zero；內部工程評審＝product × practitioner。

**不要做的事**：把 `zero` 當成「講得幼稚」——它限制的是術語密度與圖文比，不是語氣；語氣仍由 register 決定。

### 2.6 Keep / Change / Do-not-copy

使用者給了風格參考（截圖、舊版、他人作品）時必填：Keep（借的可控特質）/ Change（要改寫的）/ Do-not-copy（人名、日期、費用數字、既有卡片格）。與 Content Fidelity Lock 並行不衝突：Facts 表管事實、本段管視覺借用。

## 3. Slide Plan（Stage 3 必交，deck mode）

落檔 `<project_root>/working/slide_plan_v001.md`。每頁一行起步（輕量版），高規格案用完整欄位：

**輕量版**（每頁一行）：`N. 版型｜標題｜這頁存在的目的（一句）`

**完整版欄位**：頁碼 / 版型（必須來自 contract primitives 清單）/ 標題 / 可見文字 / 新概念（本頁引入的唯一新術語，reader_prior = zero 時必填；無則寫「無」）/ 講者備註 / 互動點 / 視覺元素 / 插畫需求（有→給用途與構圖槽位，見 imagegen-direction.md）/ 情緒曲線位置

**Gate**：
1. 每頁有存在目的（資訊、決策、情緒三選一），純裝飾頁砍掉。
2. 全副節奏預檢：單一版型連續 ≤2 頁；每 4 頁至少一次構圖轉折（全幅↔留白、深底↔淺底、圖像↔排版）。
3. 情緒曲線至少一個高峰頁（全色塊警示頁或深底宣言頁）＋首尾呼應成立。
4. **reader_prior = zero 時**（v1.8.3）：每頁「新概念」≤1 且 `## Terms` 表有對應白話說法；每頁有圖像位置；可見文字一眼讀完（建議 ≤40 CJK）。人審項目，不跑腳本。

## 3.5 單側版型的平衡元素（實務 pattern）

步驟卡頁、FAQ 頁這類「內容天然靠左」的版型，右半容易出現 40%+ 死空間（contact sheet 上一眼可見）。解法不是塞更多字，而是放一個**低調的母題水印**（例如 8% 透明度的大型母題圖形）——填空間、扣概念、不搶焦點。契約的三母題就是水印素材庫。

## 4. C1 人審包

Stage 3 結束的 C1 checkpoint，deck mode 必須呈給使用者：Visual Thesis 五欄 + contract 色盤表 + primitives 清單 + slide plan 全文（reader_prior = zero 時加 `## Terms` 術語對照表）。使用者 ✅ 才准進 Stage 4/5——**設計前審一次，比交付後重做便宜十倍**。

<!-- anti-slop-skip: trope-01,trope-02,trope-03,trope-04,trope-05,trope-06,trope-07,trope-08,trope-09,trope-10,trope-11,trope-12,trope-13,trope-14,trope-15,trope-16,trope-17,trope-18,trope-19,trope-20,trope-21,trope-22 -->

# Anti-slop Trope Catalog（22 條繁中重寫版）

> 本目錄為繁體中文原創寫作，分類參考公開的設計資源。fe-design v1.4-short 同步版（§17 新增中文字體配對檢測）。
>
> **本檔含完整壞範例 → 自身豁免於 anti-slop scan**（檔頭 `<!-- anti-slop-skip -->` marker 標記）。

每條 trope 含：特徵 / why-slop / 破解法 / 偵測 hint / severity。

---

## 01. 彩色邊條卡片（Colored Side Border Card）

**特徵**：卡片左、右、上或行內起訖邊使用粗彩邊（至少 3px 或 0.2rem/em），同檔至少三筆。

**為什麼是 slop**：AI 的「強調」直覺反應就是加彩邊。一個畫面常出現 4-6 個顏色不同的邊條，視覺嘈雜且分類意義稀薄。

**範例（壞）**：
```html
<div class="border-l-4 border-l-blue-500 pl-4">
  <h3>功能 A</h3>
</div>
<div class="border-l-4 border-l-green-500 pl-4">
  <h3>功能 B</h3>
</div>
```

**破解法**：用背景色區塊（`bg-blue-50`）或留白排版取代彩邊；留白比顏色更有級別感。

**偵測 hint**：Tailwind 同側 border-l/t/r-N（N≥3）配對彩色 class；CSS 邊條簡寫由 css_value 判斷，支援 hex、var()、rgb(a)、hsl(a) 與 CSS 具名色。排除 border-bottom、分開寫的寬度屬性、透明及指定中性色名稱，min_count 維持 3。

**Severity**：`warning`

---

## 02. 過度漸層（Multi-stop Hero Gradient）

**特徵**：hero 區三色以上的漸層（紫 → 粉 → 橙是 2023 招牌）。

**為什麼是 slop**：視覺雜訊高、傳達資訊力弱、與品牌通常不對齊。

**範例（壞）**：
```html
<section class="bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400">
```

**破解法**：單色漸層、雙色 subtle 漸層（< 8% 對比差）、純色塊配大量留白。

**研究觀察**：獲獎網站研究裡，漸層填色在高分網站占 22%、低分網站 52%（相關觀察，限制見文末「研究數字對照」）。

**偵測 hint**：Tailwind from-via-to 或 CSS linear-gradient 4+ stops。regex 的 exclude_properties 逐筆排除 mask-image、-webkit-mask-image、mask、-webkit-mask 值內的漸層；同檔背景漸層照常計次，行號保留。

**Severity**：`warning`

---

## 03. 三欄置中 benefit card（Three-Column Centered Benefit）

**特徵**：三等分 grid、每欄一個 icon（圓形/方形）置中、標題置中、短文案置中。

**為什麼是 slop**：千篇一律的 marketing 套版，看完記不住任何一條的內容。

**範例（壞）**：
```html
<div class="grid grid-cols-3 gap-8 text-center">
  <div><Icon /><h3>速度</h3><p>...</p></div>
  <div><Icon /><h3>安全</h3><p>...</p></div>
  <div><Icon /><h3>成本</h3><p>...</p></div>
</div>
```

**破解法**：時間軸（Timeline）/ 對照表（Comparison）/ 大圖配 3 條子標 / 縱向 stepper。

**研究觀察**：獲獎網站研究裡，頂著圖示的功能卡片在高分網站占 1%、低分網站 28%（相關觀察，限制見文末「研究數字對照」）。

**偵測 hint**：regex `grid-cols-3.*text-center` + 內部 ≥3 個 `<Icon`/`<svg`

**Severity**：`warning`

---

## 04. 預設 Inter 字型（Default Inter Everything）

**特徵**：整站只用 Inter Regular，沒有 serif 對比、沒有 display 字重。

**為什麼是 slop**：Inter 是極好字型，但「只用 Inter」= 沒有設計主張。

**範例（壞）**：
```css
body, h1, h2, h3, button { font-family: Inter, sans-serif; font-weight: 400; }
```

**破解法**：標題換 serif（Playfair / Source Serif）/ 標題用 Inter 700+ 對比 body 400 / 用 display variant（`font-feature-settings: "ss01"`）。

**偵測 hint**：regex `font-family.*Inter` + 全文無 `serif|Playfair|Source\s?Serif|Georgia` 等

**Severity**：`info`

---

## 05. 所有元素置中（Everything Centered）

**特徵**：Hero / feature / cta 全置中。

**為什麼是 slop**：無視覺張力，動線單調。

**範例（壞）**：
```html
<section class="flex flex-col items-center justify-center text-center">
  <h1>標題</h1>
  <p>...</p>
  <button>CTA</button>
</section>
```

**破解法**：左對齊主文 + 右側錯位元素 / 左圖右文 / Z 字形動線。

**偵測 hint**：HTML 大區塊內 `text-center` + `items-center` + `mx-auto` 同時出現 3+ 次

**Severity**：`warning`

---

## 06. 過度圓角（Over-rounded Everything）

**特徵**：所有元素 `rounded-lg` 以上（甚至 `rounded-2xl`），按鈕、卡片、輸入框、圖片全部一致。

**為什麼是 slop**：統一到失去識別。原本 sharp 對比 round 才有觸覺暗示。

**範例（壞）**：
```html
<button class="rounded-2xl">
<img class="rounded-2xl">
<input class="rounded-2xl">
```

**破解法**：0~4px sharp 的 + 12px+ round 的混用（按鈕 round、卡片 sharp、image 0px）。

**補註（2026-10-18）**：taste-skill v2 指出 9～16px 的「軟圓角」是低分網站的預設，高分網站的按鈕 52% 直角、23% 全圓。本條仍以「所有元素一致的大圓角」為準，不另立規則；人審時一併看圓角是否有意圖。

**偵測 hint**：regex `rounded-(2xl|3xl|full)` 出現次數 ≥ 5

**Severity**：`warning`

---

## 07. Emoji 當 icon（Emoji-as-Icon）

**特徵**：🚀 💡 ✨ 🎯 等 emoji 作為主要 icon。

**為什麼是 slop**：正式度不夠、跨平台 render 不一致、無法控制 stroke / weight。

**範例（壞）**：
```html
<h3>🚀 速度提升</h3>
<h3>💡 智慧分析</h3>
```

**破解法**：用 SVG icon set（lucide / heroicons / phosphor）、保持 stroke 一致性。

**偵測 hint**：regex emoji unicode 範圍 `[\u{1F300}-\u{1F9FF}]` 出現在 `<h\d>` 或 `<button>`

**Severity**：`warning`

---

## 08. Linear gradient border（Gradient Card Border）

**特徵**：卡片外框漸層（CSS `border-image: linear-gradient`）。

**為什麼是 slop**：2022 年初 Linear 風格大流行後的氾濫產物。

**範例（壞）**：
```css
.card { border: 2px solid; border-image: linear-gradient(45deg, #f472b6, #818cf8) 1; }
```

**破解法**：用 box-shadow 構造邊框質感、純色細邊（1px）、subtle inset shadow。

**偵測 hint**：regex `border-image.*linear-gradient` 或 `bg-gradient.*p-\[\d+px\]` (作邊框 trick)

**Severity**：`warning`

---

## 09. 浮誇詞彙（Hyperbolic Marketing Lingo）

**特徵**：revolutionary / seamless / cutting-edge / unleash / transform / next-generation / game-changer。

**為什麼是 slop**：空洞行銷腔，讀者反射性跳過。

**範例（壞）**：
```html
<h1>Revolutionary AI that transforms your workflow</h1>
<p>Unleash next-generation productivity</p>
```

**破解法**：改用具體數字（"省 40 分鐘/天"）/ 動詞（"自動產生報表"）/ 結果（"接通客戶後 3 秒回應"）。

**偵測 hint**：regex word-list `\b(revolutionary|seamless|cutting-edge|unleash|game-changer|next-generation|paradigm|disruptive)\b` (case-insensitive)

**Severity**：`warning`

---

## 10. 過量 hover 特效（Hover-Effect Overload）

**特徵**：每個元素都有 `hover:scale-105` / `hover:shadow-2xl` / `hover:bg-...`，且同時 active。

**為什麼是 slop**：視覺噪音、注意力被稀釋、實際 CTA 看不出來。

**範例（壞）**：
```html
<div class="hover:scale-105 hover:shadow-2xl transition-all">
<div class="hover:scale-105 hover:shadow-2xl transition-all">
<div class="hover:scale-105 hover:shadow-2xl transition-all">
```

**破解法**：聚焦 — 只主 CTA + 主要連結加 hover；其他維持靜態。

**偵測 hint**：regex `hover:scale-` 或 `hover:shadow-` 在單一檔案出現次數 ≥ 8

**Severity**：`info`

---

## 11. 假資料人名陳腔（Stock Persona Names）

**特徵**：John Doe / Jane Smith / 王小明 / 陳大華 + 預設 avatar 灰色頭像。

**為什麼是 slop**：testimonial / about us 區塊裝飾感重，無真實感，使用者識別出「demo data」就降低信任。

**範例（壞）**：
```html
<div class="testimonial">
  <img src="/avatars/default.png">
  <h4>John Doe</h4>
  <p>"Great product!"</p>
</div>
```

**破解法**：真實客戶（拿過授權）/ 留白「您的客戶」+ 上傳 placeholder / 完全不放 avatar，只放公司 logo。

**偵測 hint**：regex `\b(John Doe|Jane Smith|王小明|陳大華|Tom Cook|Lindsay Walton|Anonymous)\b` 或 `default.png|avatar.png|placeholder.jpg`

**Severity**：`info`

---

## 12. Dashboard 無意義圖表（Decorative Dashboard Charts）

**特徵**：隨機曲線 / 漸層 bar chart / 大百分比數字 + 「+24%」綠箭頭。

**為什麼是 slop**：純裝飾性圖表，看完不知道要 action 什麼。

**範例（壞）**：
```html
<div class="chart">
  <SparkLine data={randomData} />
  <span class="text-4xl">+24%</span>
</div>
```

**破解法**：放真實資料 / 刻意極簡（單一數字大 + 1 行 context）/ 不放圖表，改 bullet 重點。

**偵測 hint**：regex `randomData|fakeData|mockData|generateChart` 或 `<SparkLine|<Chart` 但無 `data={\w+(?!Random|Fake|Mock)`

**Severity**：`info`

---

## 13. 堆疊式 feature list（Pile-up Feature List）

**特徵**：✓ ✓ ✓ + 一行短句 × 8+，無分組、無優先序。

**為什麼是 slop**：無層次，讀者看到第 4 條就放棄。

**範例（壞）**：
```html
<ul>
  <li>✓ 高速處理</li>
  <li>✓ 安全加密</li>
  <li>✓ 24/7 支援</li>
  <li>✓ 雲端同步</li>
  <li>✓ AI 分析</li>
  <li>✓ 跨平台</li>
  <li>✓ 開放 API</li>
  <li>✓ 客製化</li>
</ul>
```

**破解法**：分組（核心 / 進階 / 整合）+ 對比表（vs 競爭者）+ 標粗 1-2 條主打 / 圖文排版。

**偵測 hint**：regex `<li>.*[✓✔]` 或 `<li>` 連續 ≥ 8 條且每條 < 30 字

**Severity**：`info`

---

## 14. Hero 巨型標題（Oversized Hero Headline）

**特徵**：h1 96px+ + 一句話、無子標、無 CTA 直接連著結束。

**為什麼是 slop**：視覺重量都壓在一句話，缺乏脈絡，使用者不知道下一步。

**範例（壞）**：
```html
<h1 class="text-9xl">Build the future</h1>
```

**破解法**：標題（48-72px 適中）+ 承諾子標（具體價值 + 2-3 行）+ CTA 三層次。

**偵測 hint**：regex `<h1.*text-(8xl|9xl)|font-size:\s*(96|112|128|144)px` + 後 100 字內無 `<h2|<p`

**Severity**：`warning`

---

## 15. 全 font-weight: 400（Single-Weight Typography）

**特徵**：全站僅一種字重（通常 400），標題 / body / button 都一樣。

**為什麼是 slop**：無視覺階層，重點不出來。

**範例（壞）**：
```css
* { font-weight: 400; }
```

**破解法**：300 light（標題襯托）/ 500 medium（body）/ 700 bold（標題、按鈕、強調）混用。

**偵測 hint**：grep 整檔 `font-weight` 值，若全是同一數值 → 觸發

**Severity**：`info`

---

## 16. 過度嵌套 Container（Excessive Container Nesting）

**特徵**：為對齊不斷套 `<div>`，單一區塊嵌套 ≥ 6 層；連續 `flex items-center justify-center` 重複類名。

**為什麼是 slop**：AI 處理 layout 對齊習慣堆 wrapper。DOM 極難維護、影響效能、可訪性差。

**範例（壞）**：
```html
<div class="flex items-center justify-center">
  <div class="flex items-center justify-center">
    <div class="flex items-center justify-center">
      <div class="flex items-center justify-center">
        <div class="flex flex-col">
          <div class="flex">
            <span>內容</span>
```

**破解法**：用 CSS Grid `grid-template-areas` / `place-items: center` 一次解；HTML 嵌套深度 ≤ 5；同父層下重複 className 去重。

**偵測 hint**：HTML AST 分析：`<div>` 嵌套深度 > 5；或 regex 連續 3+ 行 `flex items-center justify-center`

**Severity**：`warning`

---

## 17. CJK 明體+黑體混搭 / CJK Mincho+Gothic Mismatch（fe-design v1.4 §24.2 新增）

**現象**：同一 selector 內混用「CJK 明體（Noto Serif TC / 思源宋體）」+「CJK 黑體（Noto Sans TC / 思源黑體）」，違反中文界基本法則。

> Latin 字型（Source Serif 4 / Inter）已從 patterns.json trope-17 名單移除，避免合法方案 D（matched serif pair display + matched sans pair body）誤觸。詳見 v1.4-short P6.1 audit。

**為什麼是 slop**：

中文字體配對基本法則（justfont / TeSA / BFA / 思源黑體官方）：
- ✅ 「襯線體配明體、無襯線體配黑體」（同類字族搭配）
- ✅ 「同字族不同字重」做標題/內文對比
- ❌ 不混搭「明體標題 + 黑體內文」— 西方 consulting deck（McKinsey serif headline + sans body）的英文邏輯**不適用**繁中

來源：justfont《Word 預設中英搭配有什麼問題？》、《2024 推薦中文字體》；TeSA / BFA 簡報專欄。

**破解法**（4 種方案，依受眾選）：
- **A 西方 consulting**（serif + sans）— 僅當主受眾為英文用戶（`mixed-bilingual.css`，需 `--ignore-trope trope-17` 跳過）
- **B 全黑體 + 字重對比** ⭐ 中文簡報通用預設（`consulting-mono-sans.css`）
- **C 全明體 + 字重對比** — 年報 / 學術（`editorial-serif.css`）
- **D 全黑體 + 不同字族** — 進階質感（`premium-mixed-sans.css`）

**偵測 hint**：patterns.json trope-17 含 4 條 regex（正反向順序對 + CSS 變數對），同行 500 字符跨度，不跨行降低誤觸風險。

**Severity**：`warning`

**對應 design-tokens-presets**：`~/.claude/skills/starter-components/design-tokens-presets/`（4 套 CSS 對應方案 A/B/C/D）

---

## 18. 全屬性過渡（Transition All）

**特徵**：CSS 使用 `transition: all`、`transition-property: all`，或 Tailwind 使用獨立 `transition-all` class。

**為什麼是 slop**：全屬性過渡會讓原本沒有動態用途的屬性也加入過渡，增加非預期動態。

**破解法**：明列過渡屬性，例如 transform 與 opacity。

**偵測 hint**：CSS 宣告含獨立 `all` 值，包含逗號分隔清單；Tailwind 允許 `hover:transition-all`、`!transition-all`、`transition-all!`。utility 左側須為空白、引號、反引號、冒號或驚嘆號（或檔案開頭），右側須為空白、引號、反引號或檔案結尾；不匹配 `transition-all-xxx`、`my-transition-all`、`transition-alligator`、`transition-all/50`。這是字串候選比對，不解析 CSS 或 class AST。

**Severity**：`warning`

---

## 19. 缺少減少動態宣告（候選，需在瀏覽器切換減少動態設定確認）

**特徵**：整份檔案含 `@keyframes`、`animation:` 或 `transition:`，卻沒有 `prefers-reduced-motion`。

**為什麼提示**：動態可能沒有減少動態替代；單檔字串比對無法確認實際瀏覽器行為，因此只列候選。

**破解法**：候選，需在瀏覽器切換減少動態設定確認；提供靜態或低動態替代，保留操作結果與必要資訊。

**偵測 hint**：沿用整份檔案的 `exclusion_pattern` 豁免，大小寫不敏感。同檔出現偏好名稱即可豁免，不代表替代行為正確；跨檔樣式不合併，其他檔案的偏好宣告不會豁免本檔。

**Severity**：`info`（候選）

---

## 20. 奶油色底（Cream Background Candidate）

**特徵**：background、background-color，或名稱含 bg、background、paper、surface、base 的 CSS 變數使用暖色淺底。

**為什麼提示**：奶油底可能是預設風格，也可能符合咖啡等主題，只列候選，需人判斷。

**範例（候選）**：
```css
background: #fdf3e2;
--paper: #fdf6e3;
background: rgba(255, 250, 242, 0.95);
```

**破解法**：核對背景色與內容、品牌的關係；有意採用時用 --skip-tropes trope-20 或檔內 skip 標記排除。

**偵測 hint**：css_value 的 cream_background 將明示 hex、rgb(a)、hsl(a) 轉成 HSL，色相 30–60 度、亮度至少 90%、飽和度至少 20%；純白、灰白、偏粉排除。不解析變數引用。min_count=1，單一背景宣告就可能覆蓋整頁。

**Severity**：`info`（候選，需人判斷）

---

## 21. 彩色光暈（Colored Glow Candidate）

**特徵**：box-shadow、text-shadow 或 filter: drop-shadow() 的位移為 0 0、模糊至少 20px，使用彩色而非黑白灰。

**為什麼提示**：大範圍彩色光暈容易變成裝飾預設，但也可能是狀態或品牌效果，需人工確認用途。

**範例（候選）**：
```css
box-shadow: 0 0 40px rgba(124, 58, 237, 0.5);
```

**破解法**：確認用途，必要時降低模糊與彩度；刻意採用可跳過 trope-21。

**偵測 hint**：css_value 的 colored_glow 支援多層陰影，每宣告最多計一次；明示色碼 RGB 最大最小差小於 16 視為灰，黑白灰具名色不算，未解析的 var() 不算。min_count=1。

**Severity**：`info`（候選，需人判斷）

---

## 22. 裝飾條紋背景（Decorative Stripe Background Candidate）

**特徵**：background 或 background-image 使用 repeating-linear-gradient 或 repeating-radial-gradient。

**為什麼提示**：重複紋理可能增加雜訊，也可能服務主題或資料呈現，需人判斷。

**範例（候選）**：
```css
background: repeating-linear-gradient(to bottom, transparent 0, transparent calc(12.5% - 4px), #5a3620 calc(12.5% - 4px), #5a3620 12.5%);
```

**破解法**：確認條紋與內容的關係，必要時改為單色背景；有意採用可跳過 trope-22。

**偵測 hint**：regex 只看 background / background-image 宣告內的重複線性或放射漸層，不比對 mask 與自訂屬性。min_count=1。

**Severity**：`info`（候選，需人判斷）

---

結構型樣式 trope-03、trope-13、trope-15、trope-16 尚未實作，文字與 JSON 報告會另列「未實作、未檢查」。trope-03 與 trope-16 的 regex 部分仍執行，不能把結構型未檢查解讀為通過。

## 研究數字對照（觀察不是規則）

來源：Leonxlnx/taste-skill v2 `references/research.md` 第 6 節。2026-10-05 擷取 One Page Love 與 Awwwards 每日網站共 248 站，由 21 位模型評審照 Awwwards 權重評分；可量測的高分組（7.5 分以上）82 站、低分組（6.5 分以下）23 站。限制：單日擷取、模型評分而非真人評審、低分組樣本小、只看歐美公開行銷頁；只能說明「常一起出現」，不能證明因果，也不能外推到簡報與後台。

| 做法 | 高分網站 | 低分網站 | 對應條目 |
|---|---|---|---|
| 頂著圖示的功能卡片 | 1% | 28% | 03 |
| 漸層填色 | 22% | 52% | 02、08 |
| 靜止物件加陰影 | 24% | 48% | 10（人審留意） |
| 小字距大寫標籤 | 16% | 57% | 人審留意 |

**不列為反樣板**：等寬字標籤（高分 44%、低分 24%）、01／02／03 編號（38%、21%）在高分網站反而更常見，細線（61%、52%）沒有明顯差異。taste-skill 禁用它們是作者的個人品味，本目錄不跟進；簡報的頁碼編號與資料頁的表格線照常使用。

## Severity 對照原則

| Level | 何時用 | 處置 |
|---|---|---|
| `critical` | 結構壞掉 / 不可見 / 完全違反 spec | 必修才能 ship |
| `warning` | 設計品質明顯下降 | 建議修，可帶入 PR review |
| `info` | 風格偏好性 | 提示、不阻塞 |
| `nit` | 雞毛蒜皮 | 略過或自動修 |

22 條 trope 預設 severity 多為 `warning`，但 fe-design v1.2 雙層架構合併時可 local remap（例如 trope 04 預設 Inter 在「標準 dashboard」場景可降為 `nit`）。

---

## 來源 & License

本目錄為繁體中文原創寫作，分類參考公開的設計資源：

- [VoltAgent awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
- [Google design.md](https://github.com/google-labs-code/design.md)（google-labs-code/design.md，Apache-2.0）
- [taste-skill](https://github.com/Leonxlnx/taste-skill)（Leonxlnx/taste-skill，MIT；「研究數字對照」段落的出處）

可自由使用、修改、分發，但建議保留 attribution（例如「來自 anti-slop-review skill v1.0 — Kevin Du, 2026-04-25」）。

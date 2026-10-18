# Craft Rule: Anti-AI-Slop

> 模組：anti-ai-slop
> 嚴重度：P0（必修，不通過則 pipeline FAIL）
> 預設：✅ 未宣告 craft.requires 時自動注入

## 7 Cardinal Sins

AI 生成前端設計時最常犯的 7 個致命陷阱。每一條都會被 `scan.py scan_seven_sins()` 自動偵測。

### Sin #1 — Tailwind Indigo Escape

**症狀**：用 `#6366f1` 或其變體作為 accent/primary 色。
**為什麼是問題**：這是 Tailwind 預設 indigo-500，幾乎所有 AI 生成的 UI 都長一樣。
**偵測**：比對 7 色（#6366f1 / #4f46e5 / #4338ca / #3730a3 / #8b5cf6 / #7c3aed / #a855f7）出現在非 `:root` token 定義區。
**修復**：使用 `var(--accent)` 引用 DESIGN.md 定義的品牌色。

### Sin #2 — Two-Stop Trust Gradient

**症狀**：`linear-gradient` 含 purple→blue、blue→cyan、indigo→pink 組合。
**為什麼是問題**：這是 AI 生成的「信任感」漸層的通用配方，已被過度使用。
**偵測**：regex 比對 gradient 方向 + 色值組合。
**修復**：改用 solid surface + 有意圖的色彩對比。

### Sin #3 — Emoji as Feature Icons

**症狀**：emoji 出現在 `<h*>` / `<button>` / `<li>` / `[class*="icon"]` 內。
**為什麼是問題**：emoji 在不同 OS/版本下 render 不一致，降低專業感。
**偵測**：emoji codepoint 在語義 HTML 元素內。
**修復**：使用 SVG icon（1.6-1.8px stroke，例如 Lucide / Heroicons）。

### Sin #4 — Font Conflict（Token-Aware）

**症狀**：DESIGN.md 定義 `--font-display` 為 serif，但 h1/h2 實際用了 Inter/Roboto/system-ui。
**為什麼是問題**：設計系統定義與實作脫節，token 形同虛設。
**偵測**：解析 DESIGN.md 的 typography token → 比對 HTML 中實際使用的 font-family。依賴 `token_resolver.py`。
**修復**：使用 `var(--font-display)` 引用 token。

### Sin #5 — Rounded Card + Colored Left-Border

**症狀**：`border-radius` + `border-left: 3-5px solid {color}` 同時出現在同一元素。
**為什麼是問題**：這是 AI 生成的「資訊卡片」最常見的視覺模式，已成為 AI slop 標記。
**偵測**：同元素同時含 border-radius 和 border-left。
**修復**：二選一——去圓角（sharp card + left border）或去邊條（rounded card，無邊條）。

### Sin #6 — Invented Metrics

**症狀**：`\d+[×x%]` 出現但無 `data-source` 標記或 Facts 表引用。
**為什麼是問題**：AI 容易編造看似權威的數據（「提升 300%」「節省 10× 時間」）。
**偵測**：regex 找數字宣稱 → 檢查是否有 `data-source` 屬性或 Facts 表條目。
**修復**：標記為 placeholder（`data-placeholder="true"`）或引用真實來源。

### Sin #7 — Filler Copy

**症狀**：lorem ipsum / "Feature One" / "placeholder text" / "sample content" / "Your content here"。
**為什麼是問題**：交付物不應含佔位文字。
**偵測**：字串比對常見 filler 片語。
**修復**：替換為真實內容（來自 brief / Facts 表 / 客戶資料）。

## 延伸規則

### 配色一致性
- 同一頁面不得出現超過 6 種非 token 定義的顏色
- 所有色值應引用 DESIGN.md token，禁止 hardcode hex

### 元件語義
- `<button>` 必須有 `type` 屬性
- interactive 元素必須有 `:hover` / `:focus` 狀態
- 裝飾性圖片必須有 `aria-hidden="true"` 或空 `alt=""`

### 字體回退
- CJK 字體必須有 fallback chain（至少 3 個候選）
- `font-display: swap` 必設（避免 FOIT）

### 操作文案
- 操作按鈕要清楚表達動作與必要受詞，例如「匯出報表」「送出審核」；分頁名稱、選項名稱不必硬改成動詞。
- 英文介面預設用 Sentence case，專有名詞與縮寫照正確寫法；中文不套大小寫規則。
- 不加沒有資訊價值的裝飾眉標（標題上方的小字標籤）與空泛宣稱；真實的分類、狀態、章節標籤，以及品牌頁上可核對的訴求可以保留。
- 這一節由人審判定，檢查器只能提供候選。


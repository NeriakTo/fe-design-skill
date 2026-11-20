---
name: anti-slop-review
description: 對 AI 產出的 HTML／JSX／DESIGN.md 與樣式、程式檔做規則化的去 AI 味（anti-slop）檢查：結構層跑 `npx @google/design.md@0.1.1 lint`（8 條規則），語義層跑 scan.py（22 條繁中 trope＋7 sins 硬擋）。由 /anti-slop 與 /fe-design 第 6 階段呼叫。
---

# anti-slop-review

## 用途

對 AI 生成的 HTML / JSX / DESIGN.md 與樣式、程式檔做規則化的去 AI 味檢查（anti-slop review），找出：
1. **結構層** slop（broken-ref / missing-primary / contrast-ratio < WCAG AA / orphaned-tokens / section-order …）— 透過 `npx @google/design.md@0.1.1 lint` 8 條 default rule
2. **語義層** slop（彩色邊條卡片 / 三欄置中 benefit card / Inter 預設 / 過度漸層 / 浮誇詞彙 …）— 透過自家 22 條繁中 trope（regex 與 CSS 值；未實作結構型樣式另列）

合併輸出 4 級報告：critical / warning / info / nit。

## 何時呼叫

- 啟動 `/anti-slop <target>` slash command
- pre-commit hook（前端類專案）
- CI pipeline 阻塞低品質 PR
- `/fe-design` orchestrator pipeline 第 6 階段「自動化視覺品質掃描」

## 雙層架構

```
┌──────────────────────────────────────────────┐
│ 第一層：結構層（npx @google/design.md lint）  │
│   - broken-ref（{path.to.token} 解析失敗）    │
│   - contrast-ratio（< WCAG AA 4.5:1）         │
│   - missing-primary / missing-typography      │
│   - missing-sections / orphaned-tokens        │
│   - section-order / token-summary             │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 第二層：語義層（scan.py 22 條繁中 trope）     │
│   - 彩色邊條卡片 / 過度漸層 / 三欄 benefit    │
│   - 預設 Inter 字型 / 全置中 / 過度圓角       │
│   - Emoji 當 icon / 漸層 border / 浮誇詞彙   │
│   - 過量 hover / 假資料人名 / 假 dashboard    │
│   - 堆疊 feature list / Hero 巨型標題         │
│   - 全 font-weight: 400 / 過度嵌套 Container  │
│   - CJK 字型混搭 / 全屬性過渡 / 減少動態候選 │
│   - 奶油色底 / 彩色光暈 / 裝飾條紋候選       │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 合併輸出：critical / warning / info / nit     │
└──────────────────────────────────────────────┘
```

> 已定義規則總數：**結構層 8 條＋語義層 22 條＝30 條**（Google `types.ts` 是 type scaffold，不算 rule），另有 7 sins 硬擋層。語義層有 4 個結構型樣式未實作，並非全部規則都已執行，詳見「掃描範圍與未檢查項目」。

## 檔案結構

```
anti-slop-review/
├── SKILL.md               (本檔)
├── trope-catalog.md       22 條繁中 trope 完整 catalog（特徵 / why-slop / 破解法）
├── design-md-rules.md     8 條 Google design.md lint rule 中文釋義
├── patterns.json          22 條 trope（26 個 regex＋3 個 CSS 值樣式＋4 個未實作結構型樣式）
├── scan.py                主程式（雙層合併輸出）
├── templates/
│   └── report-template.md 報告格式範本
└── LICENSE-APACHE-2.0     upstream 衍生 license（npx 接 Google CLI 所需）
```

## 使用方式

### CLI

```bash
# 對單一 HTML 檔
python ~/.claude/skills/anti-slop-review/scan.py /path/to/index.html

# 對 design.md（先跑結構層 lint 再跑 trope）
python ~/.claude/skills/anti-slop-review/scan.py /path/to/.design/DESIGN.md

# 對整個目錄遞迴
python ~/.claude/skills/anti-slop-review/scan.py /path/to/project/ --recursive

# 跳過結構層（npx 不可用時）
python ~/.claude/skills/anti-slop-review/scan.py /path/to/index.html --skip-design-md-lint
```

### Slash Command

```
/anti-slop /path/to/target
```

執行後會：
1. 偵測 target 類型（DESIGN.md / HTML / JSX / 目錄）
2. 對 DESIGN.md 跑結構層 lint
3. 對所有收集到的檔案跑語義層 trope scan（7 sins 僅 HTML/HTM/JSX/TSX）
4. 合併輸出，按 severity 排序

## 預熱（一次性）

首次使用前在 host 機器跑：

```bash
npm install -g @google/design.md@0.1.1
# 之後 npx 走本地 cache，避免 cold start 2-5 秒延遲
```

## Severity 對照

| 來源 | 原生 severity | scan.py 顯示 |
|---|---|---|
| Google `broken-ref` | error | **critical**（passthrough）|
| Google `contrast-ratio` | warning | **warning** |
| Google `missing-primary` / `missing-typography` | warning | **warning** |
| Google `orphaned-tokens` | warning | **nit**（local remap）|
| Google `section-order` | warning | **warning**（passthrough，不加嚴成 hard fail）|
| Google `missing-sections` | info | **info** |
| Google `token-summary` | info | **info** |
| 22 條繁中 trope | — | 各 trope 自定（見 patterns.json）|

## Upstream 鎖定

- **Repo**：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**：`8ecd4645b957e6a683a05fb9c79cd6c9028873d0`
- **npm package**：`@google/design.md@0.1.1`
- **License**：Apache-2.0（見 `./LICENSE-APACHE-2.0`）

## 相關文件

- `trope-catalog.md` 本目錄（22 條 trope 詳解）
- `design-md-rules.md` 本目錄（8 條結構規則中文釋義）

## 與其他 skill / command 的關係

- `/fe-design` orchestrator（`~/.claude/commands/fe-design.md`）：stage 6 第一層自動呼叫 `/anti-slop --recursive`
- `/anti-slop` slash command（`~/.claude/commands/anti-slop.md`）：本 skill 的單檔/單目錄入口
- `design-review`（gstack）：fe-design stage 6 第二層；該 skill 為 AUTO-GENERATED 不可直接改檔，因此 fe-design.md 在進入第二層前會 instruct Claude 先 `Read ~/.claude/skills/anti-slop-review/trope-catalog.md` 載入 22 條 trope 視角，再交給 design-review 做設計師複核（取代 v1.2 §10 P3.8 原規劃的 symlink 機制）
- `frontend-slides`：在 Related ECC Skills 段已加入本 skill / `/anti-slop` 作為交付前檢核工具

## 掃描範圍與未檢查項目

### CSS 值樣式與逐筆豁免

patterns.json 新增 `type: css_value`，由標準庫 `colorsys` 與宣告值候選解析器判斷三種 `rule`：

- `colored_border`：trope-01 的 CSS 簡寫；左、右、上、inline-start、inline-end，粗度至少 3px 或 0.2rem/em。接受 hex、var(--名稱)、rgb(a)、hsl(a) 與 CSS 具名色；具名色排除 transparent、currentColor、inherit、initial、unset、black、white、gray、grey、silver。Tailwind 另以 regex 配對同側 border-l/t/r-N 與彩色 class，N 至少 3。min_count 維持 3。
- `cream_background`：trope-20；只看 background、background-color 或名稱含 bg、background、paper、surface、base 的自訂屬性。明示 hex、rgb(a)（也接受 hsl(a)）轉成 HSL，色相 30–60 度、亮度至少 90%、飽和度至少 20%。min_count=1，因單一背景宣告即可涵蓋整頁。
- `colored_glow`：trope-21；box-shadow、text-shadow 或 filter 的 drop-shadow()，位移 0 0、模糊至少 20px，明示色碼 RGB 最大最小差至少 16，或彩色具名色。支援多層陰影，每個宣告最多計一次。

trope-22 用 regex 找 background / background-image 中的 repeating-linear-gradient 或 repeating-radial-gradient。trope-20～22 一律 info、min_count=1，是需人工判斷的候選。

宣告解析先決定樣式區域：以標準庫 `HTMLParser` 辨認到起始標籤、結束標籤、HTML 註解或宣告作為 HTML 判準；判斷前將 CSS 註解換成等長空白並保留換行，CSS `url()` 內嵌標記只是 URL 資料，以等長空白遮掉其中的角括號。HTML 只取每個 `<style>` 的內容及標籤內名稱恰好為 `style` 的屬性值，忽略 `<script>` 內容與其他文字。屬性在每個標籤內依序解析，支援單引號、雙引號及不加引號；外層引號依 HTML 規則結束，反斜線不能跳過它。

純 CSS 與 `<style>` 內容只解析大括號區塊內的宣告；以區塊深度走訪巢狀規則及 @media，選擇器及 @規則前導部分不當成宣告。但非 HTML 且全文沒有大括號時，整份當成一串宣告清單解析，以相容片段檔與既有測試。style 屬性本身是宣告清單。字串內及函式內的分號不結束值，字串遇未跳脫換行復原；註解換成等長空白並保留換行，所有位置與行號對應原文。各區域依序走訪、游標單向移動，宣告只解析一次並供全部 CSS 值規則與屬性排除共用，總時間與輸入長度成正比。

這是文字候選解析，並非完整 CSS AST 或瀏覽器計算樣式：不解析變數實際色值、calc() 粗度、色彩空間函式與繼承。奶油底僅判斷單一明示色值（可加 !important），不從圖片或漸層推估整片底色。光暈模糊值目前只接受 px。CSS 宣告解析不跨區塊或 HTML 屬性邊界；區域末尾未完成的反斜線跳脫會在邊界結束。此區域限制適用 CSS 值規則及 `exclude_properties`，既有 regex 規則仍掃描全文。只有內容出現指定標籤外形（`styled` 後接 `.`／`(`，或 `css`、`createGlobalStyle`、`keyframes`、`injectGlobal` 接反引號，允許既有泛型與空白）才啟動樣板辨識與遮蔽；未啟動時沿用原有區域解析，未配對反引號與連續三個以上反引號不作樣板分隔。JS／TS 帶標籤樣板字串也獨立納入樣式區域，與上述 HTML／純 CSS 判準並存：辨認 `styled.標籤名`、`styled(元件)`，以及前兩者接 `.attrs(...)`，支援標籤與反引號間的空白及泛型參數，泛型參數可含箭頭函式型別；另辨認 `css`、`createGlobalStyle`、`keyframes`、`injectGlobal`。區域從開頭反引號後到對應結尾反引號前，跳脫反引號不結束字串；最外層視為宣告清單，巢狀區塊也解析，選擇器與 @規則前導不解析。插值內的帶標籤樣板也納入樣式區域，其餘插值內容遮成空白；`${...}` 插值支援巢狀大括號、字串與任意層巢狀樣板字串，遮蔽時保持等長並保留換行，維持原文位置；一般無標籤樣板字串不納入，`style={{ ... }}` 物件寫法維持現狀。已知限制：說明文件若沒有大括號會整份當宣告清單解析，檔首的範例宣告可能被當成真宣告（R2，轉待辦）；`.withConfig(...)` 鏈式方法未辨識（轉待辦）；樣式標籤前方若有落單反引號（例如 JSX 文字裡的 ` 字元）會中斷後方樣板辨識（轉待辦）。

regex 可設定 `exclude_properties`：只剔除位於指定 CSS 屬性值裡的命中，保留其餘命中及原始行號。trope-02 用它排除 mask-image、-webkit-mask-image、mask、-webkit-mask；既有 `exclusion_pattern` 仍是整檔豁免。

### 排除指定規則

`--skip-tropes trope-20,trope-21` 可跳過指定規則，未知編號會報錯並以結束碼 2 退出。這只控制 trope 層；檔內也接受 `<!-- anti-slop-skip: trope-20,trope-21 -->` 或 `/* anti-slop-skip: trope-20,trope-21 */`，同檔標記與 CLI 排除取聯集。

目錄掃描支援 `.md`、`.mdx`、`.html`、`.htm`、`.jsx`、`.tsx`、`.css`、`.scss`、`.js`、`.mjs`、`.ts`、`.vue`、`.svelte`，副檔名大小寫不敏感。遞迴先排除 `node_modules`、`.git`、`dist`、`build`、`.next`、`out`、`coverage`，不追蹤目錄符號連結；明確指定單檔仍照常掃描。

22 條 trope 中，trope-13、trope-15 只有未實作的結構型樣式；trope-03、trope-16 同時有 regex 與未實作的結構型樣式。文字與 JSON（每檔 `unchecked_rules`）均列出這 4 個樣式的編號、名稱與「未實作、未檢查」，不受 severity 篩選影響，也不算成違規命中。

trope-18 為 warning：全屬性過渡，補救為明列過渡屬性，例如 transform 與 opacity。trope-19 為 info：候選，需在瀏覽器切換減少動態設定確認；僅檢查同檔是否有 `prefers-reduced-motion`，不能驗證跨檔宣告或替代行為。規範文件可用既有 `<!-- anti-slop-skip: trope-18,trope-19 -->` 豁免範例。

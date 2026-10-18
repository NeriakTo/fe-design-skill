---
name: design-context-import
description: 掃描既有前端專案，抽出 design tokens（Tailwind config／CSS 變數／SCSS 變數／頻率兜底）與框架版本，輸出 `.design/DESIGN.md`（Google design.md 格式＋`## Framework Context`）。供 /fe-design system 模式與需要 framework_context 的前端技能使用。
---

# design-context-import

## 用途

掃描既有前端專案的設計系統 ground truth，輸出**單一可信來源** `.design/DESIGN.md`，作為其他 skill（`frontend-design` / `frontend-slides` / `starter-components` / `anti-slop-review`）的 context source。

## 何時呼叫

- `/fe-design system` pipeline 第一階段（既有專案 onboarding）
- 建新專案後想要建立基準 design system
- 既有 design system 想 normalize 為 Google design.md 規格
- 任何下游 skill 需要 framework_context（react/next/tailwind 版本）卻還沒有 `.design/DESIGN.md`

## 雙產出

執行後產生（v1.2 收斂後唯一輸出）：

```
<user-project>/.design/
└── DESIGN.md       # Google YAML frontmatter + Markdown body + ## Framework Context section
```

> 下游解析 `DESIGN.md` 的 `## Framework Context` section（見 `docs/framework-context-section-spec.md`）；`design-tokens.json` 只是中介格式，不是 context source。
> DTCG `design_tokens.json` / Tailwind config 仍可隨需透過 `npx @google/design.md export` 產出，但僅作中介格式（無 framework_context、無 components）。

## 抽取優先序

1. **`tailwind.config.{js,ts,mjs,cjs}`** — 最權威；解析 `theme.extend.colors / spacing / fontSize / borderRadius`。Tailwind v4 CSS-first 專案沒有這個檔案，一律走第 2 項。
2. **CSS 自訂屬性** — 次優；以單趟字元級狀態掃描器解析（註解／字串／括號／大括號層級
   同一趟處理，產出規則樹），認得下列選擇器：

   | 選擇器 | 語意 | 進 frontmatter |
   |---|---|---|
   | `:root` / `html` / `html:root` / `*:root` | base token | 是 |
   | `@theme` / `@theme inline`（Tailwind v4） | base token | 是 |
   | `[data-theme="x"]` | palette 變體覆寫 | 否，只進 `## Theme Variants` 摘要 |
   | `.dark` / `html.dark` / `:root.dark` | 深色模式覆寫 | 否，只進摘要 |
   | `[data-theme="x"].dark`、`html.dark[data-theme="x"]` | 逐 palette 深色覆寫 | 否，只進摘要 |

   巢狀 at-rule（`@media` / `@supports` / `@layer` / `@container`）內的規則照樣找得到；
   `@keyframes` / `@font-face` / `@property` 的內容因選擇器判定不通過而自然排除。
   後代選擇器（如 `html.dark .prose`）與 CSS nesting 的內層規則（`:root { .x { … } }`）
   都不算 base token 宣告。字串內的 `; { } /* */` 一律當字面值；字串外的反斜線跳脫
   （`foo\;bar`）不觸發語意；未閉合的字串在換行處終止，後面的規則照樣抽得到；
   檔頭 BOM 以 `utf-8-sig` 剝除，不會吃掉第一個規則。
   **未支援 `&` 父選擇器參照**：巢狀寫法 `[data-theme="x"] { &.dark { … } }` 的內層會被
   跳過（不誤掛，但不計入），逐 palette 深色請用平寫 `[data-theme="x"].dark`。
   多檔案時的 first-wins 順序：副檔名 css → pcss → postcss。
3. **SCSS `$variables: value;`** — 再次；regex 抽取
4. **頻率兜底** — 掃所有 `*.{css,scss,jsx,tsx,vue}` 抓出現頻率 ≥ 3 次的 color / spacing 值

並行跑四個 extractor，後者只填補前者缺的 token。已經抽到完整 token 的專案建議加
`--skip-frequency`，否則兜底的 `frequency-N` 色會混進 frontmatter。

### palette / dark 為何不進 frontmatter

各主題的數值 canonical 在原始 CSS，複製進 `DESIGN.md` 會多出一份會漂移的來源。
`## Theme Variants` 只回答「有哪些主題、各覆寫幾個 token、在哪個檔案第幾行」。

## Framework Context 偵測

讀取 `package.json` + `tailwind.config.*` + lock files，產出：

```markdown
## Framework Context
- react: 19
- next: 15
- tailwind: v4
- typescript: 5.7
- nodejs: 22
- pkg_manager: pnpm
```

詳細規範與下游解析方式見 [`docs/framework-context-section-spec.md`](./docs/framework-context-section-spec.md)。

## 使用方式

```bash
# 一鍵掃描並輸出（在專案根目錄執行）
python3 ~/.claude/skills/design-context-import/scan.py --root . --out .design/

# 預覽不寫檔
python3 ~/.claude/skills/design-context-import/scan.py --root . --dry-run

# 跳過特定 extractor（debug 用）
python3 ~/.claude/skills/design-context-import/scan.py --root . --skip-frequency

# 掃別人的 repo：--out 的相對路徑以「目前工作目錄」解析，不會寫進被掃描的專案
python3 ~/.claude/skills/design-context-import/scan.py --root /path/to/other-repo --out /tmp/scan-out

# 結合 design.md lint 反向驗證
npx @google/design.md@0.1.1 lint .design/DESIGN.md --format json

# 跑測試（stdlib unittest，無外部依賴）
python3 -m unittest discover -s ~/.claude/skills/design-context-import/tests \
  -t ~/.claude/skills/design-context-import/tests -v
```

> **`--out` 路徑規則**：相對路徑一律以**目前工作目錄**解析，不是以 `--root` 解析。
> 這樣掃描別人的工作樹時，輸出不會寫進對方 repo。
> 要寫進被掃描的專案，就 `cd` 過去再跑，或直接給絕對路徑。

## Tailwind v4 adapter

> 這是**匯出**方向的工具（v3 config → v4 CSS），與上面的抽取流程無關；掃描 v4 專案不會用到它。

`npx @google/design.md@0.1.1 export DESIGN.md --format tailwind` 產出的是 Tailwind v3 `theme.extend` config object。要餵 v4，需另跑：

```bash
python3 ~/.claude/skills/design-context-import/extractors/tailwind_v4_adapter.py \
  --in tailwind.theme.extend.js --out tailwind-v4.css
```

詳細實作見 [`extractors/tailwind_v4_adapter.py`](./extractors/tailwind_v4_adapter.py)（P2.9）。

## 檔案結構

```
design-context-import/
├── SKILL.md
├── scan.py                          # 主程式（P2.8）
├── extractors/
│   ├── __init__.py
│   ├── framework_detector.py        # P2.6
│   ├── tailwind.py                  # P2.2（v3 config 檔專用）
│   ├── css_vars.py                  # P2.3（含 Tailwind v4 @theme / palette / dark）
│   ├── scss_vars.py                 # P2.4
│   ├── frequency.py                 # P2.5
│   └── tailwind_v4_adapter.py       # P2.9（反向：v3 config → v4 CSS，非抽取器）
├── tests/
│   ├── test_css_vars.py             # 五種選擇器 fixture + 防漏
│   └── test_scan.py                 # --out 路徑 + Theme Variants section
├── docs/
│   └── framework-context-section-spec.md   # P2.7
└── LICENSE-APACHE-2.0               # upstream Google design.md license
```

## Upstream 鎖定

DESIGN.md 格式衍生自：

- **Repo**: [google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**: `8ecd4645b957e6a683a05fb9c79cd6c9028873d0`（取得於 2026-04-25 18:31+08:00）
- **npm package**: `@google/design.md@0.1.1`
- **License**: Apache-2.0（見 `./LICENSE-APACHE-2.0`）

## 相關 Skill

- `starter-components` — 讀 `.design/DESIGN.md` 的 `## Framework Context` 選 React 18/19 變體
- `anti-slop-review` — 用 `npx @google/design.md lint` 驗證 DESIGN.md 結構正確
- `frontend-design` / `frontend-slides` — 把 DESIGN.md 當 context 餵 LLM 生成 UI

## 相關文件

- 上游 spec：[docs/spec.md](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md)

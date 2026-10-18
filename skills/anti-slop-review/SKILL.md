---
name: anti-slop-review
description: 對 AI 產出的 HTML／JSX／DESIGN.md 與樣式、程式檔做規則化 anti-slop 檢查：結構層跑 `npx @google/design.md@0.1.1 lint`（8 條規則），語義層跑 scan.py（19 條繁中 trope＋7 sins 硬擋）。由 /anti-slop 與 /fe-design 第 6 階段呼叫。
---

# anti-slop-review

## 用途

對 AI 生成的 HTML / JSX / DESIGN.md 與樣式、程式檔做規則化 anti-slop review，找出：
1. **結構層** slop（broken-ref / missing-primary / contrast-ratio < WCAG AA / orphaned-tokens / section-order …）— 透過 `npx @google/design.md@0.1.1 lint` 8 條 default rule
2. **語義層** slop（彩色邊條卡片 / 三欄置中 benefit card / Inter 預設 / 過度漸層 / 浮誇詞彙 …）— 透過自家 19 條繁中 trope（regex；未實作結構型樣式另列）

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
│ 第二層：語義層（scan.py 19 條繁中 trope）     │
│   - 彩色邊條卡片 / 過度漸層 / 三欄 benefit    │
│   - 預設 Inter 字型 / 全置中 / 過度圓角       │
│   - Emoji 當 icon / 漸層 border / 浮誇詞彙   │
│   - 過量 hover / 假資料人名 / 假 dashboard    │
│   - 堆疊 feature list / Hero 巨型標題         │
│   - 全 font-weight: 400 / 過度嵌套 Container  │
│   - CJK 字型混搭 / 全屬性過渡 / 減少動態候選 │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ 合併輸出：critical / warning / info / nit     │
└──────────────────────────────────────────────┘
```

> 已定義規則總數：**結構層 8 條＋語義層 19 條＝27 條**（Google `types.ts` 是 type scaffold，不算 rule），另有 7 sins 硬擋層。語義層有 4 個結構型樣式未實作，並非全部規則都已執行，詳見「掃描範圍與未檢查項目」。

## 檔案結構

```
anti-slop-review/
├── SKILL.md               (本檔)
├── trope-catalog.md       19 條繁中 trope 完整 catalog（特徵 / why-slop / 破解法）
├── design-md-rules.md     8 條 Google design.md lint rule 中文釋義
├── patterns.json          19 條 trope（26 個 regex＋4 個未實作結構型樣式）
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
| 19 條繁中 trope | — | 各 trope 自定（見 patterns.json）|

## Upstream 鎖定

- **Repo**：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**：`8ecd4645b957e6a683a05fb9c79cd6c9028873d0`
- **npm package**：`@google/design.md@0.1.1`
- **License**：Apache-2.0（見 `./LICENSE-APACHE-2.0`）

## 相關文件

- `trope-catalog.md` 本目錄（19 條 trope 詳解）
- `design-md-rules.md` 本目錄（8 條結構規則中文釋義）

## 與其他 skill / command 的關係

- `/fe-design` orchestrator（`~/.claude/commands/fe-design.md`）：stage 6 第一層自動呼叫 `/anti-slop --recursive`
- `/anti-slop` slash command（`~/.claude/commands/anti-slop.md`）：本 skill 的單檔/單目錄入口
- `design-review`（gstack）：fe-design stage 6 第二層；該 skill 為 AUTO-GENERATED 不可直接改檔，因此 fe-design.md 在進入第二層前會 instruct Claude 先 `Read ~/.claude/skills/anti-slop-review/trope-catalog.md` 載入 19 條 trope 視角，再交給 design-review 做設計師複核（取代 v1.2 §10 P3.8 原規劃的 symlink 機制）
- `frontend-slides`：在 Related ECC Skills 段已加入本 skill / `/anti-slop` 作為交付前檢核工具

## 掃描範圍與未檢查項目

目錄掃描支援 `.md`、`.mdx`、`.html`、`.htm`、`.jsx`、`.tsx`、`.css`、`.scss`、`.js`、`.mjs`、`.ts`、`.vue`、`.svelte`，副檔名大小寫不敏感。遞迴先排除 `node_modules`、`.git`、`dist`、`build`、`.next`、`out`、`coverage`，不追蹤目錄符號連結；明確指定單檔仍照常掃描。

19 條 trope 中，trope-13、trope-15 只有未實作的結構型樣式；trope-03、trope-16 同時有 regex 與未實作的結構型樣式。文字與 JSON（每檔 `unchecked_rules`）均列出這 4 個樣式的編號、名稱與「未實作、未檢查」，不受 severity 篩選影響，也不算成違規命中。

trope-18 為 warning：全屬性過渡，補救為明列過渡屬性，例如 transform 與 opacity。trope-19 為 info：候選，需在瀏覽器切換減少動態設定確認；僅檢查同檔是否有 `prefers-reduced-motion`，不能驗證跨檔宣告或替代行為。規範文件可用既有 `<!-- anti-slop-skip: trope-18,trope-19 -->` 豁免範例。

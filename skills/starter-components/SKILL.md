---
name: starter-components
description: 前端骨架與設計系統倉庫：deck／canvas／裝置外框／動畫／圖表骨架、design system starter、中文字體配對 preset、匯出工具（standalone／PDF／PPTX）。供 /fe-design 第 4 階段與前端類技能取用。
---

# starter-components

## 用途

本 skill 為 `/fe-design` orchestrator 與其他前端類 skill（`frontend-slides` / `frontend-design`）提供：

1. **`scaffolds/`** — copy-paste 級骨架：deck stage / design canvas / iOS/Android frame / macOS/browser window / animations / copy_button / reading_progress / charts (pie/bar/kpi/radar/gantt/waterfall/matrix/process-flow) / tweaks_panel
2. **`starters/`** — 完整 design system starter（含 `DESIGN.md`），6 套品牌模板：
   - `chenxi-liuli/`（晨曦琉璃，暗色玻璃擬態）
   - `consulting-professional/`（白底黑體 McKinsey 顧問風）
   - `corporate-warm/`（暖米底地產商務風）
   - `tech-dark/`（深色科技 Linear/Vercel 風）
   - `editorial-minimal/`（白底明體年報學術風）
   - `chenxi-liuli-light/`（晨曦琉璃淺色變體）
3. **`craft/`** — 模組化品質規則（v1.7 P9.8）：`anti-ai-slop` / `typography` / `color` / `motion` / `taste-layout` / `interaction`，DESIGN.md 透過 `craft.requires` 宣告式引用
4. **`design-tokens-presets/`** — fe-design v1.4 §24.2 中文字體配對 4 套，加 1 套顧問簡報參數，共 5 個 CSS preset：
   - `consulting-mono-sans.css`（方案 B：全黑體 + 字重對比，⭐ 中文簡報通用預設）
   - `editorial-serif.css`（方案 C：全明體 + 字重對比，年報/學術派）
   - `mckinsey-consulting.css`（顧問風長時數簡報的設計參數，非字體配對方案）
   - `mixed-bilingual.css`（方案 A：serif headline + sans body，**僅當主受眾為英文用戶**）
   - `premium-mixed-sans.css`（方案 D：兩套黑體不同字族，進階質感）
   - 對應 fe-design.md §[1/7] Stage 1「字體配對方案」題目
5. **`tools/`** — standalone-export.mjs / fonts-inline.mjs / visual-diff.mjs / fact-check.mjs / pdf-export.mjs（v1.4 短期新增）
6. **`references/`** — 設計參考文件（v1.5 新增）：
   - `design-philosophies.md`（20 種設計哲學 × 5 流派 + 設計方向顧問流程）
   - `brand-asset-protocol.md`（品牌資產 5 步搜集協議）
   - `design-critique.md`（5 維度設計評審框架 + 雷達圖）
   - `tweaks-system.md`（即時變體切換系統使用指南）
7. **`templates/`** — 文件模板（v1.5 新增）：
   - `brand-spec.md`（品牌資產規格模板）

## 何時呼叫

- 啟動 `/fe-design deck|page|app|system` pipeline 第 4 階段「Scaffold 初始化」
- 任何前端類 skill 需要 design tokens 或元件骨架
- 直接 `cp -r ~/.claude/skills/starter-components/starters/<name>/ <user-project>/.design/` 一鍵帶入 starter

## starters 目錄

| Starter | 風格 | 適用場景 |
|---|---|---|
| `chenxi-liuli/` | 暗色玻璃擬態 | 科技產品 demo、創意展示 |
| `consulting-professional/` | 白底黑體 McKinsey 顧問風 | 企業提案、教育訓練、工業簡報 |
| `corporate-warm/` | 暖米底地產商務風 | 物業提案、社區活動 |
| `tech-dark/` | 深色科技 Linear/Vercel 風 | SaaS dashboard、技術產品頁 |
| `editorial-minimal/` | 白底明體年報學術風 | 年度報告、白皮書、學術課件 |
| `chenxi-liuli-light/` | 晨曦琉璃淺色變體 | 通用淺色玻璃擬態 |

## tools 目錄

| Tool | 說明 |
|---|---|
| `tools/standalone-export.mjs` | 把 deck/page HTML 專案 inline 為單一 .html（CSS/JS/字型/圖片全 base64 data URI；無外部依賴） |

```bash
# Standalone HTML export（零外部依賴需求）
node ~/.claude/skills/starter-components/tools/standalone-export.mjs \
  --input deck/index.html --output deck-standalone.html
```

> `tools/` 目錄下的匯出工具鏈（`export-deck-pptx.mjs` / `html2pptx*.mjs` / `pdf-export.mjs` / `html2video.mjs`）同時服務 `frontend-slides` 的 PPTX/PDF/影片匯出需求。

## scaffolds 目錄

| Scaffold | 說明 |
|---|---|
| `deck_stage.js` | slide-deck web component（1920×1080 / 鍵盤導航 / 列印 CSS / 內嵌字型）|
| `design_canvas.jsx` | 併排比較容器 |
| `ios_frame.jsx` / `android_frame.jsx` | 行動裝置外框 + status bar + keyboard |
| `macos_window.jsx` / `browser_window.jsx` | 桌面 chrome |
| `animations.jsx` | 時間軸動畫引擎 |

## 一鍵帶入 starter

```bash
# 帶入晨曦琉璃 design system 到使用者專案
# 結尾的 /. 確保把目錄內所有檔案（含 LICENSE-APACHE-2.0 / Inter-LICENSE-OFL）複製過去
cp -r ~/.claude/skills/starter-components/starters/chenxi-liuli/. /path/to/user-project/.design/

# 進入目標目錄
cd /path/to/user-project/.design

# 驗證 DESIGN.md 結構（需先 npm install -g @google/design.md@0.1.1）
npx @google/design.md@0.1.1 lint DESIGN.md --format json

# 重生產 DTCG / Tailwind 格式（統一在 .design/ 目錄下產出）
npx @google/design.md@0.1.1 export DESIGN.md --format dtcg > design_tokens.json
npx @google/design.md@0.1.1 export DESIGN.md --format tailwind > tailwind.theme.extend.js.raw
# Tailwind 原生輸出是純 JSON，需手動 wrap 為 CommonJS module（與 starter 內既有版本一致格式）
```

## Upstream 鎖定

衍生內容（starters/chenxi-liuli/）源自：

- **Repo**: [google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**: `8ecd4645b957e6a683a05fb9c79cd6c9028873d0`（取得於 2026-04-25 18:31+08:00）
- **npm package**: `@google/design.md@0.1.1`
- **License**: Apache-2.0（見 `./LICENSE-APACHE-2.0`）

Inter 字型（self-hosted，零外部依賴需求）：

- **License**: SIL Open Font License 1.1（見 `./Inter-LICENSE-OFL`）
- **來源**: [rsms/inter](https://github.com/rsms/inter)

## 合規檢查

```bash
# 三份 LICENSE 副本就位
test -f ~/.claude/skills/starter-components/LICENSE-APACHE-2.0
test -f ~/.claude/skills/starter-components/Inter-LICENSE-OFL

# 衍生自 google-labs-code/design.md 的兩套 starter 含 Modifications 註記
grep -l "Modifications" ~/.claude/skills/starter-components/starters/chenxi-liuli/DESIGN.md \
  ~/.claude/skills/starter-components/starters/chenxi-liuli-light/DESIGN.md
# ↑ 應列出兩個檔；其他 starter 為原創，不需要此註記
```

## 相關文件

- 上游 spec: [docs/spec.md](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md)

- deck mode 可跑 `scripts/deck-gates.sh <deck.html> <變體> [--config <設定檔>]`；署名與變體規則定義在 `scripts/deck-gates.config.json`，預設的四個變體都不檢查署名，要檢查時自行加規則或另指設定檔。

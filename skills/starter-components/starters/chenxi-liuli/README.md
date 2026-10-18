# 晨曦琉璃 (chenxi-liuli) Starter

Glassmorphism 風格的繁中 design system starter，承襲深夜微光與漸層的氛圍，把資訊面板做成漂浮在多彩底景上的琉璃片。

## 適用場景

- 氣象 / 智慧家居 / 即時資料儀表板
- 金融、加密貨幣等夜間使用為主的高階產品
- 沉浸式 onboarding / landing page
- App / Web 都可用

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `DESIGN.md` | 主規格（YAML frontmatter token + 8 大 section markdown body）— 唯一 source of truth |
| `design_tokens.json` | DTCG (W3C) 格式 token，可餵 Style Dictionary / Token Studio / Terrazzo |
| `tailwind.theme.extend.js` | Tailwind v3 `theme.extend` config object（v4 需另接 adapter）|
| `LICENSE-APACHE-2.0` | upstream Apache 2.0 license 副本 |
| `Inter-LICENSE-OFL` | self-hosted Inter 字型 OFL license 副本 |

> 重生產 `design_tokens.json` 與 `tailwind.theme.extend.js` 隨時可用 `npx @google/design.md@0.1.1 export` 從 `DESIGN.md` 重出（單一真源策略）。

## 一鍵帶入使用者專案

```bash
# 帶入完整 starter
cp -r ~/.claude/skills/starter-components/starters/chenxi-liuli/. /path/to/user-project/.design/

# 在使用者專案根加上 Framework Context（讓 starter-components 選 React / Tailwind 變體）
cat <<EOF >> /path/to/user-project/.design/DESIGN.md

## Framework Context
- react: 19
- next: 15
- tailwind: v4
- typescript: 5.7
- nodejs: 22
- pkg_manager: pnpm
EOF
```

## 重生產 token

```bash
# 先進入 starter / .design 所在目錄
cd /path/to/user-project/.design

# DTCG (cross-tool token format) — 純 JSON 中介格式
npx @google/design.md@0.1.1 export DESIGN.md --format dtcg > design_tokens.json

# Tailwind v3 theme.extend — 注意 CLI 原生輸出是純 JSON，
# 我方在 starter 中已 wrap 為 CommonJS module（含 attribution header）。
# 重生產時需手動加上 `module.exports = ` 前綴與結尾分號，或直接保留 .json 副檔名。
npx @google/design.md@0.1.1 export DESIGN.md --format tailwind > tailwind.theme.extend.js.raw
# 然後手動 wrap：echo "module.exports =" > out.js && cat raw >> out.js && echo ";" >> out.js

# v4 需另接 adapter（fe-design v1.2 §10 P2.9 待實作）
```

> **路徑說明**：本 starter 設計為將 `DESIGN.md` / `design_tokens.json` / `tailwind.theme.extend.js` 一併放在使用者專案的 `.design/` 目錄。Tailwind config 接入時：
> ```js
> // tailwind.config.js
> const designTokens = require('./.design/tailwind.theme.extend.js');
> module.exports = {
>   theme: { extend: designTokens.theme.extend },
>   // 你自己的其餘 config...
> };
> ```

## 驗證

```bash
# 在 starter 目錄內執行
cd /path/to/user-project/.design

# 結構驗證
npx @google/design.md@0.1.1 lint DESIGN.md --format json
# 預期：0 errors（warnings 主要來自 orphaned-tokens，是 upstream 設計就帶 47 colors 但只接 10 components）

# tailwind.theme.extend.js 是 CommonJS module，可實測：
node --check tailwind.theme.extend.js && echo "syntax OK"
```

## Upstream Pin

衍生自：

- **Repo**：[google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**：`8ecd4645b957e6a683a05fb9c79cd6c9028873d0`（取得於 2026-04-25 18:31+08:00）
- **npm package**：`@google/design.md@0.1.1`
- **原 example 路徑**：`examples/atmospheric-glass/`
- **License**：Apache-2.0（見 `./LICENSE-APACHE-2.0`）

## Inter 字型

- **License**：SIL Open Font License 1.1（見 `./Inter-LICENSE-OFL`）
- **來源**：[rsms/inter](https://github.com/rsms/inter)
- **使用方式**：建議專案 `public/fonts/` 放 woff2 檔，CSS `@font-face` 載入 self-hosted；不依賴 Google Fonts CDN（零外部依賴需求）

## 修改紀錄

由Kevin Du於 2026-04-25 從 `examples/atmospheric-glass/` 改編：

1. 名稱：Atmospheric Glass → 晨曦琉璃 (chenxi-liuli)
2. Brand voice 重寫為台灣品牌語感（避免直譯西化感）
3. 8 大 section 全繁中（保留原 token 數值不動）
4. 補上 Do's and Don'ts section（upstream example 缺，spec.md 規範要求）
5. 字型策略改 self-hosted Inter（零外部依賴）

## License 與 Attribution

```
Portions of this work are derived from google-labs-code/design.md
(commit 8ecd4645b957e6a683a05fb9c79cd6c9028873d0),
licensed under Apache License 2.0.

Modifications by Kevin Du on 2026-04-25:
  - Translated to Traditional Chinese
  - Adapted brand voice for Taiwanese aesthetic
  - Renamed "Atmospheric Glass" → "晨曦琉璃"
  - Added Do's and Don'ts section
  - Token values unchanged from upstream

Inter font is licensed under SIL Open Font License 1.1.
Original copyright: Copyright 2016 The Inter Project Authors.
```

完整法律條文見：
- `./LICENSE-APACHE-2.0`（衍生內容授權）
- `./Inter-LICENSE-OFL`（字型授權）

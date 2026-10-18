# `## Framework Context` Section 規範

> fe-design v1.2.2 §7.3 — 取代 v1.1 自家 `design-tokens.json.framework_context` schema（已棄用，因 Google parser 不保留 unknown frontmatter key）

## 1. 動機

下游 skill（`starter-components` / `frontend-design` / `frontend-slides`）需要知道目標專案的技術棧版本，以便：

- `starter-components` 選 React 18 vs 19 variant
- `frontend-slides` 決定用 deck_stage.js（Web Component）還是 React 變體
- `anti-slop-review` 跑 Tailwind v3 vs v4 規則

但 Google design.md parser（`packages/cli/src/linter/parser/spec.ts:41-54`）只保留 frontmatter 內的 `name/description/colors/typography/rounded/spacing/components` 七個 key；其他 key 會被 `toDesignSystem()`（`parser/handler.ts:192-204`）丟棄。

→ 自家擴充無法走 frontmatter，必須走 markdown body 的 unknown section heading（spec.md§Consumer Behavior for Unknown Content 表中規定 unknown section 必須 **preserve 不報錯**）。

## 2. 格式

`DESIGN.md` 內任意位置（建議放在 `## Components` 之後、`## Do's and Don'ts` 之前）插入：

````markdown
## Framework Context
- react: 19
- next: 15
- tailwind: v4
- typescript: 5.7
- nodejs: 22
- pkg_manager: pnpm
````

### 2.1 規則

- Section heading 必須是 **`## Framework Context`**（兩個 `#` + 半形空格 + 大寫 F C；末尾不加冒號）
- 每行格式：`- <key>: <value>`（連字符 + 半形空格 + key + 半形冒號 + 半形空格 + value）
- key 採 lowercase + underscore（如 `pkg_manager` 不是 `pkgManager`）
- value 為原值字串（version 含 `v` 前綴；數字版本不加引號）
- 每個 key 一行；不支援巢狀
- 行間不可插入空行（會被某些 parser 視為 section 結束）

## 3. 必填 key

| key | 說明 | 範例值 |
|---|---|---|
| `react` | React major 版本 | `18` / `19` |
| `next` | Next.js major 版本（無 Next 則寫 `none`）| `14` / `15` / `none` |
| `tailwind` | Tailwind major 版本（含 `v` 前綴）| `v3` / `v4` / `none` |
| `typescript` | TypeScript 完整版本（無 TS 則寫 `none`）| `5.7` / `none` |
| `nodejs` | Node.js major 版本 | `20` / `22` |
| `pkg_manager` | 套件管理器 | `npm` / `yarn` / `pnpm` / `bun` |

## 4. 選填 key

| key | 說明 | 範例值 |
|---|---|---|
| `vite` | Vite 版本 | `5` / `6` |
| `app_router` | Next.js 是否用 App Router | `true` / `false` |
| `rsc` | 是否用 React Server Components | `true` / `false` |
| `bundler` | 主 bundler | `vite` / `webpack` / `turbopack` |

下游 skill 應**忽略未認識的 key**（forward compatibility）。

## 5. 解析規範（下游 skill 實作）

### 5.1 Python 範例

```python
import re
from pathlib import Path

def parse_framework_context(design_md: Path) -> dict[str, str]:
    text = design_md.read_text(encoding='utf-8')
    match = re.search(
        r'^## Framework Context\s*\n((?:- \w+:.*\n?)+)',
        text,
        re.MULTILINE,
    )
    if not match:
        return {}
    ctx = {}
    for line in match.group(1).splitlines():
        m = re.match(r'^- (\w+):\s*(.+)$', line)
        if m:
            ctx[m.group(1)] = m.group(2).strip()
    return ctx

# Usage
ctx = parse_framework_context(Path('.design/DESIGN.md'))
react_version = ctx.get('react', '18')  # 預設 fallback
```

### 5.2 JavaScript 範例

```js
import { readFileSync } from 'node:fs';

function parseFrameworkContext(designMdPath) {
  const text = readFileSync(designMdPath, 'utf8');
  const m = text.match(/^## Framework Context\s*\n((?:- \w+:.*\n?)+)/m);
  if (!m) return {};
  const ctx = {};
  for (const line of m[1].split('\n')) {
    const km = line.match(/^- (\w+):\s*(.+)$/);
    if (km) ctx[km[1]] = km[2].trim();
  }
  return ctx;
}

// Usage
const ctx = parseFrameworkContext('.design/DESIGN.md');
const reactVersion = ctx.react || '18';
```

### 5.3 解析失敗處理

若 `## Framework Context` section 不存在或格式錯誤：

- 下游 skill **不應 throw**；改為使用以下 fallback 鏈：
  1. 讀目標專案 `package.json` 自行偵測（保險）
  2. 若仍偵測不到，採用該 skill 的預設版本（如 React 19、Tailwind v4）
- 在 stderr 印 `[warn] <skill>: .design/DESIGN.md missing Framework Context, using fallback`

## 6. design-context-import 寫入規範

`design-context-import/extractors/framework_detector.py` 偵測完成後，由 `scan.py` 將 section 寫入 `.design/DESIGN.md`，位置在：

- 若已有 `## Components` section：插入到其**之後**、下一個 `## ...` heading 之前
- 若無 `## Components`：插入到 frontmatter `---` 之後第一個 `## ...` heading 之前
- 若整份 DESIGN.md 是新建：寫在 `## Overview` 之後

寫入時必須：

- 保留檔案原有 trailing newline
- 寫入前後加空白 line（不破壞 markdown 結構）
- 若已有 `## Framework Context` section：**整段覆寫**（不做欄位 merge），確保 source of truth 一致

## 7. 反向驗證

確認 section 不會破壞 Google design.md lint：

```bash
# 執行不應產生 broken-ref 或 missing-sections 等 critical
npx @google/design.md@0.1.1 lint .design/DESIGN.md --format json | jq '.summary'
```

預期結果：`{"errors": 0, ...}`（warnings 視 design tokens 完整度而定，與 Framework Context section 無關）

## 8. 版本記錄

- v1.0（2026-04-26）：取代 v1.1 frontmatter 路徑，改用 markdown section

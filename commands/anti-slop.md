---
description: Anti-slop review — 對指定路徑跑雙層 anti-slop scan（npx @google/design.md@0.1.1 lint 8 條結構規則 + 自家 19 條繁中 trope）
allowed-tools:
  - Bash
  - Read
  - Glob
---

# /anti-slop

對指定路徑（HTML / JSX / DESIGN.md / 目錄）跑 fe-design v1.2 §7.2 雙層 anti-slop review。

## 用法

```
/anti-slop <path> [--severity-min critical|warning|info|nit] [--recursive] [--format text|json] [--skip-design-md-lint]
```

範例：
- `/anti-slop ./index.html`
- `/anti-slop .design/DESIGN.md --format json`
- `/anti-slop ./components/ --recursive --severity-min warning`
- `/anti-slop ./hero.jsx --skip-design-md-lint`（純跑 19 條 trope 不接 npx）

## 行為

1. 偵測 target 類型（DESIGN.md / HTML / JSX / 目錄）
2. **第一層**（DESIGN.md 才跑）：shell out `npx @google/design.md@0.1.1 lint`，收 8 條結構 finding（broken-ref / contrast-ratio / missing-primary / missing-typography / missing-sections / orphaned-tokens / section-order / token-summary）
3. **第二層**（任何檔都跑）：自家 `scan.py` 跑 19 條繁中 trope（彩色邊條 / 過度漸層 / 三欄 benefit / Inter 預設 / 全置中 / 過度圓角 / Emoji icon / gradient border / 浮誇詞彙 / 過量 hover / 假人名 / 假 dashboard / 堆疊 list / Hero 巨型標題 / 單字重 / 過度嵌套 / 明黑混搭 / 全屬性過渡 / 減少動態候選；其中 4 條結構型規則尚未實作，報告列為未檢查）
4. 合併輸出，按 severity 排序（critical > warning > info > nit）

## 預熱（首次使用）

```bash
npm install -g @google/design.md@0.1.1
# 之後 npx 走本地 cache，cold start 從 2-5 秒降到 < 0.5 秒
```

如果 npx 不可用，scan.py 會自動 fallback 純 trope 層 + 印 warning 提示。

## Exit code

- `0`：無 critical（warning 不阻塞）
- `1`：有 critical（pre-commit hook 用此 gate）
- 可改 `--exit-code fail-on-warning` 加嚴

## 實作

```bash
PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:$PATH" \
  python3 ~/.claude/skills/anti-slop-review/scan.py "$@"
```

完整文件見 `~/.claude/skills/anti-slop-review/SKILL.md`。

# vendored — `@google/design.md@0.1.1` tarball fallback

當 host 沒有 `npx` / `npm` 或 npm registry 不可達時，`scan.py` 自動 fallback 到此目錄的 vendored tarball 跑 lint。

## 內容

| 檔案 | 來源 | sha256 |
|---|---|---|
| `google-design.md-0.1.1.tgz` | `npm pack @google/design.md@0.1.1`（2026-04-26）| 見 npm registry shasum |

## 行為

`scan.py` 在以下任一情況 fallback：

- `npx` 不在 PATH（FileNotFoundError）
- npx 執行 timeout（120s）
- npx stdout JSON parse 失敗

fallback 流程：

1. lazy extract tarball 到 `~/.cache/anti-slop-review/design-md-0.1.1/`（含安全檢查：拒絕絕對路徑與 `..` 跳脫）
2. 直接 `node <cache>/package/dist/index.js lint <target> --format json`
3. 解析 payload 走原本的 severity remap 邏輯
4. 結果回傳含 `used_source: "vendored"` 標記

## 升級流程（pin 新版本時）

```bash
cd ~/.claude/skills/anti-slop-review/vendored

# 1. 移除舊版（保留版本記錄到 git history）
rm google-design.md-*.tgz

# 2. pack 新版（先確認 fe-design 規劃書已升級 NPX_PACKAGE pin）
npm pack @google/design.md@<NEW_VERSION>

# 3. 清舊 cache
rm -rf ~/.cache/anti-slop-review/

# 4. 同步更新 scan.py 內：
#    - NPX_PACKAGE = "@google/design.md@<NEW_VERSION>"
#    - VENDORED_TARBALL 路徑（檔名）
#    - VENDORED_EXTRACT_DIR 路徑（版本號）

# 5. E2E 測試 fallback
python3 -c "
import sys; sys.path.insert(0, '.')
from scan import run_design_md_lint
from pathlib import Path
r = run_design_md_lint(Path('../../starter-components/starters/chenxi-liuli/DESIGN.md'),
                       npx_cmd='nonexistent_npx_force_fallback')
assert r['ok'] and r['used_source'] == 'vendored', r
print(f\"✓ vendored fallback OK ({len(r['findings'])} findings)\")
"
```

## 為什麼不用 `git submodule` 或 `npm install --prefix`

- **submodule**：design.md 上游 repo 有 1.5 MB 完整 source，pack 出的 tarball 308 KB，差 5x
- **npm install --prefix**：要本地 `npm`，但 fallback 場景就是 `npm/npx` 不可用
- **vendored tarball**：純 `tar -xzf` + `node`，只需 Python 標準庫 + Node.js runtime（runtime 本來就需要）

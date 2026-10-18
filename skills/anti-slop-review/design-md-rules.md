# Google design.md 8 條結構規則中文釋義

> 本檔說明 `npx @google/design.md@0.1.1 lint` 所跑的 8 條 default rule，由 anti-slop-review skill shell out 執行。**規則本體不重新實作**（依賴 resolved token graph + symbolTable + WCAG contrastRatio() 等高階分析），透過 shell out 引入。
>
> 來源：`packages/cli/src/linter/linter/rules/index.ts:28-37`（DEFAULT_RULE_DESCRIPTORS）

---

## 1. `broken-ref` （嚴重 / error）

**抓什麼**：YAML frontmatter 內 `{path.to.token}` reference 解析失敗、未知 component sub-token。

**為什麼必抓**：reference 失效 = downstream 工具無法正確展開 token，例如 `button-primary.backgroundColor: "{colors.primary-99}"` 但 `colors.primary-99` 不存在 → Tailwind / DTCG export 出來會帶字串「{colors.primary-99}」而不是顏色值。

**anti-slop-review 處置**：原生 severity 為 `error`，passthrough 到我方輸出為 `critical`。必修才能 ship。

**修法**：
- 改成正確存在的 token reference（例如 `{colors.primary}`）
- 直接寫 hex 值（例如 `"#1E3A8A"`）

**範例（壞 → 好）**：
```yaml
# 壞
components:
  button-primary:
    backgroundColor: "{colors.brand-blue-99}"  # ← brand-blue-99 不存在

# 好
components:
  button-primary:
    backgroundColor: "{colors.primary}"
```

---

## 2. `contrast-ratio` （警告 / warning）

**抓什麼**：component 的 `backgroundColor` × `textColor` 對比度 < WCAG AA 4.5:1。

**演算法**：來自 `model/handler.ts:contrastRatio()`，符合 WCAG 2.1 公式（相對亮度比）。

**anti-slop-review 處置**：passthrough `warning`。

**修法**：
- 加深 textColor / 加亮 backgroundColor 直到比例 ≥ 4.5:1
- 或在 component 旁加註明「裝飾用，無文字」豁免

**範例（壞 → 好）**：
```yaml
# 壞（淺灰文字 on 白底，比例 ~ 2.8:1）
button-secondary:
  backgroundColor: "#FFFFFF"
  textColor: "#A0A0A0"

# 好（深灰文字 on 白底，比例 ~ 7.5:1）
button-secondary:
  backgroundColor: "#FFFFFF"
  textColor: "#374151"
```

---

## 3. `missing-primary` （警告 / warning）

**抓什麼**：YAML 有 `colors:` 區塊但**沒有定義 `primary` token**。

**為什麼必抓**：`primary` 是 spec 推薦的 default token name；缺它的話 downstream agent 會自動生成一個（失控且不一致）。

**anti-slop-review 處置**：passthrough `warning`，附訊息「agent 會自行 auto-generate `primary`，導致跨元件不一致」。

**修法**：在 colors 區塊加上 `primary: "#XXXXXX"`。

---

## 4. `missing-typography` （警告 / warning）

**抓什麼**：有 colors token 但 `typography:` 區塊全空。

**為什麼必抓**：沒 typography token → agent 會自己挑字型（通常 Inter 或 system-ui）→ 失去設計識別。

**anti-slop-review 處置**：passthrough `warning`，與 trope-04（預設 Inter）有相關性但角度不同。

**修法**：至少定義一個 `body-md` 或 `display-lg`。

---

## 5. `missing-sections` （資訊 / info）

**抓什麼**：`spacing` 或 `rounded` token 區塊缺。

**為什麼必抓**：缺這兩段 token agent 會 fallback 到自己的預設值（8px grid / 4px radius 等）— 不是錯，但設計系統的「個性」會被稀釋。

**anti-slop-review 處置**：passthrough `info`，提示用，不阻塞。

**修法**：加 `spacing:` 或 `rounded:` token；可從 `xs/sm/md/lg/xl/full` 標準 scale 開始。

---

## 6. `orphaned-tokens` （警告 / warning，本地降為 nit）

**抓什麼**：定義了 token 但沒有任何 component 引用它。

**為什麼存在**：常見於從 Material Design 完整 palette 複製來的 token（47 colors），但 starter component 只接 10 個。orphaned 的 47 - 已用 = 大量。

**anti-slop-review 處置**：原生 `warning`，**本地 remap 為 `nit`**（fe-design 加嚴策略：因為 starter 從 atmospheric-glass 複製來自然會帶很多未用 color，沒必要 warning 滿屏）。

**修法（如果想清乾淨）**：
- 刪掉沒用到的 token
- 或刻意接到 `surface-variant` / `outline` 等次要 component

> **注意**：這條規則在 starter（如晨曦琉璃）跑會產 ~40 個 nit，預期行為，不阻塞。

---

## 7. `section-order` （警告 / warning，**不**升為 hard fail）

**抓什麼**：8 大 section 順序錯亂。spec 規定的順序：

1. Overview（也叫 Brand & Style）
2. Colors
3. Typography
4. Layout（也叫 Layout & Spacing）
5. Elevation & Depth（也叫 Elevation）
6. Shapes
7. Components
8. Do's and Don'ts

**為什麼是 warning 不是 error**：spec 自己說「section 可省略，但不能交錯」。CLI 的 exit code 只看 `summary.errors > 0`，section-order 是 `warning` 不會單獨 exit 1。

**anti-slop-review 處置**：passthrough `warning`，**fe-design 不加嚴成 hard fail**（這是本地策略選擇）。

**修法**：手動把 section 重新排序。

---

## 8. `token-summary` （資訊 / info）

**抓什麼**：純摘要，輸出當前 design system 有 N colors / M typography / K rounded / J spacing / I components。

**為什麼存在**：給 reviewer 一眼掌握規模；不是錯誤。

**anti-slop-review 處置**：passthrough `info`，作為報告 metadata 使用（顯示在報告開頭的 statistics 區塊）。

**範例輸出**：
```
Design system defines 47 colors, 6 typography scales, 6 rounding levels, 5 spacing tokens, 10 components.
```

---

## 不算規則的：`types.ts`（type scaffold）

**為什麼提**：upstream 在 `linter/linter/rules/` 有 9 個 .ts 檔，但**真正掛 `DEFAULT_RULE_DESCRIPTORS` 的是 8 條**。`types.ts` 提供 `RuleFinding` / `RuleDescriptor` 等共用型別定義，是規則骨架的支撐檔，不是 rule 本身。

**anti-slop-review 處置**：跟著 vendoring 或忽略；不會在 lint output 出現。

---

## Severity 對照表（總表）

| Rule | Google 原生 severity | anti-slop-review 顯示 | 來源 |
|---|---|---|---|
| broken-ref | error | **critical**（passthrough）| `linter/rules/broken-ref.ts:47` |
| contrast-ratio | warning | warning | `linter/rules/contrast-ratio.ts:29` |
| missing-primary | warning | warning | `linter/rules/missing-primary.ts:31` |
| missing-typography | warning | warning | `linter/rules/missing-typography.ts:33` |
| missing-sections | info | info | `linter/rules/missing-sections.ts:42` |
| orphaned-tokens | warning | **nit**（本地 remap）| `linter/rules/orphaned-tokens.ts:50` |
| section-order | warning | warning（不升 hard fail）| `linter/rules/section-order.ts:61` |
| token-summary | info | info | `linter/rules/token-summary.ts:31` |

---

## Upstream 鎖定

- **Repo**: [google-labs-code/design.md](https://github.com/google-labs-code/design.md)
- **Commit hash**: `8ecd4645b957e6a683a05fb9c79cd6c9028873d0`（2026-04-25）
- **npm package**: `@google/design.md@0.1.1`
- **License**: Apache-2.0（見 `./LICENSE-APACHE-2.0`）

---

## 為什麼不自家 reimplementation

3 個原因：

1. **規則本體依賴 resolved token graph + symbolTable**（broken-ref / orphaned-tokens 都需要解析 `{path.to.token}` 引用樹），不是純 regex 可解。
2. **WCAG contrastRatio() 演算法精準性**（contrast-ratio）不該重造輪子。
3. **upstream 仍在演進**（spec `version: alpha`），shell out 隨 npm 升級自動受惠新規則 / bugfix。

如果未來 upstream 棄坑或長期不更新，可以 fork + vendoring 進 `~/.claude/skills/anti-slop-review/vendored/`，§17.2 已預留路徑。

# Craft Rule: Typography

> 模組：typography
> 嚴重度：P1（should-fix）
> 引用：`craft.requires: [typography]`

## 字體配對紀律

### 中文基本法則

1. **禁止明體標題 + 黑體內文**（反向混搭）。中文界權威共識（justfont / typekit / 文鼎）：明體筆畫纖細，做標題在投影環境下辨識度低。
2. **允許的組合**：
   - 全黑體（方案 B）：標題 900/700 + 內文 400（最安全）
   - 全明體（方案 C）：標題 700 + 內文 400（學術/editorial）
   - 黑體標題 + 明體內文（方案 A/D）：需確認受眾主要為中文使用者
3. **同族優先**：同一字體家族不同字重 > 混用不同字體家族。
4. **層級辨識**：標題與內文的層級要一眼分得出來，可用字級、字重、位置與間距共同達成。字重差 300（如 700 對 400）是常用起點，不是門檻；只用兩級字重（例如 400 與 500）也可以，前提是字級與間距足以分出層級。層級以實際渲染結果判定，不換成另一條固定字重規則。

### CJK Fallback Chain

必須依以下順序提供 fallback：

```css
/* 方案 B（全黑體）*/
font-family: Inter, "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif;

/* 方案 C（全明體）*/
font-family: "Source Serif Pro", "Noto Serif TC", "Songti TC", "PMingLiU", serif;
```

### PPTX 字體映射

語義級翻譯器 `html2pptx.mjs` 會自動映射：
- `Noto Sans TC` → `微軟正黑體`
- `Noto Serif TC` → `新細明體`
- `Inter` → `Calibri`

## 字級階梯紀律

### 最小層級數

每個設計系統至少定義 4 個字級：`display` / `headline` / `body` / `label`。

### 字級比例

建議使用 Perfect Fourth (1.333) 或 Major Third (1.25) 比例：

| 層級 | 比例 (1.333) | 建議 px |
|------|-------------|---------|
| display-lg | × 3.16 | 48-84px |
| headline-lg | × 1.78 | 28-32px |
| body-md | × 1.00 | 16px（基準） |
| label-sm | × 0.75 | 12px |

### 行高規則

- **黑體**：body 行高 1.5×（24px / 16px）
- **明體**：body 行高 1.75×（28px / 16px）——筆畫細節需要更大行距
- **標題**：行高 1.1-1.2×（緊湊，避免鬆散）

## Letter-Spacing 紀律

| 字級 | letterSpacing | 原因 |
|------|--------------|------|
| display-lg | -0.03 ~ -0.04em | 大字需收緊，避免鬆散感 |
| headline | -0.01 ~ -0.02em | 微收 |
| body | 0 | 預設值，不調整 |
| label-sm | +0.04 ~ +0.05em | 小字需擴展，增加辨識度 |

## 禁止項

- 禁止 CJK 文字使用 `text-transform: uppercase`（無意義）
- 禁止字級小於 12px（WCAG 最低建議）
- 禁止在同一頁面使用超過 3 種字體家族
- 禁止 `font-weight: bold`（應明確指定數值如 700）


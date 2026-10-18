# Craft Rule: Color

> 模組：color
> 嚴重度：P1（should-fix）
> 引用：`craft.requires: [color]`

## 對比度門檻

### WCAG AA 標準（必達）

| 用途 | 最低對比度 | 適用場景 |
|------|-----------|---------|
| 正文文字 | 4.5:1 | body / label / caption |
| 大字標題 | 3:1 | display-lg / headline-lg（≥ 24px 或 ≥ 18.66px bold） |
| UI 元件 | 3:1 | 按鈕邊框、icon、focus ring |
| 裝飾性 | 無要求 | 背景漸層、分隔線（非資訊承載） |

### 計算公式

相對亮度 L = 0.2126R + 0.7152G + 0.0722B（sRGB 線性化後）
對比度 = (L_lighter + 0.05) / (L_darker + 0.05)

### 常見陷阱

- 暖色系（金色、橘色）在白底上對比度容易不足——需實測
- 深色主題的 muted 文字（灰色 on 深灰）容易低於 4.5:1
- `placeholder` 文字色合法可低至 3:1，但實際填入的文字必須 4.5:1

## Palette 限制

### 核心語義色（必定義）

每個設計系統至少定義以下 5 個語義 token：

| Token | 用途 | 範例 |
|-------|------|------|
| `--primary` | 主色調、品牌識別 | 深海軍藍 #1a2332 |
| `--on-primary` | primary 上的文字 | 白色 #ffffff |
| `--surface` | 全域背景 | 白色或深色底 |
| `--on-surface` | surface 上的主要文字 | 近黑或近白 |
| `--accent` | 強調色、CTA、關鍵數據 | 暖橘 #e67e22 |

### 色數限制

- 同一頁面不超過 **6 種語義色**（primary + secondary + tertiary + error + accent + muted）
- 圖表 series 色不超過 **6 色**（超過時用明度/飽和度變體）
- 灰階最多 **5 級**（surface 系列：lowest / low / container / high / highest）

### 禁止項

- 禁止使用純黑 `#000000` 作為文字色（用 `#1a1a1a` ~ `#212529` 替代，減少視覺疲勞）
- 禁止使用純白 `#ffffff` 作為深色主題文字色（用 `#e0e0e0` ~ `#f0f0f0` 替代）
- 禁止 hardcode hex 值——所有色值必須引用 DESIGN.md token
- 禁止在 accent 色上放小字（accent 對比度通常不足 4.5:1）

## 色彩和諧

### 建議配色策略

| 策略 | 適用場景 | 範例 |
|------|---------|------|
| 單色系 + accent | 顧問簡報、企業報告 | 深藍系 + 暖橘 accent |
| 互補色 | 科技產品、創新感 | 深灰 + 電青 |
| 類比色 | 溫暖品牌、社區 | 深棕 + 暖金 + sage green |
| 中性 + 紅 accent | 學術、editorial | 近黑文字 + 深紅引用 |

### Token 命名規範

語義命名 > 色彩命名：
- ✅ `--color-primary` / `--color-accent` / `--color-error`
- ❌ `--navy-800` / `--orange-500` / `--red-600`

例外：設計系統內部的 palette 定義（`:root` 區塊）可用描述性命名（`--navy-800`），但 component 引用層必須使用語義名。

## 表面層次與邊界

### 表面用語義分層
- 用背景、表面、浮起表面、邊界等語義 token 表達層次（例如 `--background`、`--surface`、`--surface-raised`、`--border`），不用裝飾效果（光暈、漸層邊框、毛玻璃）補救資訊架構。
- 巢狀容器的層次差靠表面色與間距，不靠多層陰影或多層邊框。

### 邊界分兩種
- **必要的邊界**：分隔資訊、標示輸入框、表格格線、鍵盤焦點。必須看得見，UI 元件對比至少 3:1；鍵盤焦點一定要有可辨識的樣式，不採「不使用焦點環」。
- **裝飾性邊界**：可以用低透明度的細線，但這是選項，不是要求；能用留白分組時優先用留白。


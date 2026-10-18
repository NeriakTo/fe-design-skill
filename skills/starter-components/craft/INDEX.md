# Craft Rules

> 版本：v1.1（fe-design v1.9；v1.0 為 fe-design v1.7）
> 用途：模組化品質規則，DESIGN.md frontmatter `craft.requires` 宣告式引用

## 可用模組

| 模組 | 檔案 | 用途 | 預設 |
|------|------|------|------|
| anti-ai-slop | `anti-ai-slop.md` | 7 sins P0 硬擋、AI 生成常見陷阱、操作文案 | ✅ 共同模組 |
| typography | `typography.md` | 字體配對紀律、字級與層級、letter-spacing | ✅ 共同模組 |
| color | `color.md` | 對比度門檻、語義色、表面層次與邊界 | ✅ 共同模組 |
| motion | `motion.md` | 動態用途、時長與 easing、關閉行為、減少動態替代 | ✅ 共同模組 |
| taste-layout | `taste-layout.md` | 展示型版面參考：Hero、留白節奏、構圖與背景變化、反嵌套盒子 | 展示型（混合頁只作用於展示區） |

## 引用方式

在 DESIGN.md YAML frontmatter 加入：

```yaml
craft:
  requires: [anti-ai-slop, typography]
```

`craft.requires` 用來**增加**預設清單以外的模組，不能移除共同模組；名稱不在上表就顯示錯誤並停下。

## 運作機制

以 `~/.claude/commands/fe-design.md` 的「Craft Rules 動態注入」為準：

1. Stage 1 判定用途類型（展示型、實用型、混合）。
2. Stage 2 開始前載入預設模組：共同四模組（anti-ai-slop、typography、color、motion），展示型再加 taste-layout。
3. Stage 3 寫完 DESIGN.md 後讀 `craft.requires` 補載。
4. 載入的規則在 Stage 5 實作與 Stage 6 檢核都是約束；模組內寫明適用範圍的條款照範圍執行。
5. 檢查器（anti-slop-review）目前只程式化檢查一部分規則，其餘靠 Stage 6 的渲染檢查與人審；報告要寫明哪些沒有自動檢查。


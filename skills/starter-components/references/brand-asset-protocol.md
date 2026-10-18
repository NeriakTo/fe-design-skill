# 核心資產協議（Brand Asset Protocol）

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。

## 何時觸發

任務涉及**具體品牌**——使用者提了產品名 / 公司名 / 明確客戶時，不論使用者是否主動提供品牌資料。

**不觸發**：
- 純內部工具 / 無品牌需求的技術文件
- 使用者已提供完整 brand-spec.md
- 小修改 / follow-up（已有前版 brand-spec.md）

## 5 步流程

### Step 1 · 問（資產清單一次問全）

```
關於 <brand/product>，你手上有以下哪些資料？我按優先級列：
1. Logo（SVG / 高清 PNG）— 任何品牌必備
2. 產品圖 / 官方渲染圖 — 實體產品必備
3. UI 截圖 / 介面素材 — 數位產品必備
4. 色值清單（HEX / RGB / 品牌色盤）
5. 字體清單（Display / Body）
6. Brand guidelines PDF / Figma design system / 品牌官網連結

有的直接給我，沒有的我去搜。
```

### Step 2 · 搜官方管道

| 資產類型 | 搜尋路徑 |
|---|---|
| Logo | `<brand>.com/brand` / `<brand>.com/press` / 官網 header inline SVG |
| 產品圖 | 產品詳情頁 hero image / 官方 YouTube 截幀 / 新聞稿附圖 |
| UI 截圖 | App Store / Google Play 產品頁 / 官網 screenshots / 演示影片截幀 |
| 色值 | 官網 inline CSS / Tailwind config / brand guidelines PDF |
| 字體 | 官網 `<link rel="stylesheet">` / Google Fonts 追蹤 |

WebSearch 兜底關鍵詞：
- Logo：`<brand> logo download SVG`、`<brand> press kit`
- 產品圖：`<brand> <product> official renders`
- UI：`<brand> app screenshots`

### Step 3 · 下載資產

**3.1 Logo（任何品牌必需）**

三條路徑按成功率遞減：
1. 獨立 SVG/PNG 檔案（最理想）
2. 官網 HTML 提取 inline SVG（`curl -A "Mozilla/5.0" -L https://<brand>.com -o homepage.html` → grep SVG）
3. 官方社群媒體 avatar（最後手段）

**3.2 產品圖（實體產品必需）**

1. 官方產品頁 hero image（最高優先）
2. 官方 press kit
3. 官方發布影片截幀
4. Wikimedia Commons
5. 留誠實 placeholder（灰塊 + 文字標籤「產品圖待補」）

**3.3 UI 截圖（數位產品必需）**

- App Store / Google Play 產品截圖
- 官網 screenshots section
- 產品演示影片截幀

**品質門檻**：
- 解析度 ≥2000px
- 版權清晰（官方來源 > 公共領域）
- 與品牌氣質一致

### Step 4 · 驗證

| 資產 | 驗證動作 |
|---|---|
| Logo | 檔案存在 + SVG/PNG 可開啟 + 至少兩個版本（深底/淺底） |
| 產品圖 | 至少一張 2000px+ 解析度 + 乾淨背景 |
| UI 截圖 | 解析度真實 + 是最新版本 |
| 色值 | `grep -hoE '#[0-9A-Fa-f]{6}' assets/<brand>-brand/*.{svg,html,css} | sort | uniq -c | sort -rn` |

### Step 5 · 固化為 brand-spec.md

使用 `templates/brand-spec.md` 模板，填入所有資產路徑和數值。

**寫完後的執行紀律**：
- 所有 HTML 必須**引用** brand-spec.md 裡的資產檔案路徑
- Logo 作為 `<img>` 引用真實檔案，不重畫
- CSS 變數從 spec 注入：`:root { --brand-primary: ...; }`
- 品牌一致性從「靠自覺」變成「靠結構」

## 與 Content Fidelity Lock 的關係

brand-spec.md 為 Content Fidelity Lock（fact-check.mjs）的**上游資料源**。Stage 3 fact-check 可引用 brand-spec.md 作為 Facts 表格來源之一。

## 全流程失敗兜底

| 缺失 | 處理 |
|---|---|
| Logo 完全找不到 | **停下問使用者**，不硬做 |
| 產品圖找不到 | 向使用者索取 → 誠實 placeholder（灰塊 + 「產品圖待補」） |
| UI 截圖找不到 | 向使用者索取截圖 → 官方演示影片截幀 |
| 色值找不到 | 按設計方向顧問模式走，推薦 3 方向並標註 assumption |

**禁止**：找不到資產就靜默用 CSS 剪影 / 通用漸層硬做。

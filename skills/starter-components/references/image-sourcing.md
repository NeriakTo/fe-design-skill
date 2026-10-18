# 真圖優先策略 — 圖片來源渠道與選用規則

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。
> 版本：v1.5 P7.9（fe-design 能力對齊）

---

## 原則

設計產出中的圖片應優先使用**真實圖片**而非 placeholder / AI 生成圖。真圖提升交付物的專業感和可信度，尤其在 app mode 的 UI mock 和 page mode 的 landing page。

---

## 來源優先序

| 優先級 | 來源 | 適用場景 | 授權 |
|---|---|---|---|
| 1 | 客戶提供的品牌資產 | 所有場景 | 客戶授權 |
| 2 | 客戶官網 / Press Kit | Logo、產品圖、團隊照 | 合理使用（客戶自有素材） |
| 3 | Unsplash | 通用場景圖（辦公室、科技、自然） | Unsplash License（免費商用） |
| 4 | Pexels | 同 Unsplash 備選 | Pexels License（免費商用） |
| 5 | Wikimedia Commons | 歷史圖片、圖表、地圖 | CC / Public Domain（需逐圖確認） |
| 6 | The Metropolitan Museum of Art Open Access | 藝術品、文化素材 | CC0（公有領域） |
| 7 | placeholder.com / CSS 色塊 | 僅 Junior pass 階段 | N/A |

---

## 搜尋策略

### 步驟 1：確認需求類型

| 類型 | 建議來源 |
|---|---|
| 客戶品牌（Logo / 產品） | 來源 1-2 |
| 人物 / 團隊 | Unsplash（搜 "team" / "office"） |
| 抽象 / 科技背景 | Unsplash（搜 "abstract" / "technology"） |
| 城市 / 建築 | Unsplash + Pexels |
| 地圖 / 圖表 | Wikimedia Commons |
| 藝術品 / 文化 | Met Open Access |

### 步驟 2：搜尋並下載

- Unsplash API：`https://unsplash.com/s/photos/{keyword}`
- Pexels API：`https://www.pexels.com/search/{keyword}/`
- Wikimedia：`https://commons.wikimedia.org/w/index.php?search={keyword}`
- Met：`https://www.metmuseum.org/art/collection/search?q={keyword}&isOpenAccess=true`

### 步驟 3：解析度要求

| 用途 | 最低解析度 |
|---|---|
| deck slide 全幅背景 | 1920×1080 |
| deck slide 局部圖 | 800×600 |
| page landing hero | 1440×900 |
| app mode UI 元素 | 400×400 |
| 縮圖 / icon | 200×200 |

---

## 禁止事項

- 禁止使用有浮水印的圖片
- 禁止使用 Getty / Shutterstock 等需付費授權的預覽圖
- 禁止在正式交付物中使用 `placeholder.com` 或灰色方塊（僅限 Junior pass）
- 禁止未經確認授權的 Google Image 搜尋結果

---

## fe-design 整合

- **app mode**：Stage 5 實作時，若 brief 涉及 UI mock，主腦主動搜尋真圖替代 placeholder
- **page mode**：hero section / 產品展示區優先使用客戶提供圖或 Unsplash
- **deck mode**：背景圖 / 案例截圖優先使用客戶資產；通用圖用 Unsplash

觸發條件：brief 中出現「demo」「mockup」「prototype」「landing」等關鍵詞 → 提醒使用者提供圖片，或主動搜尋真圖。

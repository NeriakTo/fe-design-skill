# 設計參考文件索引

> 版本：v1.8.4（v1.8 P10；2026-08-27 加資料頁設計依據預載）
> 用途：fe-design pipeline 載入設計參考文件的統一入口

載入指令：`Read ~/.claude/skills/starter-components/references/INDEX.md`

---

## 文件清單

| 文件 | 用途 | 觸發時機 |
|---|---|---|
| [design-md-schema.md](design-md-schema.md) | DESIGN.md 9-section schema 標準 | 建立新 starter / 審查 DESIGN.md 格式 |
| [design-philosophies.md](design-philosophies.md) | 20 種設計哲學 × 5 流派 | Stage 2 顧問模式（brief 模糊時） |
| [brand-asset-protocol.md](brand-asset-protocol.md) | 品牌資產搜集 5 步流程 | Stage 1 新品牌首次合作 |
| [scene-templates.md](scene-templates.md) | 場景模板庫（deck/page/app） | Stage 2 顧問模式推薦場景 |
| [deck-art-direction.md](deck-art-direction.md) | Visual Thesis + Art Direction Contract + slide plan（v1.8；v1.8.3 加 §2.5.2 讀者先驗） | Stage 2 立視覺主張 / Stage 3 deck mode 必交 |
| [design-critique.md](design-critique.md) | 5 維度設計評審框架 | Stage 6 量化評審（可選） |
| [tweaks-system.md](tweaks-system.md) | Tweaks 即時變體切換系統 | Stage 5 實作 tweaks |
| [editable-pptx.md](editable-pptx.md) | PPTX 語義導出 7 條 HTML 約束 | Stage 5 需 PPTX 交付時 |
| [image-sourcing.md](image-sourcing.md) | 真圖優先策略與圖片來源渠道 | Stage 5 app/page mode 需圖片時 |
| [imagegen-direction.md](imagegen-direction.md) | 產圖工序與 style tokens（v1.8） | Stage 5 deck mode 插畫需求時 |
| [animation-design.md](animation-design.md) | 動畫設計語法與避坑清單 | Stage 5 deck mode 需動畫時 |
| [rendered-qa.md](rendered-qa.md) | Contact sheet 先行 + Optical Pass + 渲染後四道 gate（v1.8） | Stage 5 工序 / Stage 6 deck mode 必跑 |
| [fe-design-stages/stage-4-scaffold.md](fe-design-stages/stage-4-scaffold.md) | Stage 4 scaffold 初始化細則 | Stage 4 |
| [fe-design-stages/stage-7-verify-deliver.md](fe-design-stages/stage-7-verify-deliver.md) | Stage 7 驗證與交付細則（含零外部依賴驗收） | Stage 7 |
| [info-dashboard-basis.md](info-dashboard-basis.md) | 資料頁／營運後台的密度型版面與四項必備元素 | Stage 3 page/app mode 且 brief 是資料頁、儀表板、營運後台、清單頁 |

## 按 Pipeline Stage 分組

### Pre-pipeline — Starter 建立 / 審查
- `design-md-schema.md` — 9-section schema 規範（建立新 starter 或審查既有 DESIGN.md 時必讀）

### Stage 1 — 需求收集
- `brand-asset-protocol.md` — 新品牌資產搜集

### Stage 2 — 風格定位
- `design-philosophies.md` — 設計哲學選擇
- `scene-templates.md` — 場景模板推薦
- `deck-art-direction.md` §1 — Visual Thesis（deck/page mode 必交，v1.8）

### Stage 3 — 設計系統
- `deck-art-direction.md` §2/§3 — Art Direction Contract + slide plan（deck mode 必交，v1.8）
- `info-dashboard-basis.md` — 資料頁／儀表板／營運後台／清單頁的密度型版面與四項必備元素（page/app mode 條件式，v1.8.4）

### Stage 5 — 實作
- `rendered-qa.md` §1/§2 — contact sheet 先行工序 + Optical Pass（deck mode，v1.8）
- `imagegen-direction.md` — 產圖工序（deck mode 插畫需求，v1.8）
- `tweaks-system.md` — 變體切換
- `editable-pptx.md` — PPTX 約束（需 PPTX 交付時）
- `image-sourcing.md` — 真圖搜尋（app/page mode）
- `animation-design.md` — 動畫設計（deck mode）

### Stage 6 — 品質檢核
- `rendered-qa.md` §3 — 渲染後四道 gate（deck mode 必跑，v1.8）
- `design-critique.md` — 5 維度量化評審

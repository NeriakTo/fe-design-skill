# 場景模板庫

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。
> 版本：v1.5 P7.11（fe-design 能力對齊）

---

## 概述

場景模板為設計方向顧問流程（Stage 2）的延伸工具。當使用者選定設計哲學後，場景模板提供具體的版面配置和元素組合範例，加速 Stage 5 實作。

---

## 模板分類

### Deck Mode 場景

| 場景 | 適用 | 版面描述 | 推薦哲學流派 |
|---|---|---|---|
| **封面**（Cover） | 所有 deck | 全幅背景圖 + 居中標題 + 副標題 + 日期 | 所有流派 |
| **章節分隔**（Section Divider） | ≥ 8 頁 deck | 半幅色塊 + 章節標題 + 章節編號 | 資訊建築 / 極簡主義 |
| **Key Message** | 提案核心 | 居中大字 + 下方支撐段落 | 所有流派 |
| **數據展示**（Data Story） | 報告 / 提案 | 左圖表 + 右解讀文字 / 上標題下全幅圖表 | 資訊建築 |
| **比較表**（Comparison） | 方案對比 | 2-3 欄並列 + 勾選圖示 + 推薦標記 | 資訊建築 / 極簡主義 |
| **時間軸**（Timeline） | 里程碑 / 歷程 | 水平軸 + 節點 + 上下交錯描述 | 資訊建築 / 運動詩學 |
| **團隊介紹**（Team） | 關於我們 | 頭像網格 + 姓名 + 職稱 | 極簡主義 / 東方哲學 |
| **案例展示**（Case Study） | 成果展示 | 裝置框架內截圖 + 旁側文字 | 所有流派 |
| **問答**（Q&A / Thank You） | 結尾 | 居中感謝語 + 聯絡方式 | 所有流派 |
| **全幅圖片**（Full Bleed） | 沈浸感 | 全幅圖片 + 半透明文字 overlay | 運動詩學 / 實驗先鋒 |

### Page Mode 場景

| 場景 | 適用 | 版面描述 |
|---|---|---|
| **Hero Section** | Landing page 首屏 | 大標題 + CTA 按鈕 + 右側圖片或動畫 |
| **Feature Grid** | 功能介紹 | 3×2 或 4×2 卡片網格 + icon + 標題 + 描述 |
| **Testimonial** | 客戶見證 | 引言 + 頭像 + 姓名職稱 + 公司 |
| **Pricing Table** | 定價方案 | 2-3 欄 + 功能比較 + CTA |
| **FAQ Accordion** | 常見問題 | 摺疊式問答 |
| **CTA Banner** | 行動呼籲 | 全幅色塊 + 標題 + 按鈕 |
| **Footer** | 頁尾 | Logo + 連結群 + 社交媒體 icon + 版權 |

### App Mode 場景

| 場景 | 適用 | 版面描述 |
|---|---|---|
| **Login / Register** | 認證頁 | 居中表單 + Logo + 背景 |
| **Dashboard** | 數據總覽 | KPI 卡片列 + 圖表區 + 側邊導航 |
| **List → Detail** | CRUD 應用 | 左側列表 + 右側詳情（master-detail） |
| **Settings** | 設定頁 | 分組表單 + toggle / select |
| **Empty State** | 無資料 | 插圖 + 說明文字 + CTA |

---

## 使用方式

### Stage 2 顧問模式中

1. 使用者選定設計哲學後，主腦從本文件篩選 3-5 個最適合的場景模板
2. 列出場景名稱 + 版面描述，讓使用者確認哪些場景需要
3. 進入 Stage 5 時，按確認的場景模板組織投影片/頁面結構

### Stage 5 實作中

- 場景模板為**結構指引**，不是固定 HTML
- 主腦根據模板描述 + 選定哲學的設計特徵，產出對應的 HTML 實作
- 可混搭場景（如 Data Story + Key Message 組合）

---

## 與設計哲學的交叉對照

| 哲學流派 | 強推場景 | 弱推 / 避免 |
|---|---|---|
| 資訊建築（01-04） | Data Story / Comparison / Timeline | Full Bleed（過於感性） |
| 運動詩學（05-08） | Full Bleed / Case Study / Cover | Comparison（過於理性） |
| 極簡主義（09-12） | Key Message / Section Divider / Team | 密集 Data Story（資訊量過大） |
| 實驗先鋒（13-16） | Full Bleed / Timeline（非傳統排版） | 傳統 Pricing Table |
| 東方哲學（17-20） | Key Message / Team / Cover（留白） | 密集 Feature Grid |

---

## fe-design 整合

- **Stage 2**：顧問模式推薦設計方向時，一併推薦適用的場景模板
- **Stage 4**：scaffold 選擇時，參照場景模板決定投影片結構
- 載入指令：`Read ~/.claude/skills/starter-components/references/scene-templates.md`

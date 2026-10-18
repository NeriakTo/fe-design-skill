# Imagegen Direction — 產圖工序（deck mode）

> 版本：v1.8 P10.4
> 觸發時機：Stage 5 實作期間，slide plan 標記「插畫需求」的頁面
> 引擎：用你手邊的生圖工具（任何可接受文字提示詞的生圖模型或服務皆可）

---

## 1. 何時生成、何時不生成

**鐵律：圖片若不承擔理解、情緒或節奏功能，就不生成。** HTML 排版能講清楚的，不畫圖。

| 用途 | 配額 | 位置 |
|---|---|---|
| 全幅插畫（full-bleed） | 每 20 頁 2–4 張 | 僅限：封面、章節轉場、情緒高峰、結尾呼應 |
| Spot 插畫（半頁/角落） | 依 slide plan | 人物情境、隱喻提示、視線引導 |
| 禁止 | — | 密集說明文字、表格、精確數字圖表、流程節點、每頁插畫化 |

## 2. Style Tokens（從 Art Direction Contract 轉譯）

Stage 3 contract 定稿後，先把美術意圖轉成固定 style token 段，之後每張 prompt 共用：

```text
媒材：＿＿（watercolor / gouache / pencil…）
筆觸：＿＿（loose wash / fine grain…）
紙張：＿＿（warm cream paper texture…）
色盤：＿＿（列 contract 的 3-4 個主色英文描述）
光線：＿＿（soft morning light / dusk gold…）
人物比例：＿＿（storybook proportions, no realistic faces…）
鏡位：＿＿（wide establishing / eye-level…）
留白方向：＿＿（clear blank area top-left for text overlay…）
禁用項：no text, no Chinese characters, no real faces, no logos
```

## 3. Prompt 規則

- **長度不設硬上限**（實測耗時主要在生圖工具本身，不在提示詞長度；工具若有逾時設定，建議放寬到 600 秒）。結構：`[用途+構圖槽位] + [場景描述] + [style tokens 精簡版] + [禁用項]`。
- **提示詞要求工具原文照送**：下指令時明寫四點——提示詞原文照送、只呼叫一次、不准自行修圖、只回傳檔案路徑；不寫的話，部分工具會把提示詞改寫成自己的規格，風格鎖定就失效。
- **圖內零中文字**：生圖模型的中文渲染多半不可靠；所有文字留在 HTML 層。
- 若生圖工具不支援參考圖（純文字生圖），風格一致性全靠 style tokens 文字鎖定。
- 文字疊圖頁必須在 prompt 指定留白區（"clear blank area on the left third"）。

## 4. 產圖工序與資產管理

1. 用你手邊的生圖工具，把完整提示詞原文送出（要求工具原文照送）。
2. 每張圖只產一次，不准工具自行修圖或重畫。
3. 產出後立即存進專案（工具的暫存目錄可能被清掉），並把提示詞全文存成同名 `.prompt.txt`。
4. 連續產多張圖時，每張各自獨立產一次。

- 資產落檔慣例：

```text
<project_root>/assets/image2/s{NN}_{purpose}_v{版本}.png
<project_root>/assets/image2/s{NN}_{purpose}_v{版本}.prompt.txt   ← prompt 全文必存
```

- build-metadata.json 加 `image2_assets[]`：`{slide, purpose, file, prompt_file}`。

## 5. 驗收 Gate（每張圖必過）

1. Read 檢視圖檔：構圖與 slide plan 槽位相符（不要求像素級）。
2. **全副一致性**：色溫、筆觸、角色造型跨圖一致——排版後把所有插畫縮圖並排比對一次。
3. 文字安全區乾淨（疊字區無高頻細節）。
4. 不合格 → 調 prompt 重跑（上限 3 次/張，超過改用排版方案替代），不修圖。
5. 4:5 / 16:9 等長寬比需求：生圖工具的輸出比例常有限，必要時產大圖後 `sips --cropOffset` 裁切（構圖居中原則寫進 prompt）。

## 6. 直式圖上 16:9 全幅的裁切 SOP

生圖工具常回直式圖（豎幅 2:3），deck 全幅頁是 16:9——`object-fit:cover` 預設取中段，可能把主體（貓臉/人物對視）裁掉：

1. Prompt 儘量寫入 "wide landscape composition"（不保證生效，實務上三張中約一張聽話）。
2. 直式圖落地後，渲染截圖檢視全幅頁，主體被裁 → 調 `object-position:50% N%`（N 偏向主體所在帶，例如用 18% 取回上段的對視瞬間）。
3. **必須渲染後用眼睛確認**——這正是 rendered-qa.md Gate 3 的用途；不要只看原圖就宣稱構圖 OK。

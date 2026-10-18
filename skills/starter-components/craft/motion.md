# Craft Rule: Motion

<!-- anti-slop-skip: trope-18,trope-19 -->

> 模組：motion
> 嚴重度：P1（should-fix）
> 引用：`craft.requires: [motion]`

## 動態的用途

每一個動態都要說得出三件事：什麼觸發它、它交代了什麼狀態變化、使用者因此少了什麼困惑（例如送出後清單更新、面板就地展開、項目被移除）。說不出用途就不要做；沒有動態也是合法的設計。

## 時長紀律

### 分級建議

| 類型 | 時長 | easing | 用途 |
|------|------|--------|------|
| 微互動 | 100-200ms | ease-out | hover、focus、toggle |
| 狀態轉換 | 200-300ms | ease-in-out | modal 開關、tab 切換、accordion |
| 入場動畫 | 300-500ms | ease-out / cubic-bezier(0.16,1,0.3,1) | 頁面載入、元素出現 |
| 退場動畫 | 150-250ms | ease-in | 元素移除、modal 關閉 |
| 數據動畫 | 600-1000ms | ease-out | counter-up、chart 繪製、progress bar |
| 頁面轉場 | 300-400ms | ease-in-out | slide 切換、route 轉場 |

### 黃金法則

1. **入場 > 退場**：入場動畫吸引注意，退場快速不干擾。入場 300ms → 退場 200ms。
2. **300ms 上限**：UI 回饋動畫（hover/click）超過 300ms 會讓使用者感覺遲鈍。
3. **依序出現分兩種**：
   - **列表與卡片**（離散元素）：間隔 50-100ms；總長＝最後一項的延遲＋該項動畫時長，不超過 500ms。
   - **文字逐字或逐詞出現**：只限展示型的短句，可選、不作預設；不得延後必要資訊、不得破壞螢幕閱讀器朗讀與文字複製。
4. **一次只動一個維度**：避免同時 scale + rotate + translate（認知負擔高）。

## Easing 函式

### 建議預設

```css
:root {
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);    /* Material standard */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0.16, 1, 0.3, 1); /* 入場減速曲線（舊名 --ease-spring，那是貝茲曲線，不是物理彈簧） */
}
```

### 禁止項

- 禁止 `linear`（除非用於無限循環 spinner 或 progress bar）
- 禁止 `ease`（CSS 預設值，模糊且不具意圖性）
- 禁止 bounce easing 用於資料視覺化（數據動畫應平滑收斂）
- 禁止 `transition: all`、`transition-property: all` 與 Tailwind 的 `transition-all`：要明列過渡的屬性（通常是 `transform`、`opacity`）

### 參考值（可選，不是門檻）

| 用途 | 參考值 | 來源 |
|------|--------|------|
| 微位移 | 4-12px | transitions.dev |
| 微縮放（按壓、對話框出現） | 0.96-0.99 | transitions.dev |
| 減速曲線 | `cubic-bezier(0.22, 1, 0.36, 1)` | transitions.dev |
| 彈簧用途分類 | 按壓回饋、面板過渡、就地變形三類 | Arc UI（精確參數未查到，專案有彈簧引擎時才另訂） |

同一個專案的曲線與時長統一成少數幾個 token，元件不要各自挑曲線。

## 關閉行為

可逆或可關閉的動態元件（對話框、抽屜、選單、展開面板）必須定義退場行為；立即消失也是合法選擇。不得因等待動畫而延後必要操作，也不得讓重開後的狀態錯誤。這一條要在瀏覽器實際開、關、重開、中途中斷來驗，不用字串比對判定。

## Deck Mode 特殊規則

### Slide 轉場

- **預設**：`opacity 0→1, 300ms ease-out`（淡入）
- **禁止**：3D flip / cube rotate / slide-from-right（過度花俏降低專業感）
- **consulting-style**：僅允許 fade 和 none

### PPTX 相容性

以下 CSS 動畫在 html2pptx 翻譯時會被靜默忽略（PPTX 不支援）：
- `@keyframes`
- `animation-*`
- `transition-*`
- `transform` 動畫（靜態 transform 可翻譯）

設計動畫時應確保**移除動畫後頁面仍可讀**（graceful degradation）。

## 無障礙

### prefers-reduced-motion

必須提供 reduced-motion 替代。下面的 CSS 只是起點：它縮短了時長，但不處理動畫延遲與 JavaScript 或動畫函式庫驅動的動態。後兩者要另外處理（延遲歸零、改成直接顯示最終狀態），並在瀏覽器切換設定實測，確認內容仍可閱讀與操作。整份專案出現一段 media query，不能視為每個元件都通過。

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 閃爍限制

- 禁止每秒閃爍超過 3 次的動畫（WCAG 2.3.1 Three Flashes）
- 禁止全螢幕色彩快速切換

## 效能

- 僅動畫 `transform` 和 `opacity`（GPU 加速屬性）
- 避免動畫 `width` / `height` / `margin` / `padding`（觸發 layout reflow）
- `will-change` 只在實際量測到卡頓時才加（例如長列表依序入場掉幀），不依項目數預設加上（依 emilkowalski animation-performance 的「不盲加 will-change」原則）
- 動畫結束後移除 `will-change`（避免記憶體佔用）


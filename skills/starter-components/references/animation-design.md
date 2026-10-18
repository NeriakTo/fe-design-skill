# 動畫設計語法與避坑清單

> 靈感來源：alchaincyf/huashu-design 的等效能力描述。本文件為獨立撰寫，不含原始碼引用。
> 版本：v1.5 P7.10（fe-design 能力對齊）

---

## 動畫設計原則

### 1. 有目的的動畫

每個動畫必須服務一個目的：引導注意力、表達狀態變化、建立空間關係。禁止純裝飾性動畫。

### 2. 時間函數選擇

| 場景 | 推薦 easing | 理由 |
|---|---|---|
| 進入畫面 | `ease-out` / `cubic-bezier(0, 0, 0.2, 1)` | 快速出現，緩慢定位 |
| 離開畫面 | `ease-in` / `cubic-bezier(0.4, 0, 1, 1)` | 緩慢啟動，快速消失 |
| 狀態切換 | `ease-in-out` | 平滑過渡 |
| 彈跳效果 | `cubic-bezier(0.34, 1.56, 0.64, 1)` | overshoot 回彈 |
| 禁止 | `linear` 做 UI 動畫 | 感覺機械、不自然 |

### 3. 持續時間指引

| 類型 | 建議 duration | 最大值 |
|---|---|---|
| 微互動（hover / focus） | 150-200ms | 300ms |
| 面板展開 / 收合 | 200-300ms | 500ms |
| 頁面過渡 | 300-500ms | 800ms |
| 載入動畫 | 500-1000ms | 2000ms |
| deck slide 過場 | 300-600ms | 1000ms |

超過最大值 → 使用者會感覺遲緩。

---

## CSS 動畫語法速查

### Transition（狀態間切換）

```css
.element {
  transition: transform 300ms ease-out, opacity 200ms ease-out;
}
.element:hover {
  transform: translateY(-4px);
  opacity: 0.9;
}
```

### Keyframe Animation（序列動畫）

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.element {
  animation: fadeInUp 500ms ease-out both;
}
```

### Stagger Pattern（序列延遲）

```css
.item { animation: fadeInUp 400ms ease-out both; }
.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 100ms; }
.item:nth-child(3) { animation-delay: 200ms; }
```

---

## Deck Mode 動畫場景

| 場景 | 建議技法 | 注意事項 |
|---|---|---|
| Slide 進場 | fadeInUp / slideInRight | `animation-fill-mode: both` 避免閃爍 |
| 數據揭示 | 計數器動畫 + bar grow | 用 CSS `@property` 或 JS requestAnimationFrame |
| 圖表進場 | 由下往上 grow | `transform-origin: bottom` |
| 重點強調 | scale pulse / highlight | 不超過 2 次循環 |
| 過場（slide 間） | 由 deck_stage.js 控制 | 不自行實作 |

---

## 避坑清單

### 效能陷阱

| 陷阱 | 問題 | 解法 |
|---|---|---|
| 動畫 `width` / `height` | 觸發 layout reflow（每幀） | 改用 `transform: scale()` |
| 動畫 `top` / `left` | 同上 | 改用 `transform: translate()` |
| 動畫 `box-shadow` | 觸發 paint（每幀） | 用 pseudo-element + opacity 切換 |
| `will-change` 濫用 | GPU 記憶體過度佔用 | 僅在動畫發生時加，結束後移除 |
| 動畫期間 DOM 操作 | 導致卡頓 | 動畫完成後再 DOM 修改 |

### PPTX 相容性

| 陷阱 | 問題 | 解法 |
|---|---|---|
| CSS animation 不可翻譯 | pptxgenjs 不支援動畫 | PPTX 中呈現動畫的最終幀 |
| `transform` 用於排版 | 翻譯器無法推導位置 | 用 `position: absolute` 替代 |
| `@keyframes` 中間幀 | PPTX 只有靜態 | 設計時確保靜態幀也美觀 |

### 無障礙

- 尊重 `prefers-reduced-motion`：
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```
- 避免閃爍（flash）頻率 > 3Hz
- 自動播放動畫必須可暫停

---

## fe-design 整合

- **deck mode**：Stage 5 實作需要動畫場景時，`Read references/animation-design.md` 載入本文件
- **app mode**：微互動設計參照本文件的時間函數和持續時間指引
- **PPTX 交付**：設計階段即考慮靜態幀美觀度（動畫不可翻譯至 PPTX）

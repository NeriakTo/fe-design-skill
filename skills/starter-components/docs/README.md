# scaffolds usage 速查

starter-components 的 7 個 scaffold 各自有完整 docstring 在檔案頂部（`scaffolds/*.{js,jsx}`）。本 README 只列**速查範例 + 適用場景**，深入 API 看各檔 header。

| Scaffold | 檔案 | 適用場景 | 行數 |
|---|---|---|---|
| 🎬 [deck_stage](#deck_stagejs) | `scaffolds/deck_stage.js` | slide deck / 簡報 / 全螢幕投影 | 455 |
| 🎨 [design_canvas](#design_canvasjsx) | `scaffolds/design_canvas.jsx` | before/after 對比 / A/B test / 主題並列 | 258 |
| 📱 [ios_frame](#ios_framejsx) | `scaffolds/ios_frame.jsx` | iPhone 模擬框（Dynamic Island / status bar）| 198 |
| 🤖 [android_frame](#android_framejsx) | `scaffolds/android_frame.jsx` | Pixel 等 Android 手機模擬框 | 235 |
| 💻 [macos_window](#macos_windowjsx) | `scaffolds/macos_window.jsx` | macOS app 視窗 chrome | 159 |
| 🌐 [browser_window](#browser_windowjsx) | `scaffolds/browser_window.jsx` | 瀏覽器視窗 + URL bar + tabs | 280 |
| ✨ [animations](#animationsjsx) | `scaffolds/animations.jsx` | 進場動畫 / Stagger / Timeline | 206 |

## 一鍵帶入專案

```bash
cp -r ~/.claude/skills/starter-components/scaffolds/. /your/project/src/components/
```

7 個 scaffold 全部相互**獨立**，可單獨 import 使用。除 `deck_stage.js`（純 web component，無 deps）外，其餘 6 個 jsx 需要 React 18+。

---

## deck_stage.js

```html
<script type="module" src="./components/deck_stage.js"></script>

<deck-stage>
  <section class="slide active" data-notes="Speaker note 1">第一張</section>
  <section class="slide">第二張</section>
  <section class="slide">第三張</section>
</deck-stage>
```

**鍵盤**：← → Space / Home End / B 黑屏 / P 列印 / N 開 notes 視窗 / 數字 + Enter 跳第 N 張

> ⚠️ `window.__deck` 為單一 instance 寫入，**同頁面只支援一個 `<deck-stage>`**。多 deck 場景請改用 `document.querySelector('deck-stage')` 直接取元件。`notes-target` 預設 `window.location.origin`（same-origin 安全），跨 origin 才需要 opt-in。

**全 API**：見 `scaffolds/deck_stage.js:1-80` header docstring（attrs / events / window.__deck / CSS vars）

---

## design_canvas.jsx

```jsx
import DesignCanvas, { Panel } from './components/design_canvas.jsx';

<DesignCanvas mode="split" labelA="Before" labelB="After">
  <Panel slot="a"><LegacyHomepage /></Panel>
  <Panel slot="b"><RedesignedHomepage /></Panel>
</DesignCanvas>
```

**modes**：`split`（左右 + 拖曳）/ `stacked`（左右雙欄 + 兩個獨立可滾動容器，可開 `syncScroll` 同步）/ `overlay`（疊加 + 透明度拖曳）

**props 命名**：JSX 統一 camelCase — `aspectRatio`、`syncScroll`、`labelA`、`labelB`、`ratio`

**全 API**：見 `scaffolds/design_canvas.jsx:1-50` header docstring

---

## ios_frame.jsx

```jsx
import IosFrame from './components/ios_frame.jsx';

<IosFrame variant="iphone-15-pro" theme="dark" time="9:41" battery={85}>
  <YourAppScreen />
</IosFrame>
```

**variants**：`iphone-15-pro`（含 Dynamic Island）/ `iphone-se` / `ipad`

> 💡 螢幕背景預設 `isDark ? '#000' : '#fff'`，若主題為非黑白色（如琉璃色系），請覆寫 `--ios-frame-screen-bg` CSS variable，否則設備殼內可能出現視覺突兀的白／黑底。

**全 API**：見 `scaffolds/ios_frame.jsx:1-30` header docstring

---

## android_frame.jsx

```jsx
import AndroidFrame from './components/android_frame.jsx';

<AndroidFrame variant="pixel-8" theme="light" navStyle="gesture">
  <YourAppScreen />
</AndroidFrame>
```

**variants**：`pixel-8` / `galaxy-s24` / `tablet`
**navStyle**：`gesture`（手勢條）/ `buttons`（三按鈕）

**全 API**：見 `scaffolds/android_frame.jsx:1-30` header docstring

---

## macos_window.jsx

```jsx
import MacosWindow from './components/macos_window.jsx';

<MacosWindow title="My App — document.txt" theme="light" onAction={(k) => console.log(k)}>
  <YourAppContent />
</MacosWindow>
```

**themes**：`light` / `dark` / `transparent`（backdrop-filter 半透明）

**全 API**：見 `scaffolds/macos_window.jsx:1-30` header docstring

---

## browser_window.jsx

```jsx
import BrowserWindow from './components/browser_window.jsx';

<BrowserWindow
  url="https://example.com/products"
  tabs={[
    { title: 'Home', favicon: '🏠' },
    { title: 'Products', active: true, favicon: '🛒' },
  ]}
  theme="light"
>
  <YourPageContent />
</BrowserWindow>
```

**themes**：`light` / `dark`
**browser**：`chrome`（tab 上圓 8px / URL bar pill / lights 12px）/ `safari`（tab 全圓 8px / URL bar 方角 8 / lights 13px）/ `firefox`（tab 上圓 4px / URL bar 全膠囊 999 / lights 12px）

**全 API**：見 `scaffolds/browser_window.jsx:1-30` header docstring

---

## animations.jsx

```jsx
import { Animate, Stagger, Timeline, useTimeline } from './components/animations.jsx';

// 進入畫面時觸發
<Animate type="fade-up" delay={200}>
  <h1>Hello</h1>
</Animate>

// 子元素依序進入（戰式效果）
<Stagger type="slide-left" interval={100}>
  <li>項目 1</li>
  <li>項目 2</li>
</Stagger>

// 手動 step 控制（搭配 deck_stage 用）
const tl = useTimeline(0, 5);
<Timeline step={tl.step}>
  <Animate at={1} type="fade">第一段在 step 1 出現</Animate>
  <Animate at={2} type="zoom">第二段在 step 2 出現</Animate>
</Timeline>
<button onClick={tl.next}>下一步</button>
```

**types**：fade / fade-up / fade-down / fade-left / fade-right / slide-{up,down,left,right} / zoom / zoom-out / blur-in
**triggers**：`view`（IntersectionObserver，default）/ `mount` / `manual`

**全 API**：見 `scaffolds/animations.jsx:1-50` header docstring

---

## 字型與設計 tokens

scaffolds 預設用 `system-ui` / `--deck-font` / `--canvas-font` 等 CSS variable，**不綁字型**。如需設計感統一，配合 `starters/chenxi-liuli/` design system 使用：

```bash
# 帶入晨曦琉璃 design tokens（含 self-hosted Inter 字型策略）
cp -r ~/.claude/skills/starter-components/starters/chenxi-liuli/. /your/project/.design/
```

> ⚠️ scaffolds 不會自動掃描 `.design/` 目錄。專案需先在 entry 載入 tokens CSS（例如 `import './.design/tokens.css'` 或 `<link rel="stylesheet">`），元件才會讀到對應的 CSS custom properties。

## License

所有 scaffold 為 Apache-2.0（同 starter-components skill 整體）。可自由商用、修改、再分發。Copyright Kevin Du 2026。

詳細 attribution 與衍生 license 條款見 `../LICENSE-APACHE-2.0`。

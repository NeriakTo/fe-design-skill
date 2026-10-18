// design_canvas.jsx — 併排 / 疊加 / 重疊比較容器
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.3)
//
// 適用情境：before/after、desktop/mobile、theme A/B、舊版/新版、A/B test 對比
//
// Usage (React 18 / 19 兼容):
//
//   import DesignCanvas, { Panel } from './design_canvas.jsx';
//
//   <DesignCanvas mode="split" labelA="Before" labelB="After">
//     <Panel slot="a"><LegacyHomepage /></Panel>
//     <Panel slot="b"><RedesignedHomepage /></Panel>
//   </DesignCanvas>
//
// Props:
//   mode             "split" (default) | "stacked" | "overlay"
//   labelA           A 面板標籤（default "A"）
//   labelB           B 面板標籤（default "B"）
//   ratio            split 預設分割比例（0-1，default 0.5）
//   aspectRatio      強制 aspect ratio（例 "16/9"，default unset）
//   bordered         加邊框（boolean）
//   syncScroll      mode=stacked 時兩欄同步滾動（boolean）
//
// Public API（fork verifier 友善）:
//   <Panel slot="a|b">          子元件，必填 slot
//   data-design-canvas-mode     根 div 屬性，可被 querySelector 找
//   data-design-canvas-ratio    當前 split ratio
//
// Modes 說明：
//   split    左右切割（垂直 divider 可拖曳；clipPath 切割同一畫面對比）
//   stacked  左右雙欄（兩個獨立可滾動容器；適合 desktop / mobile 並列展示，可開 syncScroll 同步）
//   overlay  A 在底 / B 半透明疊上（透明度可拖曳）
//
// CSS custom properties:
//   --canvas-bg          整體背景（default transparent）
//   --canvas-divider     divider 顏色（default rgba(0,0,0,0.5)）
//   --canvas-label-bg    標籤背景（default rgba(0,0,0,0.7)）
//   --canvas-label-fg    標籤文字（default #fff）

import React, { useState, useRef, useEffect, Children } from 'react';

const ROOT_STYLE = {
  position: 'relative',
  width: '100%',
  height: '100%',
  overflow: 'hidden',
  background: 'var(--canvas-bg, transparent)',
  fontFamily: 'var(--canvas-font, system-ui, -apple-system, sans-serif)',
};

const LABEL_STYLE = {
  position: 'absolute',
  top: 12,
  zIndex: 10,
  padding: '4px 12px',
  borderRadius: 9999,
  background: 'var(--canvas-label-bg, rgba(0, 0, 0, 0.7))',
  color: 'var(--canvas-label-fg, #ffffff)',
  fontSize: 13,
  fontWeight: 600,
  letterSpacing: '0.04em',
  pointerEvents: 'none',
  userSelect: 'none',
};

export function Panel({ slot, children }) {
  // 純 marker 元件，由父 DesignCanvas 透過 children 走訪認 slot prop
  return <>{children}</>;
}

export default function DesignCanvas({
  mode = 'split',
  labelA = 'A',
  labelB = 'B',
  ratio: initialRatio = 0.5,
  aspectRatio,
  bordered = false,
  syncScroll = false,
  children,
  className,
  style,
}) {
  const [ratio, setRatio] = useState(clamp(initialRatio, 0.05, 0.95));
  const rootRef = useRef(null);
  const draggingRef = useRef(false);
  const panelARef = useRef(null);
  const panelBRef = useRef(null);

  // 從 children 中認 slot=a / slot=b
  const panels = { a: null, b: null };
  Children.forEach(children, (child) => {
    if (!child || !child.props) return;
    const slot = child.props.slot;
    if (slot === 'a' || slot === 'b') {
      panels[slot] = child.props.children;
    }
  });

  // sync scroll for stacked mode
  useEffect(() => {
    if (mode !== 'stacked' || !syncScroll) return;
    const a = panelARef.current;
    const b = panelBRef.current;
    if (!a || !b) return;
    let suppress = false;
    const sync = (src, dst) => () => {
      if (suppress) return;
      suppress = true;
      dst.scrollTop = src.scrollTop;
      dst.scrollLeft = src.scrollLeft;
      requestAnimationFrame(() => { suppress = false; });
    };
    const onA = sync(a, b);
    const onB = sync(b, a);
    a.addEventListener('scroll', onA, { passive: true });
    b.addEventListener('scroll', onB, { passive: true });
    return () => {
      a.removeEventListener('scroll', onA);
      b.removeEventListener('scroll', onB);
    };
  }, [mode, syncScroll]);

  // divider 拖曳邏輯（split + overlay 共用）
  useEffect(() => {
    if (mode === 'stacked') return;
    const onMove = (e) => {
      if (!draggingRef.current || !rootRef.current) return;
      const rect = rootRef.current.getBoundingClientRect();
      const x = (e.clientX || (e.touches && e.touches[0]?.clientX)) - rect.left;
      const r = clamp(x / rect.width, 0.05, 0.95);
      setRatio(r);
    };
    const onUp = () => { draggingRef.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchmove', onMove, { passive: true });
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onUp);
    };
  }, [mode]);

  const startDrag = (e) => {
    e.preventDefault();
    draggingRef.current = true;
  };

  const rootStyle = {
    ...ROOT_STYLE,
    aspectRatio: aspectRatio || undefined,
    border: bordered ? '1px solid rgba(0,0,0,0.15)' : undefined,
    borderRadius: bordered ? 8 : undefined,
    ...style,
  };

  if (mode === 'stacked') {
    return (
      <div
        ref={rootRef}
        className={className}
        style={{ ...rootStyle, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}
        data-design-canvas-mode="stacked"
        data-design-canvas-ratio={ratio}
      >
        <div ref={panelARef} style={{ position: 'relative', overflow: 'auto', background: '#fff' }}>
          <div style={{ ...LABEL_STYLE, left: 12 }}>{labelA}</div>
          {panels.a}
        </div>
        <div ref={panelBRef} style={{ position: 'relative', overflow: 'auto', background: '#fff' }}>
          <div style={{ ...LABEL_STYLE, left: 12 }}>{labelB}</div>
          {panels.b}
        </div>
      </div>
    );
  }

  if (mode === 'overlay') {
    return (
      <div
        ref={rootRef}
        className={className}
        style={rootStyle}
        data-design-canvas-mode="overlay"
        data-design-canvas-ratio={ratio}
      >
        <div style={{ ...LABEL_STYLE, left: 12 }}>{labelA}</div>
        <div style={{ ...LABEL_STYLE, right: 12 }}>{labelB}</div>
        <div style={{ position: 'absolute', inset: 0 }}>{panels.a}</div>
        <div style={{ position: 'absolute', inset: 0, opacity: ratio, mixBlendMode: 'normal' }}>
          {panels.b}
        </div>
        <div
          onMouseDown={startDrag}
          onTouchStart={startDrag}
          style={{
            position: 'absolute',
            left: `${ratio * 100}%`,
            top: 0,
            bottom: 0,
            width: 4,
            transform: 'translateX(-2px)',
            background: 'var(--canvas-divider, rgba(0,0,0,0.5))',
            cursor: 'ew-resize',
            zIndex: 5,
          }}
          aria-label="opacity slider"
          role="separator"
        />
      </div>
    );
  }

  // mode === 'split' (default)
  return (
    <div
      ref={rootRef}
      className={className}
      style={rootStyle}
      data-design-canvas-mode="split"
      data-design-canvas-ratio={ratio}
    >
      <div style={{ ...LABEL_STYLE, left: 12 }}>{labelA}</div>
      <div style={{ ...LABEL_STYLE, right: 12 }}>{labelB}</div>
      <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 ${(1 - ratio) * 100}% 0 0)` }}>
        {panels.a}
      </div>
      <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 0 ${ratio * 100}%)` }}>
        {panels.b}
      </div>
      <div
        onMouseDown={startDrag}
        onTouchStart={startDrag}
        style={{
          position: 'absolute',
          left: `${ratio * 100}%`,
          top: 0,
          bottom: 0,
          width: 4,
          transform: 'translateX(-2px)',
          background: 'var(--canvas-divider, rgba(0,0,0,0.5))',
          cursor: 'ew-resize',
          zIndex: 5,
        }}
        aria-label="split divider"
        role="separator"
      />
    </div>
  );
}

function clamp(v, lo, hi) {
  return Math.min(hi, Math.max(lo, v));
}

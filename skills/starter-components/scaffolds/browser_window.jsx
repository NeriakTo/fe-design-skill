// browser_window.jsx — 瀏覽器視窗 chrome（traffic lights + tabs + URL bar）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.5)
//
// Usage:
//   import BrowserWindow from './browser_window.jsx';
//
//   <BrowserWindow
//     url="https://example.com/products"
//     tabs={[
//       { title: 'Home', active: false, favicon: '🏠' },
//       { title: 'Products — Example', active: true, favicon: '🛒' },
//     ]}
//     theme="light"
//   >
//     <YourPageContent />
//   </BrowserWindow>
//
// Props:
//   url           當前網址（顯示在 URL bar）
//   tabs          tab 列表（[{title, active, favicon}]，default 1 tab）
//   theme         "light" (default) | "dark"
//   browser       "chrome" (default) | "safari" | "firefox"
//                 影響三項可見細節：tab 形狀、URL bar 圓度、traffic light 尺寸
//                 - chrome:  tab 上圓角 8px、URL bar pill (radius 18)、lights 12px
//                 - safari:  tab 全圓角 8px、URL bar 方角 (radius 8)、lights 13px
//                 - firefox: tab 上圓角 4px、URL bar 全膠囊 (radius 999)、lights 12px
//   secure        是否顯示 HTTPS lock icon（default true）
//   width / height
//   className / style

import React from 'react';

const BROWSER_VARIANT = {
  chrome:  { tabRadius: '8px 8px 0 0', urlRadius: 18,  lightSize: 12 },
  safari:  { tabRadius: '8px',         urlRadius: 8,   lightSize: 13 },
  firefox: { tabRadius: '4px 4px 0 0', urlRadius: 999, lightSize: 12 },
};

const THEME = {
  light: {
    chromeBg: '#f1f3f4',
    tabActiveBg: '#fff',
    tabInactiveBg: 'transparent',
    fg: '#1a1a1a',
    border: 'rgba(0,0,0,0.12)',
    urlBg: '#fff',
    urlFg: '#1a1a1a',
  },
  dark: {
    chromeBg: '#202124',
    tabActiveBg: '#292a2d',
    tabInactiveBg: 'transparent',
    fg: '#e8eaed',
    border: 'rgba(255,255,255,0.1)',
    urlBg: '#3a3b3e',
    urlFg: '#e8eaed',
  },
};

export default function BrowserWindow({
  url = '',
  tabs,
  theme = 'light',
  browser = 'chrome',
  secure = true,
  width,
  height,
  children,
  className,
  style,
}) {
  const t = THEME[theme] || THEME.light;
  const v = BROWSER_VARIANT[browser] || BROWSER_VARIANT.chrome;
  const tabList = Array.isArray(tabs) && tabs.length > 0
    ? tabs
    : [{ title: extractDomainOrPath(url), active: true, favicon: '🌐' }];

  return (
    <div
      className={className}
      data-browser-window-theme={theme}
      data-browser-window-browser={browser}
      style={{
        position: 'relative',
        width: width || '100%',
        height: height || '100%',
        background: t.chromeBg,
        borderRadius: 10,
        boxShadow: '0 16px 40px rgba(0,0,0,0.18), 0 0 0 1px ' + t.border,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
        ...style,
      }}
    >
      {/* Top bar：traffic lights + tabs */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          padding: '6px 12px 0',
          background: t.chromeBg,
          gap: 8,
          flexShrink: 0,
        }}
      >
        <TrafficLights size={v.lightSize} />
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, marginLeft: 8 }}>
          {tabList.map((tab, i) => (
            <Tab key={i} {...tab} theme={t} radius={v.tabRadius} />
          ))}
          <button
            type="button"
            aria-label="new tab"
            style={{
              marginLeft: 4,
              width: 28,
              height: 28,
              border: 'none',
              background: 'transparent',
              color: t.fg,
              fontSize: 18,
              cursor: 'pointer',
              borderRadius: 4,
            }}
          >
            +
          </button>
        </div>
      </div>

      {/* URL bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 12px',
          background: t.chromeBg,
          borderBottom: `1px solid ${t.border}`,
          flexShrink: 0,
        }}
      >
        <NavBtn label="◀" color={t.fg} />
        <NavBtn label="▶" color={t.fg} />
        <NavBtn label="↻" color={t.fg} />
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: t.urlBg,
            borderRadius: v.urlRadius,
            padding: '6px 14px',
            color: t.urlFg,
            fontSize: 13,
            border: `1px solid ${t.border}`,
            overflow: 'hidden',
          }}
        >
          {secure && (
            <span aria-hidden="true" style={{ opacity: 0.6, fontSize: 11 }}>🔒</span>
          )}
          <span
            style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              fontFamily: 'system-ui, sans-serif',
            }}
          >
            {url || 'about:blank'}
          </span>
        </div>
        <NavBtn label="⋮" color={t.fg} />
      </div>

      {/* Page content */}
      <div style={{ flex: '1 1 auto', overflow: 'auto', background: '#fff' }}>
        {children}
      </div>
    </div>
  );
}

function Tab({ title, active, favicon, theme, radius = '8px 8px 0 0' }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '8px 14px',
        background: active ? theme.tabActiveBg : theme.tabInactiveBg,
        color: theme.fg,
        fontSize: 12,
        borderRadius: radius,
        maxWidth: 220,
        minWidth: 100,
        cursor: 'default',
        opacity: active ? 1 : 0.7,
        borderTop: active ? `1px solid ${theme.border}` : 'none',
        borderLeft: active ? `1px solid ${theme.border}` : 'none',
        borderRight: active ? `1px solid ${theme.border}` : 'none',
      }}
    >
      {favicon && <span style={{ fontSize: 13 }} aria-hidden="true">{favicon}</span>}
      <span
        style={{
          flex: 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {title}
      </span>
      {active && (
        <span style={{ opacity: 0.5, fontSize: 14 }} aria-label="close tab">×</span>
      )}
    </div>
  );
}

function TrafficLights({ size = 12 }) {
  const colors = ['#ff5f57', '#febc2e', '#28c840'];
  return (
    <div style={{ display: 'flex', gap: 8, paddingBottom: 8 }}>
      {colors.map((c) => (
        <div
          key={c}
          style={{
            width: size,
            height: size,
            borderRadius: '50%',
            background: c,
            border: '1px solid rgba(0,0,0,0.15)',
            boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.35)',
          }}
        />
      ))}
    </div>
  );
}

function NavBtn({ label, color }) {
  return (
    <button
      type="button"
      aria-label={label}
      style={{
        width: 28,
        height: 28,
        border: 'none',
        background: 'transparent',
        color,
        cursor: 'pointer',
        borderRadius: 4,
        opacity: 0.65,
        fontSize: 14,
      }}
    >
      {label}
    </button>
  );
}

function extractDomainOrPath(url) {
  if (!url) return 'New Tab';
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, '');
  } catch {
    return url.slice(0, 30);
  }
}

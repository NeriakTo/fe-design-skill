// ios_frame.jsx — iOS 裝置外框（Dynamic Island / status bar / home indicator）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.4)
//
// 用於模擬 iPhone 15 Pro 風格外框，內含 children 顯示 app screen
//
// Usage:
//   import IosFrame from './ios_frame.jsx';
//
//   <IosFrame variant="iphone-15-pro" theme="dark" time="9:41" battery={85}>
//     <YourAppScreen />
//   </IosFrame>
//
// Props:
//   variant     "iphone-15-pro" (default) | "iphone-se" | "ipad"
//   theme       "light" (default) | "dark"
//   time        Status bar 時間（default "9:41"）
//   battery     0-100（default 100）
//   carrier     左上角 carrier 文字（default 不顯示）
//   showHome    顯示 home indicator（default true）
//   showIsland  顯示 Dynamic Island（iphone-15-pro 專用，default true）
//   width       自訂寬度（default variant 預設）
//   className / style
//
// CSS custom properties:
//   --ios-frame-bg          外框背景（default #000）
//   --ios-frame-screen-bg   螢幕背景（default #fff for light / #000 for dark）

import React from 'react';

const VARIANTS = {
  'iphone-15-pro': { width: 390, height: 844, radius: 56, frameWidth: 14, hasIsland: true },
  'iphone-se':    { width: 375, height: 667, radius: 36, frameWidth: 8,  hasIsland: false },
  'ipad':         { width: 820, height: 1180, radius: 24, frameWidth: 12, hasIsland: false },
};

export default function IosFrame({
  variant = 'iphone-15-pro',
  theme = 'light',
  time = '9:41',
  battery = 100,
  carrier,
  showHome = true,
  showIsland = true,
  width: customWidth,
  children,
  className,
  style,
}) {
  const v = VARIANTS[variant] || VARIANTS['iphone-15-pro'];
  const scale = customWidth ? customWidth / v.width : 1;
  const isDark = theme === 'dark';
  const fgColor = isDark ? '#fff' : '#000';

  return (
    <div
      className={className}
      data-ios-frame-variant={variant}
      data-ios-frame-theme={theme}
      style={{
        position: 'relative',
        width: v.width * scale,
        height: v.height * scale,
        background: 'var(--ios-frame-bg, #000)',
        borderRadius: v.radius * scale,
        padding: v.frameWidth * scale,
        boxShadow: '0 30px 60px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(255,255,255,0.08)',
        boxSizing: 'border-box',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif',
        overflow: 'hidden',
        ...style,
      }}
    >
      {/* Screen */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          borderRadius: (v.radius - v.frameWidth) * scale,
          overflow: 'hidden',
          background: `var(--ios-frame-screen-bg, ${isDark ? '#000' : '#fff'})`,
        }}
      >
        {/* Status bar */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 50 * scale,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: `0 ${28 * scale}px 0 ${28 * scale}px`,
            color: fgColor,
            fontSize: 17 * scale,
            fontWeight: 600,
            zIndex: 100,
            pointerEvents: 'none',
          }}
        >
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>
            {carrier ? `${carrier} ` : ''}{time}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 * scale }}>
            <SignalIcon scale={scale} color={fgColor} />
            <WifiIcon scale={scale} color={fgColor} />
            <BatteryIcon scale={scale} color={fgColor} level={battery} />
          </span>
        </div>

        {/* Dynamic Island */}
        {v.hasIsland && showIsland && (
          <div
            style={{
              position: 'absolute',
              top: 11 * scale,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 126 * scale,
              height: 37 * scale,
              borderRadius: 9999,
              background: '#000',
              zIndex: 99,
            }}
            aria-hidden="true"
          />
        )}

        {/* App content */}
        <div
          style={{
            position: 'absolute',
            top: 50 * scale,
            left: 0,
            right: 0,
            bottom: showHome ? 34 * scale : 0,
            overflow: 'auto',
          }}
        >
          {children}
        </div>

        {/* Home indicator */}
        {showHome && (
          <div
            style={{
              position: 'absolute',
              bottom: 8 * scale,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 134 * scale,
              height: 5 * scale,
              borderRadius: 9999,
              background: fgColor,
              opacity: 0.85,
              zIndex: 100,
            }}
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}

function SignalIcon({ scale, color }) {
  return (
    <svg width={17 * scale} height={11 * scale} viewBox="0 0 17 11" fill={color} aria-hidden="true">
      <rect x="0"  y="7" width="3" height="4" rx="0.5" />
      <rect x="4.5" y="5" width="3" height="6" rx="0.5" />
      <rect x="9"  y="3" width="3" height="8" rx="0.5" />
      <rect x="13.5" y="0" width="3" height="11" rx="0.5" />
    </svg>
  );
}

function WifiIcon({ scale, color }) {
  return (
    <svg width={15 * scale} height={11 * scale} viewBox="0 0 15 11" fill={color} aria-hidden="true">
      <path d="M7.5 0C4.4 0 1.6 1.2 0 3l1.5 1.5c1.6-1.4 3.7-2.2 6-2.2s4.4 0.8 6 2.2L15 3C13.4 1.2 10.6 0 7.5 0zM7.5 4c-1.7 0-3.2 0.6-4.4 1.6L4.6 7c0.8-0.6 1.8-1 2.9-1s2.1 0.4 2.9 1l1.5-1.4C10.7 4.6 9.2 4 7.5 4zm0 4c-0.7 0-1.4 0.3-1.9 0.7L7.5 11l1.9-2.3C8.9 8.3 8.2 8 7.5 8z" />
    </svg>
  );
}

function BatteryIcon({ scale, color, level }) {
  const pct = Math.max(0, Math.min(100, level));
  return (
    <svg width={27 * scale} height={11 * scale} viewBox="0 0 27 11" aria-hidden="true">
      <rect x="0.5" y="0.5" width="22" height="10" rx="2.5" stroke={color} strokeOpacity="0.35" fill="none" />
      <rect x="2.5" y="2.5" width={Math.max(0, (18 * pct) / 100)} height="6" rx="1" fill={color} />
      <rect x="23.5" y="3.5" width="2" height="4" rx="0.5" fill={color} fillOpacity="0.4" />
    </svg>
  );
}

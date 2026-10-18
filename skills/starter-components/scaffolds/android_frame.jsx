// android_frame.jsx — Android 裝置外框（Pixel 8 / Android S24 風格）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.4)
//
// Usage:
//   import AndroidFrame from './android_frame.jsx';
//
//   <AndroidFrame variant="pixel-8" theme="light" time="9:41" battery={85}>
//     <YourAppScreen />
//   </AndroidFrame>
//
// Props:
//   variant     "pixel-8" (default) | "galaxy-s24" | "tablet"
//   theme       "light" (default) | "dark"
//   time        Status bar 時間（default "9:41"）
//   battery     0-100（default 100）
//   showNav     底部導航條（default true，三按鈕或手勢條）
//   navStyle    "gesture" (default) | "buttons"
//   width       自訂寬度
//   className / style

import React from 'react';

const VARIANTS = {
  'pixel-8':    { width: 412, height: 915, radius: 36, frameWidth: 10, punchHole: true },
  'galaxy-s24': { width: 384, height: 854, radius: 32, frameWidth: 8,  punchHole: true },
  'tablet':     { width: 800, height: 1280, radius: 16, frameWidth: 12, punchHole: false },
};

export default function AndroidFrame({
  variant = 'pixel-8',
  theme = 'light',
  time = '9:41',
  battery = 100,
  showNav = true,
  navStyle = 'gesture',
  width: customWidth,
  children,
  className,
  style,
}) {
  const v = VARIANTS[variant] || VARIANTS['pixel-8'];
  const scale = customWidth ? customWidth / v.width : 1;
  const isDark = theme === 'dark';
  const fgColor = isDark ? '#fff' : '#1a1a1a';
  const screenBg = isDark ? '#000' : '#fff';

  return (
    <div
      className={className}
      data-android-frame-variant={variant}
      data-android-frame-theme={theme}
      style={{
        position: 'relative',
        width: v.width * scale,
        height: v.height * scale,
        background: 'var(--android-frame-bg, #1a1a1a)',
        borderRadius: v.radius * scale,
        padding: v.frameWidth * scale,
        boxShadow: '0 30px 60px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(255,255,255,0.05)',
        boxSizing: 'border-box',
        fontFamily: 'Roboto, "Google Sans", system-ui, sans-serif',
        overflow: 'hidden',
        ...style,
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          borderRadius: (v.radius - v.frameWidth) * scale,
          overflow: 'hidden',
          background: `var(--android-frame-screen-bg, ${screenBg})`,
        }}
      >
        {/* Status bar */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 30 * scale,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: `0 ${20 * scale}px`,
            color: fgColor,
            fontSize: 14 * scale,
            fontWeight: 500,
            zIndex: 100,
            pointerEvents: 'none',
          }}
        >
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>{time}</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 * scale }}>
            <SignalBars scale={scale} color={fgColor} />
            <WifiIcon scale={scale} color={fgColor} />
            <BatteryHorizontal scale={scale} color={fgColor} level={battery} />
          </span>
        </div>

        {/* Punch hole camera */}
        {v.punchHole && (
          <div
            style={{
              position: 'absolute',
              top: 12 * scale,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 10 * scale,
              height: 10 * scale,
              borderRadius: '50%',
              background: '#000',
              border: `2px solid #2a2a2a`,
              zIndex: 99,
            }}
            aria-hidden="true"
          />
        )}

        {/* App content */}
        <div
          style={{
            position: 'absolute',
            top: 30 * scale,
            left: 0,
            right: 0,
            bottom: showNav ? (navStyle === 'gesture' ? 24 : 48) * scale : 0,
            overflow: 'auto',
          }}
        >
          {children}
        </div>

        {/* Navigation */}
        {showNav && navStyle === 'gesture' && (
          <div
            style={{
              position: 'absolute',
              bottom: 8 * scale,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 108 * scale,
              height: 4 * scale,
              borderRadius: 9999,
              background: fgColor,
              opacity: 0.85,
              zIndex: 100,
            }}
            aria-hidden="true"
          />
        )}
        {showNav && navStyle === 'buttons' && (
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 48 * scale,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              background: isDark ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.6)',
              backdropFilter: 'blur(12px)',
              zIndex: 100,
              pointerEvents: 'none',
            }}
          >
            <NavBack scale={scale} color={fgColor} />
            <NavHome scale={scale} color={fgColor} />
            <NavRecent scale={scale} color={fgColor} />
          </div>
        )}
      </div>
    </div>
  );
}

function SignalBars({ scale, color }) {
  return (
    <svg width={14 * scale} height={11 * scale} viewBox="0 0 14 11" fill={color} aria-hidden="true">
      <rect x="0"  y="7" width="2.5" height="4" rx="0.5" />
      <rect x="3.7" y="5" width="2.5" height="6" rx="0.5" />
      <rect x="7.4" y="3" width="2.5" height="8" rx="0.5" />
      <rect x="11.1" y="0" width="2.5" height="11" rx="0.5" />
    </svg>
  );
}

function WifiIcon({ scale, color }) {
  return (
    <svg width={14 * scale} height={11 * scale} viewBox="0 0 14 11" fill={color} aria-hidden="true">
      <path d="M7 0C4 0 1.4 1.2 0 3l1.4 1.4C2.9 3 4.9 2.2 7 2.2s4.1 0.8 5.6 2.2L14 3c-1.4-1.8-4-3-7-3zm0 4c-1.6 0-3 0.6-4.1 1.6L4.3 7C5 6.5 5.9 6.2 7 6.2s2 0.3 2.7 0.8L11.1 5.6C10 4.6 8.6 4 7 4zm0 4c-0.7 0-1.3 0.3-1.7 0.7L7 10.5l1.7-1.8C8.3 8.3 7.7 8 7 8z" />
    </svg>
  );
}

function BatteryHorizontal({ scale, color, level }) {
  const pct = Math.max(0, Math.min(100, level));
  return (
    <svg width={22 * scale} height={11 * scale} viewBox="0 0 22 11" aria-hidden="true">
      <rect x="0.5" y="1.5" width="18" height="8" rx="2" stroke={color} strokeOpacity="0.4" fill="none" />
      <rect x="2" y="3" width={Math.max(0, (15 * pct) / 100)} height="5" rx="1" fill={color} />
      <rect x="19.5" y="4" width="2" height="3" rx="0.5" fill={color} fillOpacity="0.4" />
    </svg>
  );
}

function NavBack({ scale, color }) {
  return (
    <svg width={20 * scale} height={20 * scale} viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="2" aria-hidden="true">
      <polyline points="13,4 5,10 13,16" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function NavHome({ scale, color }) {
  return (
    <svg width={18 * scale} height={18 * scale} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth="2" aria-hidden="true">
      <circle cx="9" cy="9" r="7" />
    </svg>
  );
}

function NavRecent({ scale, color }) {
  return (
    <svg width={18 * scale} height={18 * scale} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth="2" aria-hidden="true">
      <rect x="2" y="2" width="14" height="14" rx="1" />
    </svg>
  );
}

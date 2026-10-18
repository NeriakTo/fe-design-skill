// macos_window.jsx — macOS 視窗 chrome（traffic lights + title bar）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.5)
//
// Usage:
//   import MacosWindow from './macos_window.jsx';
//
//   <MacosWindow title="My App — Document.txt" theme="light">
//     <YourAppContent />
//   </MacosWindow>
//
// Props:
//   title          視窗標題（default ""）
//   theme          "light" (default) | "dark" | "transparent"
//   width / height 自訂尺寸（default 100%）
//   resizable      顯示 resize handle 視覺暗示（純展示，無互動）
//   activeButtons  哪些 traffic light 是 enabled（default ["close","minimize","maximize"]）
//   onAction       (action: "close"|"minimize"|"maximize") => void
//   className / style

import React from 'react';

const THEME = {
  light: { bg: '#f6f6f6', titleColor: '#1a1a1a', border: 'rgba(0,0,0,0.12)' },
  dark:  { bg: '#2c2c2e', titleColor: '#f0f0f0', border: 'rgba(255,255,255,0.08)' },
  transparent: { bg: 'rgba(255,255,255,0.6)', titleColor: '#1a1a1a', border: 'rgba(0,0,0,0.08)' },
};

export default function MacosWindow({
  title = '',
  theme = 'light',
  width,
  height,
  resizable = true,
  activeButtons = ['close', 'minimize', 'maximize'],
  onAction,
  children,
  className,
  style,
}) {
  const t = THEME[theme] || THEME.light;
  const isTransparent = theme === 'transparent';

  return (
    <div
      className={className}
      data-macos-window-theme={theme}
      style={{
        position: 'relative',
        width: width || '100%',
        height: height || '100%',
        background: t.bg,
        backdropFilter: isTransparent ? 'blur(20px)' : undefined,
        borderRadius: 10,
        boxShadow: '0 16px 40px rgba(0,0,0,0.18), 0 0 0 1px ' + t.border,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif',
        ...style,
      }}
    >
      {/* Title bar */}
      <div
        style={{
          position: 'relative',
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          alignItems: 'center',
          gap: 12,
          padding: '8px 14px',
          height: 38,
          borderBottom: `1px solid ${t.border}`,
          background: isTransparent ? 'transparent' : undefined,
          flexShrink: 0,
          userSelect: 'none',
        }}
      >
        <TrafficLights
          active={activeButtons}
          onAction={onAction}
        />
        <div
          style={{
            textAlign: 'center',
            color: t.titleColor,
            fontSize: 13,
            fontWeight: 500,
            letterSpacing: '-0.01em',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {title}
        </div>
        <div style={{ width: 52 }} aria-hidden="true" />
      </div>

      {/* Content area */}
      <div style={{ flex: '1 1 auto', overflow: 'auto', position: 'relative' }}>
        {children}
      </div>

      {/* Resize handle hint */}
      {resizable && (
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            right: 4,
            bottom: 4,
            width: 14,
            height: 14,
            opacity: 0.35,
            backgroundImage:
              'linear-gradient(135deg, transparent 50%, currentColor 50%, currentColor 60%, transparent 60%, transparent 70%, currentColor 70%, currentColor 80%, transparent 80%)',
            color: t.titleColor,
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  );
}

function TrafficLights({ active, onAction }) {
  const isActive = (k) => active.includes(k);
  const handle = (k) => () => { if (onAction) onAction(k); };
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', height: 14 }}>
      <Light color="#ff5f57" enabled={isActive('close')} onClick={handle('close')} aria-label="close" />
      <Light color="#febc2e" enabled={isActive('minimize')} onClick={handle('minimize')} aria-label="minimize" />
      <Light color="#28c840" enabled={isActive('maximize')} onClick={handle('maximize')} aria-label="maximize" />
    </div>
  );
}

function Light({ color, enabled, onClick, ...rest }) {
  return (
    <button
      type="button"
      onClick={enabled ? onClick : undefined}
      disabled={!enabled}
      style={{
        width: 12,
        height: 12,
        borderRadius: '50%',
        background: enabled ? color : '#bbb',
        border: enabled ? `1px solid rgba(0,0,0,0.15)` : `1px solid rgba(0,0,0,0.08)`,
        boxShadow: enabled ? 'inset 0 1px 1px rgba(255,255,255,0.35)' : 'none',
        padding: 0,
        cursor: enabled ? 'pointer' : 'not-allowed',
      }}
      {...rest}
    />
  );
}

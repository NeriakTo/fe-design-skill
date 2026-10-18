// app_phone.jsx — App 原型 flow demo 狀態管理器
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.8)
//
// 用於 app mode 的多屏 flow demo，管理畫面切換與狀態
//
// Usage:
//   import AppPhone from './app_phone.jsx';
//   import IosFrame from './ios_frame.jsx';
//
//   const screens = [
//     { id: 'login', label: '登入', component: <LoginScreen /> },
//     { id: 'home', label: '首頁', component: <HomeScreen /> },
//     { id: 'detail', label: '詳情', component: <DetailScreen /> },
//   ];
//
//   <AppPhone screens={screens} initialScreen="login" frame="ios">
//     {({ current, goto, back, history }) => (
//       <IosFrame>
//         {current.component}
//       </IosFrame>
//     )}
//   </AppPhone>
//
// Props:
//   screens         [{ id, label, component }] — 可用畫面列表
//   initialScreen   初始畫面 id（default: screens[0].id）
//   showNav         顯示底部導航列（default: true）
//   showBreadcrumb  顯示頂部 breadcrumb（default: false）
//   onNavigate      (from, to) => void — 畫面切換回呼
//   className / style
//
// 裝置外框由消費端組合（render props pattern）：
//   <AppPhone screens={screens}>
//     {({ current }) => <IosFrame>{current.component}</IosFrame>}
//   </AppPhone>

import React, { useState, useCallback, useMemo } from 'react';

export default function AppPhone({
  screens = [],
  initialScreen,
  showNav = true,
  showBreadcrumb = false,
  onNavigate,
  className = '',
  style = {},
  children,
}) {
  const startId = initialScreen || screens[0]?.id;
  const [currentId, setCurrentId] = useState(startId);
  const [history, setHistory] = useState([startId]);

  const current = useMemo(
    () => screens.find(s => s.id === currentId) || screens[0],
    [screens, currentId]
  );

  const goto = useCallback((targetId) => {
    const target = screens.find(s => s.id === targetId);
    if (!target) return;
    const prev = currentId;
    setCurrentId(targetId);
    setHistory(h => [...h, targetId]);
    onNavigate?.(prev, targetId);
  }, [screens, currentId, onNavigate]);

  const back = useCallback(() => {
    if (history.length <= 1) return;
    const newHistory = history.slice(0, -1);
    const prev = currentId;
    const targetId = newHistory[newHistory.length - 1];
    setCurrentId(targetId);
    setHistory(newHistory);
    onNavigate?.(prev, targetId);
  }, [history, currentId, onNavigate]);

  const reset = useCallback(() => {
    setCurrentId(startId);
    setHistory([startId]);
  }, [startId]);

  const canGoBack = history.length > 1;

  const ctx = { current, goto, back, reset, history, canGoBack, screens };

  if (typeof children === 'function') {
    return children(ctx);
  }

  return (
    <div
      className={`app-phone ${className}`}
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', ...style }}
    >
      {showBreadcrumb && (
        <div style={{
          display: 'flex', gap: 8, padding: '8px 0', fontSize: 12,
          color: 'var(--color-text-muted, #888)',
        }}>
          {history.map((id, i) => {
            const screen = screens.find(s => s.id === id);
            return (
              <React.Fragment key={`${id}-${i}`}>
                {i > 0 && <span style={{ opacity: 0.5 }}>{'>'}</span>}
                <span
                  style={{
                    cursor: i < history.length - 1 ? 'pointer' : 'default',
                    textDecoration: i < history.length - 1 ? 'underline' : 'none',
                  }}
                  onClick={() => {
                    if (i < history.length - 1) {
                      const prev = currentId;
                      const newHistory = history.slice(0, i + 1);
                      setCurrentId(id);
                      setHistory(newHistory);
                      onNavigate?.(prev, id);
                    }
                  }}
                >
                  {screen?.label || id}
                </span>
              </React.Fragment>
            );
          })}
        </div>
      )}

      <div style={{ position: 'relative', width: '100%' }}>
        {current?.component}
      </div>

      {showNav && (
        <div style={{
          display: 'flex', gap: 4, padding: '12px 0', flexWrap: 'wrap', justifyContent: 'center',
        }}>
          {screens.map(s => (
            <button
              key={s.id}
              onClick={() => goto(s.id)}
              style={{
                padding: '6px 16px',
                borderRadius: 6,
                border: '1px solid var(--color-border, #ddd)',
                background: s.id === currentId
                  ? 'var(--color-accent, #0066cc)'
                  : 'var(--color-bg-secondary, #f5f5f5)',
                color: s.id === currentId
                  ? '#fff'
                  : 'var(--color-text, #333)',
                fontSize: 13,
                cursor: 'pointer',
                fontFamily: 'var(--font-body, system-ui)',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export { AppPhone };

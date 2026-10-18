// animations.jsx — 時間軸動畫引擎（純 React + CSS keyframes，無外部依賴）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.2.2 §7.1 P1.6)
//
// 適用於 deck slide、landing page hero、feature reveal 等場景
// 純 CSS animation + IntersectionObserver / Timeline state，零 framework dep
//
// Usage:
//   import { Animate, Stagger, Timeline } from './animations.jsx';
//
//   // 1. 單一 Animate（進入畫面時觸發）
//   <Animate type="fade-up" delay={200} duration={600}>
//     <h1>Hello</h1>
//   </Animate>
//
//   // 2. Stagger（子元素依序進入）
//   <Stagger type="slide-left" interval={100}>
//     <li>項目 1</li>
//     <li>項目 2</li>
//     <li>項目 3</li>
//   </Stagger>
//
//   // 3. Timeline（手動控制 step；step 由 useTimeline() hook 提供）
//   const tl = useTimeline(0, 3);  // initialStep=0, totalSteps=3
//   <button onClick={tl.next}>下一段</button>
//   <Timeline step={tl.step}>
//     <Animate at={1} type="fade">第一段在 step 1 出現</Animate>
//     <Animate at={2} type="zoom">第二段在 step 2 出現</Animate>
//     <Animate at={3} type="fade-up">第三段在 step 3 出現</Animate>
//   </Timeline>
//
// Animation types:
//   fade / fade-up / fade-down / fade-left / fade-right
//   slide-up / slide-down / slide-left / slide-right
//   zoom / zoom-out
//   blur-in
//
// Public API（fork verifier 友善）:
//   data-animate-type / data-animate-state="enter|done"
//   data-animate-timeline-step={step}
//   <Timeline> 為受控元件（step 為必需 prop），不暴露 imperative ref；
//   控制函式 next() / prev() / goto(step) / reset() 一律透過 useTimeline(initial, total) hook 取得
//
// Props 摘要（Animate）:
//   type        animation 類型
//   delay       延遲 ms（default 0）
//   duration    動畫時長 ms（default 500）
//   easing      CSS easing（default 'cubic-bezier(0.22, 1, 0.36, 1)'）
//   trigger     "view" (default, IntersectionObserver) | "mount" | "manual"
//   visible     trigger=manual 時用此 prop 控制
//   at          Timeline mode 用此屬性指定 step
//   className / style / as

import React, {
  useState, useRef, useEffect, useMemo, useContext, createContext, Children,
} from 'react';

const TimelineContext = createContext(null);

const KEYFRAMES = {
  fade:        { from: { opacity: 0 }, to: { opacity: 1 } },
  'fade-up':   { from: { opacity: 0, transform: 'translateY(24px)' },  to: { opacity: 1, transform: 'translateY(0)' } },
  'fade-down': { from: { opacity: 0, transform: 'translateY(-24px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
  'fade-left': { from: { opacity: 0, transform: 'translateX(24px)' },  to: { opacity: 1, transform: 'translateX(0)' } },
  'fade-right':{ from: { opacity: 0, transform: 'translateX(-24px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
  'slide-up':  { from: { transform: 'translateY(40px)' }, to: { transform: 'translateY(0)' } },
  'slide-down':{ from: { transform: 'translateY(-40px)' }, to: { transform: 'translateY(0)' } },
  'slide-left':{ from: { transform: 'translateX(40px)' }, to: { transform: 'translateX(0)' } },
  'slide-right':{from: { transform: 'translateX(-40px)' }, to: { transform: 'translateX(0)' } },
  zoom:        { from: { opacity: 0, transform: 'scale(0.92)' }, to: { opacity: 1, transform: 'scale(1)' } },
  'zoom-out':  { from: { opacity: 0, transform: 'scale(1.08)' }, to: { opacity: 1, transform: 'scale(1)' } },
  'blur-in':   { from: { opacity: 0, filter: 'blur(12px)' }, to: { opacity: 1, filter: 'blur(0)' } },
};

const DEFAULT_EASING = 'cubic-bezier(0.22, 1, 0.36, 1)';

export function Animate({
  type = 'fade',
  delay = 0,
  duration = 500,
  easing = DEFAULT_EASING,
  trigger = 'view',
  visible: externalVisible,
  at,
  children,
  className,
  style,
  as: Tag = 'div',
}) {
  const [visible, setVisible] = useState(trigger === 'mount');
  const ref = useRef(null);
  const timeline = useContext(TimelineContext);

  // Timeline mode 優先
  const timelineActive = timeline && typeof at === 'number'
    ? timeline.step >= at
    : null;

  // External manual control
  const isVisible = trigger === 'manual'
    ? !!externalVisible
    : timelineActive !== null
      ? timelineActive
      : visible;

  // IntersectionObserver
  useEffect(() => {
    if (trigger !== 'view' || !ref.current) return;
    if (typeof IntersectionObserver === 'undefined') {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      });
    }, { threshold: 0.1 });
    io.observe(ref.current);
    return () => io.disconnect();
  }, [trigger]);

  const kf = KEYFRAMES[type] || KEYFRAMES.fade;
  const fromStyle = isVisible ? kf.to : kf.from;
  const transitionProps = Object.keys({ ...kf.from, ...kf.to }).join(', ');

  return (
    <Tag
      ref={ref}
      className={className}
      data-animate-type={type}
      data-animate-state={isVisible ? 'done' : 'enter'}
      style={{
        ...fromStyle,
        transition: `${transitionProps} ${duration}ms ${easing} ${delay}ms`,
        willChange: transitionProps,
        ...style,
      }}
    >
      {children}
    </Tag>
  );
}

export function Stagger({
  type = 'fade-up',
  interval = 100,
  delay: baseDelay = 0,
  duration = 500,
  easing = DEFAULT_EASING,
  trigger = 'view',
  children,
  className,
  style,
}) {
  const arr = Children.toArray(children);
  return (
    <div className={className} style={style} data-animate-stagger={type}>
      {arr.map((child, i) => (
        <Animate
          key={i}
          type={type}
          delay={baseDelay + i * interval}
          duration={duration}
          easing={easing}
          trigger={trigger}
        >
          {child}
        </Animate>
      ))}
    </div>
  );
}

export function Timeline({ step = 0, children, className, style }) {
  const value = useMemo(() => ({ step }), [step]);
  return (
    <TimelineContext.Provider value={value}>
      <div
        className={className}
        style={style}
        data-animate-timeline-step={step}
      >
        {children}
      </div>
    </TimelineContext.Provider>
  );
}

// Hook：手動控制 timeline 的 step（與 Timeline 配合）
//   initialStep  起始 step（default 0）
//   totalSteps   step 上界（含）；範例 useTimeline(0, 3) 對應 <Animate at={1|2|3}> 三段全可達
//                未指定時 step 無上界（Infinity）
export function useTimeline(initialStep = 0, totalSteps) {
  const [step, setStep] = useState(initialStep);
  const max = typeof totalSteps === 'number' ? totalSteps : Infinity;
  return {
    step,
    next: () => setStep((s) => Math.min(max, s + 1)),
    prev: () => setStep((s) => Math.max(0, s - 1)),
    goto: (n) => setStep(Math.max(0, Math.min(max, n))),
    reset: () => setStep(initialStep),
  };
}

export default Animate;

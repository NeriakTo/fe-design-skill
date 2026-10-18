// gantt_chart.mjs — 甘特圖（時程橫條圖）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.12)

const escapeHtml = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const TOKEN_COLORS = [
  'var(--chart-1, #003366)',
  'var(--chart-2, #d97706)',
  'var(--chart-3, #4a6285)',
  'var(--chart-4, #92400e)',
  'var(--chart-5, #2c4a73)',
  'var(--chart-6, #cbd5e0)',
];

/**
 * 將日期字串 / Date / epoch ms 轉為 timestamp，無效回傳 NaN。
 */
function toTimestamp(v) {
  if (v instanceof Date) return v.getTime();
  if (typeof v === 'number') return v;
  const d = new Date(v);
  return d.getTime();
}

/**
 * 將 timestamp 格式化為 MM/DD 短日期。
 */
function formatDate(ts) {
  const d = new Date(ts);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${mm}/${dd}`;
}

export function GanttChart({
  tasks = [],
  width = 720,
  height,
  showToday = false,
  todayLabel = 'Today',
} = {}) {
  if (!Array.isArray(tasks) || tasks.length === 0) {
    return `<div class="chart-gantt chart-gantt--empty" role="img" aria-label="empty gantt chart">(no data)</div>`;
  }

  // 解析並驗證日期
  const parsed = tasks.map((t, i) => {
    const startTs = toTimestamp(t.start);
    const endTs = toTimestamp(t.end);
    if (isNaN(startTs) || isNaN(endTs) || endTs <= startTs) return null;
    return {
      label: t.label ?? `task ${i + 1}`,
      start: startTs,
      end: endTs,
      color: t.color || TOKEN_COLORS[i % TOKEN_COLORS.length],
      progress: typeof t.progress === 'number' ? Math.max(0, Math.min(1, t.progress)) : null,
    };
  });

  const validTasks = parsed.filter(Boolean);
  if (validTasks.length === 0) {
    return `<div class="chart-gantt chart-gantt--empty" role="img" aria-label="empty gantt chart">(invalid dates)</div>`;
  }

  // 時間範圍
  const allStarts = validTasks.map((t) => t.start);
  const allEnds = validTasks.map((t) => t.end);
  const timeMin = Math.min(...allStarts);
  const timeMax = Math.max(...allEnds);
  const timeSpan = timeMax - timeMin || 1;

  // 佈局參數
  const padding = { top: 28, right: 24, bottom: 28, left: 120 };
  const rowHeight = 32;
  const barHeight = 20;
  const autoHeight = height || (padding.top + validTasks.length * rowHeight + padding.bottom);
  const innerW = width - padding.left - padding.right;
  const innerH = autoHeight - padding.top - padding.bottom;

  // 時間軸 → x 座標
  const timeToX = (ts) => padding.left + ((ts - timeMin) / timeSpan) * innerW;

  // 建立 aria-label
  const ariaLabel = `gantt chart: ${validTasks.map((t) => `${t.label} ${formatDate(t.start)}-${formatDate(t.end)}`).join(', ')}`;

  // 繪製 task 橫條
  const barsSvg = validTasks.map((t, i) => {
    const x = timeToX(t.start);
    const w = timeToX(t.end) - x;
    const y = padding.top + i * rowHeight + (rowHeight - barHeight) / 2;
    const titleText = `${escapeHtml(t.label)}: ${formatDate(t.start)} - ${formatDate(t.end)}${t.progress !== null ? ` (${(t.progress * 100).toFixed(0)}%)` : ''}`;

    // 標籤（左側）
    const labelX = padding.left - 8;
    const labelY = padding.top + i * rowHeight + rowHeight / 2;

    // 進度條（內嵌）
    const progressBar = t.progress !== null
      ? `<rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${(w * t.progress).toFixed(2)}" height="${barHeight.toFixed(2)}" fill="${t.color}" opacity="0.45" rx="3" pointer-events="none" />`
      : '';

    return `<g class="chart-gantt__task"><text x="${labelX.toFixed(2)}" y="${labelY.toFixed(2)}" class="chart-gantt__label" text-anchor="end" dominant-baseline="central">${escapeHtml(t.label)}</text><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w.toFixed(2)}" height="${barHeight.toFixed(2)}" fill="${t.color}" opacity="0.25" rx="3"><title>${titleText}</title></rect>${progressBar}</g>`;
  }).join('');

  // 今日標記線
  let todayMarker = '';
  if (showToday) {
    const nowTs = Date.now();
    if (nowTs >= timeMin && nowTs <= timeMax) {
      const tx = timeToX(nowTs);
      todayMarker = `<line x1="${tx.toFixed(2)}" y1="${padding.top}" x2="${tx.toFixed(2)}" y2="${(padding.top + innerH).toFixed(2)}" class="chart-gantt__today" /><text x="${tx.toFixed(2)}" y="${(padding.top - 6).toFixed(2)}" class="chart-gantt__today-label" text-anchor="middle" dominant-baseline="alphabetic">${escapeHtml(todayLabel)}</text>`;
    }
  }

  // 時間軸刻度（底部，最多 6 個刻度）
  const tickCount = Math.min(6, validTasks.length + 1);
  const ticksSvg = Array.from({ length: tickCount }, (_, i) => {
    const ts = timeMin + (timeSpan * i) / (tickCount - 1 || 1);
    const x = timeToX(ts);
    const y = padding.top + innerH + 16;
    return `<text x="${x.toFixed(2)}" y="${y.toFixed(2)}" class="chart-gantt__tick" text-anchor="middle" dominant-baseline="hanging">${formatDate(ts)}</text>`;
  }).join('');

  // 水平格線
  const gridSvg = validTasks.map((_, i) => {
    const y = padding.top + i * rowHeight + rowHeight;
    return `<line x1="${padding.left}" y1="${y.toFixed(2)}" x2="${(padding.left + innerW).toFixed(2)}" y2="${y.toFixed(2)}" class="chart-gantt__grid" />`;
  }).join('');

  return `<div class="chart-gantt" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-gantt__svg" viewBox="0 0 ${width} ${autoHeight}" width="${width}" height="${autoHeight}" focusable="false">${gridSvg}${barsSvg}${todayMarker}${ticksSvg}</svg></div>`;
}

export default GanttChart;

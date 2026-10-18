// waterfall_chart.mjs — 瀑布圖（累計變化正負分色）
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

// 顏色對應：increase=綠、decrease=紅、total=藍
const TYPE_COLORS = {
  increase: 'var(--waterfall-increase, var(--chart-3, #15803d))',
  decrease: 'var(--waterfall-decrease, var(--chart-6, #b91c1c))',
  total: 'var(--waterfall-total, var(--chart-1, #003366))',
};

export function WaterfallChart({
  data = [],
  width = 560,
  height = 360,
  valueFormat = (v) => v,
} = {}) {
  if (!Array.isArray(data) || data.length === 0) {
    return `<div class="chart-waterfall chart-waterfall--empty" role="img" aria-label="empty waterfall chart">(no data)</div>`;
  }

  const padding = { top: 24, right: 24, bottom: 40, left: 56 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  // 計算每個 bar 的 y 座標範圍（running sum）
  let runningSum = 0;
  const bars = data.map((d, i) => {
    const value = Number(d.value) || 0;
    const type = d.type || (value >= 0 ? 'increase' : 'decrease');
    const label = d.label ?? `item ${i + 1}`;
    let barStart, barEnd;

    if (type === 'total') {
      // total 從 baseline 0 畫到 running sum（忽略 value，用 running sum）
      barStart = 0;
      barEnd = runningSum;
    } else {
      barStart = runningSum;
      runningSum += value;
      barEnd = runningSum;
    }

    return {
      label,
      value,
      type,
      color: TYPE_COLORS[type] || TYPE_COLORS.increase,
      barTop: Math.max(barStart, barEnd),
      barBottom: Math.min(barStart, barEnd),
      runningAfter: runningSum,
    };
  });

  // 找出 y 軸範圍
  const allTops = bars.map((b) => b.barTop);
  const allBottoms = bars.map((b) => b.barBottom);
  const yMax = Math.max(0, ...allTops);
  const yMin = Math.min(0, ...allBottoms);
  const ySpan = yMax - yMin || 1;

  // 值 → y 座標（SVG y 軸向下，所以反轉）
  const valToY = (v) => padding.top + innerH - ((v - yMin) / ySpan) * innerH;
  const baselineY = valToY(0);

  const slotWidth = innerW / bars.length;
  const barWidth = slotWidth * 0.55;
  const barGap = (slotWidth - barWidth) / 2;

  // aria-label
  const ariaLabel = `waterfall chart: ${bars.map((b) => `${b.label} ${valueFormat(b.value)} (${b.type})`).join(', ')}`;

  // 繪製連接虛線（前一 bar 的 running sum → 當前 bar 的起點）
  const connectorsSvg = bars.map((b, i) => {
    if (i === 0) return '';
    const prev = bars[i - 1];
    const prevX = padding.left + (i - 1) * slotWidth + barGap + barWidth;
    const currX = padding.left + i * slotWidth + barGap;
    const connY = valToY(prev.runningAfter);
    return `<line x1="${prevX.toFixed(2)}" y1="${connY.toFixed(2)}" x2="${currX.toFixed(2)}" y2="${connY.toFixed(2)}" class="chart-waterfall__connector" />`;
  }).join('');

  // 繪製 bar
  const barsSvg = bars.map((b, i) => {
    const x = padding.left + i * slotWidth + barGap;
    const yTop = valToY(b.barTop);
    const yBottom = valToY(b.barBottom);
    const h = Math.max(yBottom - yTop, 1);
    // total 型顯示 running sum，其餘顯示原始 value
    const displayValue = b.type === 'total' ? b.barTop : b.value;
    const prefix = b.type !== 'total' && b.value > 0 ? '+' : '';
    const titleText = `${escapeHtml(b.label)}: ${escapeHtml(prefix + valueFormat(displayValue))} (${b.type})`;

    // 類別標籤（底部）
    const labelX = padding.left + i * slotWidth + slotWidth / 2;
    const labelY = padding.top + innerH + 16;

    // 數值標籤（bar 頂端上方）
    const valueX = x + barWidth / 2;
    const valueY = yTop - 6;

    return `<g class="chart-waterfall__bar"><rect x="${x.toFixed(2)}" y="${yTop.toFixed(2)}" width="${barWidth.toFixed(2)}" height="${h.toFixed(2)}" fill="${b.color}" rx="2"><title>${titleText}</title></rect><text x="${valueX.toFixed(2)}" y="${valueY.toFixed(2)}" class="chart-waterfall__value" text-anchor="middle" dominant-baseline="alphabetic">${escapeHtml(prefix + valueFormat(displayValue))}</text><text x="${labelX.toFixed(2)}" y="${labelY.toFixed(2)}" class="chart-waterfall__category" text-anchor="middle" dominant-baseline="hanging">${escapeHtml(b.label)}</text></g>`;
  }).join('');

  // baseline 零線
  const baselineSvg = `<line x1="${padding.left}" y1="${baselineY.toFixed(2)}" x2="${(padding.left + innerW).toFixed(2)}" y2="${baselineY.toFixed(2)}" class="chart-waterfall__baseline" />`;

  return `<div class="chart-waterfall" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-waterfall__svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" focusable="false">${baselineSvg}${connectorsSvg}${barsSvg}</svg></div>`;
}

export default WaterfallChart;

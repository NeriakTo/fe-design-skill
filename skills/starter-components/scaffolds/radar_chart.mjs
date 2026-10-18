// radar_chart.mjs — 5 維度雷達圖 SVG 元件
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.5)

const DEFAULTS = {
  size: 300,
  maxValue: 10,
  levels: 5,
  color: 'var(--color-accent, #0ea5e9)',
  bgColor: 'var(--color-bg, #f8fafc)',
  gridColor: 'var(--color-text, #334155)',
  labelColor: 'var(--color-text, #334155)',
  fillOpacity: 0.25,
  strokeWidth: 2,
  dotRadius: 4,
  fontSize: 12,
  labelOffset: 24,
};

export function RadarChart(props = {}) {
  const {
    dimensions,
    size = DEFAULTS.size,
    maxValue = DEFAULTS.maxValue,
    levels = DEFAULTS.levels,
    color = DEFAULTS.color,
    bgColor = DEFAULTS.bgColor,
    gridColor = DEFAULTS.gridColor,
    labelColor = DEFAULTS.labelColor,
    fillOpacity = DEFAULTS.fillOpacity,
    strokeWidth = DEFAULTS.strokeWidth,
    dotRadius = DEFAULTS.dotRadius,
    fontSize = DEFAULTS.fontSize,
    labelOffset = DEFAULTS.labelOffset,
    title = '',
  } = props;

  if (!dimensions || !Array.isArray(dimensions) || dimensions.length < 3) {
    return `<div class="radar-chart-error" role="alert">RadarChart: dimensions 需至少 3 項</div>`;
  }

  const cx = size / 2;
  const cy = size / 2;
  const radius = (size / 2) - labelOffset - 10;
  const n = dimensions.length;
  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  const point = (i, value) => {
    const angle = startAngle + i * angleStep;
    const r = (value / maxValue) * radius;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  };

  const gridLines = [];
  for (let level = 1; level <= levels; level++) {
    const r = (level / levels) * radius;
    const pts = [];
    for (let i = 0; i < n; i++) {
      const angle = startAngle + i * angleStep;
      pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
    }
    gridLines.push(`<polygon points="${pts.join(' ')}" fill="none" stroke="${gridColor}" stroke-opacity="0.15" stroke-width="0.5"/>`);
  }

  const axes = [];
  for (let i = 0; i < n; i++) {
    const end = point(i, maxValue);
    axes.push(`<line x1="${cx}" y1="${cy}" x2="${end.x}" y2="${end.y}" stroke="${gridColor}" stroke-opacity="0.2" stroke-width="0.5"/>`);
  }

  const dataPoints = dimensions.map((d, i) => point(i, Math.min(d.value, maxValue)));
  const dataPolygon = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

  const dots = dataPoints.map((p, i) =>
    `<circle cx="${p.x}" cy="${p.y}" r="${dotRadius}" fill="${color}" stroke="white" stroke-width="1.5">` +
    `<title>${dimensions[i].label}: ${dimensions[i].value}/${maxValue}</title></circle>`
  ).join('\n    ');

  const labels = dimensions.map((d, i) => {
    const lp = point(i, maxValue);
    const angle = startAngle + i * angleStep;
    const lx = cx + (radius + labelOffset) * Math.cos(angle);
    const ly = cy + (radius + labelOffset) * Math.sin(angle);
    let anchor = 'middle';
    if (Math.cos(angle) < -0.1) anchor = 'end';
    else if (Math.cos(angle) > 0.1) anchor = 'start';
    return `<text x="${lx}" y="${ly}" text-anchor="${anchor}" dominant-baseline="central" fill="${labelColor}" font-size="${fontSize}" font-family="var(--font-body, system-ui)">${d.label} (${d.value})</text>`;
  }).join('\n    ');

  const ariaLabel = `雷達圖${title ? '：' + title : ''}。${dimensions.map(d => `${d.label} ${d.value}/${maxValue}`).join('、')}`;

  return `<div class="radar-chart" role="img" aria-label="${ariaLabel}">
  <svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
    <title>${ariaLabel}</title>
    ${gridLines.join('\n    ')}
    ${axes.join('\n    ')}
    <polygon points="${dataPolygon}" fill="${color}" fill-opacity="${fillOpacity}" stroke="${color}" stroke-width="${strokeWidth}"/>
    ${dots}
    ${labels}
  </svg>
</div>`;
}

export default RadarChart;

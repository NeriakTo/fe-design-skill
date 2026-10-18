/**
 * pie_chart.mjs — fe-design v1.4-short §24.10 P6.9
 *
 * SVG pie chart (vanilla, pure HTML string export). No runtime needed —
 * tooltips use SVG <title> for browser-native hover. Token-aware: pulls from
 * mckinsey-consulting.css `--chart-1..6` (with fallbacks for standalone use).
 *
 * Usage:
 *   import { PieChart } from '~/.claude/skills/starter-components/scaffolds/charts/pie_chart.mjs';
 *   const html = PieChart({
 *     data: [
 *       { label: '正向', value: 60 },
 *       { label: '中立', value: 25 },
 *       { label: '負向', value: 15 },
 *     ],
 *     size: 320,                // px diameter (default 320)
 *     showLegend: true,         // legend on the right (default true)
 *     showPercent: true,        // overlay % on each slice (default true)
 *     valueFormat: (v) => `${v}%`,  // optional, used in tooltip title
 *   });
 *
 * Output: a single <div class="chart-pie"> containing <svg> + optional legend.
 */

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

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180.0;
  return {
    x: cx + r * Math.cos(rad),
    y: cy + r * Math.sin(rad),
  };
}

function arcPath(cx, cy, r, startAngle, endAngle) {
  // Handle full-circle case (single 100% slice) by drawing two half arcs
  if (Math.abs(endAngle - startAngle) >= 360 - 1e-6) {
    const top = polarToCartesian(cx, cy, r, 0);
    const bottom = polarToCartesian(cx, cy, r, 180);
    return `M ${top.x} ${top.y} A ${r} ${r} 0 1 1 ${bottom.x} ${bottom.y} A ${r} ${r} 0 1 1 ${top.x} ${top.y} Z`;
  }
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`;
}

export function PieChart({
  data = [],
  size = 320,
  showLegend = true,
  showPercent = true,
  valueFormat = (v) => v,
} = {}) {
  if (!Array.isArray(data) || data.length === 0) {
    return `<div class="chart-pie chart-pie--empty" role="img" aria-label="empty pie chart">(no data)</div>`;
  }
  const total = data.reduce((sum, d) => sum + (Number(d.value) || 0), 0);
  if (total <= 0) {
    return `<div class="chart-pie chart-pie--empty" role="img" aria-label="empty pie chart">(zero total)</div>`;
  }

  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 2;

  let cursor = 0;
  const slices = data.map((d, i) => {
    const value = Number(d.value) || 0;
    const startAngle = (cursor / total) * 360;
    cursor += value;
    const endAngle = (cursor / total) * 360;
    const midAngle = (startAngle + endAngle) / 2;
    const labelPos = polarToCartesian(cx, cy, r * 0.6, midAngle);
    const pct = (value / total) * 100;
    return {
      label: d.label ?? `series ${i + 1}`,
      value,
      color: d.color || TOKEN_COLORS[i % TOKEN_COLORS.length],
      d: arcPath(cx, cy, r, startAngle, endAngle),
      labelPos,
      pct,
    };
  });

  const ariaLabel = `pie chart: ${slices
    .map((s) => `${s.label} ${valueFormat(s.value)} (${s.pct.toFixed(1)}%)`)
    .join(', ')}`;

  const slicesSvg = slices
    .map((s) => {
      const titleText = `${escapeHtml(s.label)}: ${escapeHtml(valueFormat(s.value))} (${s.pct.toFixed(1)}%)`;
      const labelHtml = showPercent && s.pct >= 5
        ? `<text x="${s.labelPos.x.toFixed(2)}" y="${s.labelPos.y.toFixed(2)}" class="chart-pie__label" text-anchor="middle" dominant-baseline="central">${s.pct.toFixed(0)}%</text>`
        : '';
      return `<g class="chart-pie__slice"><path d="${s.d}" fill="${s.color}" stroke="var(--color-bg, #ffffff)" stroke-width="1.5"><title>${titleText}</title></path>${labelHtml}</g>`;
    })
    .join('');

  const legendHtml = showLegend
    ? `<ul class="chart-pie__legend" role="list">${slices
        .map(
          (s) =>
            `<li class="chart-pie__legend-item"><span class="chart-pie__swatch" style="background:${s.color}" aria-hidden="true"></span><span class="chart-pie__legend-label">${escapeHtml(s.label)}</span><span class="chart-pie__legend-value">${escapeHtml(valueFormat(s.value))} <small>(${s.pct.toFixed(1)}%)</small></span></li>`,
        )
        .join('')}</ul>`
    : '';

  return `<div class="chart-pie" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-pie__svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" focusable="false">${slicesSvg}</svg>${legendHtml}</div>`;
}

export default PieChart;

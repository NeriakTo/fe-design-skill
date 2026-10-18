/**
 * bar_chart.mjs — fe-design v1.4-short §24.10 P6.9
 *
 * SVG bar chart (vanilla, pure HTML string export). Supports horizontal and
 * vertical orientations. No runtime needed — uses SVG <title> for tooltips.
 * Token-aware: pulls from mckinsey-consulting.css `--chart-1..6`.
 *
 * Usage:
 *   import { BarChart } from '~/.claude/skills/starter-components/scaffolds/charts/bar_chart.mjs';
 *   const html = BarChart({
 *     data: [
 *       { label: 'Q1', value: 120 },
 *       { label: 'Q2', value: 150 },
 *       { label: 'Q3', value: 200, color: 'var(--chart-2)' },  // emphasis
 *     ],
 *     orientation: 'v',         // 'v' | 'h' (default 'v')
 *     width: 480,
 *     height: 320,
 *     max: 250,                 // optional, auto from data if omitted
 *     valueFormat: (v) => `${v}`,
 *     showValueLabels: true,    // print value on each bar
 *   });
 */

const escapeHtml = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const DEFAULT_COLOR = 'var(--chart-1, #003366)';

export function BarChart({
  data = [],
  orientation = 'v',
  width = 480,
  height = 320,
  max,
  valueFormat = (v) => v,
  showValueLabels = true,
  padding,
} = {}) {
  if (!Array.isArray(data) || data.length === 0) {
    return `<div class="chart-bar chart-bar--empty" role="img" aria-label="empty bar chart">(no data)</div>`;
  }
  const isHorizontal = orientation === 'h';
  // Default padding diverges by orientation: horizontal needs more left gutter
  // for category labels (~6 CJK chars at fs-caption); vertical uses original 48.
  if (!padding) {
    padding = isHorizontal
      ? { top: 16, right: 24, bottom: 24, left: 96 }
      : { top: 16, right: 16, bottom: 32, left: 48 };
  }
  const values = data.map((d) => Number(d.value) || 0);
  const dataMax = Math.max(...values, 0);
  const scaleMax = (typeof max === 'number' && max > 0) ? max : (dataMax > 0 ? dataMax : 1);

  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const slotSize = isHorizontal ? innerH / data.length : innerW / data.length;
  const barThickness = slotSize * 0.6;
  const barGap = (slotSize - barThickness) / 2;

  const ariaLabel = `bar chart: ${data
    .map((d) => `${d.label ?? ''} ${valueFormat(Number(d.value) || 0)}`)
    .join(', ')}`;

  const bars = data.map((d, i) => {
    const value = Number(d.value) || 0;
    const ratio = value / scaleMax;
    const color = d.color || DEFAULT_COLOR;
    const label = d.label ?? `bar ${i + 1}`;
    const titleText = `${escapeHtml(label)}: ${escapeHtml(valueFormat(value))}`;

    if (isHorizontal) {
      const y = padding.top + i * slotSize + barGap;
      const w = innerW * ratio;
      const x = padding.left;
      const labelX = padding.left - 8;
      const labelY = y + barThickness / 2;
      const valueX = x + w + 4;
      const valueY = y + barThickness / 2;
      return `<g class="chart-bar__bar"><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w.toFixed(2)}" height="${barThickness.toFixed(2)}" fill="${color}" rx="2"><title>${titleText}</title></rect><text x="${labelX.toFixed(2)}" y="${labelY.toFixed(2)}" class="chart-bar__category" text-anchor="end" dominant-baseline="central">${escapeHtml(label)}</text>${showValueLabels ? `<text x="${valueX.toFixed(2)}" y="${valueY.toFixed(2)}" class="chart-bar__value" text-anchor="start" dominant-baseline="central">${escapeHtml(valueFormat(value))}</text>` : ''}</g>`;
    } else {
      const x = padding.left + i * slotSize + barGap;
      const h = innerH * ratio;
      const y = padding.top + innerH - h;
      const labelY = padding.top + innerH + 18;
      const labelX = x + barThickness / 2;
      const valueX = x + barThickness / 2;
      const valueY = y - 6;
      return `<g class="chart-bar__bar"><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${barThickness.toFixed(2)}" height="${h.toFixed(2)}" fill="${color}" rx="2"><title>${titleText}</title></rect><text x="${labelX.toFixed(2)}" y="${labelY.toFixed(2)}" class="chart-bar__category" text-anchor="middle" dominant-baseline="hanging">${escapeHtml(label)}</text>${showValueLabels && h > 0 ? `<text x="${valueX.toFixed(2)}" y="${valueY.toFixed(2)}" class="chart-bar__value" text-anchor="middle" dominant-baseline="alphabetic">${escapeHtml(valueFormat(value))}</text>` : ''}</g>`;
    }
  }).join('');

  const baseline = isHorizontal
    ? `<line x1="${padding.left}" y1="${padding.top + innerH}" x2="${padding.left}" y2="${padding.top}" class="chart-bar__axis" />`
    : `<line x1="${padding.left}" y1="${padding.top + innerH}" x2="${padding.left + innerW}" y2="${padding.top + innerH}" class="chart-bar__axis" />`;

  return `<div class="chart-bar chart-bar--${isHorizontal ? 'h' : 'v'}" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-bar__svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" focusable="false">${baseline}${bars}</svg></div>`;
}

export default BarChart;

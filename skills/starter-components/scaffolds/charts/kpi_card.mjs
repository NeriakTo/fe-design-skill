/**
 * kpi_card.mjs — fe-design v1.4-short §24.10 P6.9
 *
 * KPI card (HTML string, no SVG). Shows a large headline number with optional
 * change indicator. Token-aware: pulls from mckinsey-consulting.css
 * `--kpi-card-*` and `--color-*`.
 *
 * Usage:
 *   import { KpiCard } from '~/.claude/skills/starter-components/scaffolds/charts/kpi_card.mjs';
 *   const html = KpiCard({
 *     value: 30,
 *     prefix: '+',
 *     suffix: '%',
 *     label: 'Q2 營收成長率',
 *     change: 5.2,           // optional, % change vs prior period
 *     changeDirection: 'up', // 'up' | 'down' | 'neutral' (auto-derived from sign if omitted)
 *     comparator: 'vs Q1',   // optional, prints under change
 *   });
 *
 * Accessibility: aria-label combines value + label + change for screen readers.
 */

const escapeHtml = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

function autoDirection(change) {
  if (change === undefined || change === null || isNaN(Number(change))) return null;
  const n = Number(change);
  if (n > 0) return 'up';
  if (n < 0) return 'down';
  return 'neutral';
}

const DIRECTION_GLYPH = { up: '▲', down: '▼', neutral: '–' };

export function KpiCard({
  value,
  prefix = '',
  suffix = '',
  label = '',
  change,
  changeDirection,
  comparator,
  size = 'md', // 'sm' | 'md' | 'lg'
} = {}) {
  if (value === undefined || value === null || value === '') {
    return `<div class="kpi-card kpi-card--empty" role="group" aria-label="empty KPI card"></div>`;
  }
  const direction = changeDirection || autoDirection(change);
  const hasChange = change !== undefined && change !== null && !isNaN(Number(change)) && direction;
  const changeAbs = hasChange ? Math.abs(Number(change)) : null;
  const glyph = direction ? DIRECTION_GLYPH[direction] || '' : '';

  // Build aria parts from RAW strings; escapeHtml is applied once when
  // interpolating the final attribute (avoids double-escape `&` → `&amp;` → `&amp;amp;`)
  const ariaParts = [];
  if (label) ariaParts.push(label);
  ariaParts.push(`${prefix}${value}${suffix}`);
  if (hasChange) ariaParts.push(`change ${direction} ${changeAbs}%`);
  const ariaLabel = ariaParts.join(', ');

  const changeHtml = hasChange
    ? `<div class="kpi-card__change kpi-card__change--${direction}" aria-hidden="true"><span class="kpi-card__change-glyph">${glyph}</span><span class="kpi-card__change-value">${escapeHtml(changeAbs)}%</span>${comparator ? `<span class="kpi-card__comparator">${escapeHtml(comparator)}</span>` : ''}</div>`
    : '';

  return `<div class="kpi-card kpi-card--${escapeHtml(size)}" role="group" aria-label="${escapeHtml(ariaLabel)}"><div class="kpi-card__value"><span class="kpi-card__prefix">${escapeHtml(prefix)}</span><span class="kpi-card__number">${escapeHtml(value)}</span><span class="kpi-card__suffix">${escapeHtml(suffix)}</span></div>${label ? `<div class="kpi-card__label">${escapeHtml(label)}</div>` : ''}${changeHtml}</div>`;
}

export default KpiCard;

// matrix_chart.mjs — 矩陣圖（2x2 / NxN 網格）
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
];

export function MatrixChart({
  cells = [],
  rowLabels = [],
  colLabels = [],
  width = 480,
  height,
} = {}) {
  if (!Array.isArray(rowLabels) || rowLabels.length === 0 ||
      !Array.isArray(colLabels) || colLabels.length === 0) {
    return `<div class="chart-matrix chart-matrix--empty" role="img" aria-label="empty matrix chart">(no data)</div>`;
  }

  const rows = rowLabels.length;
  const cols = colLabels.length;

  // 佈局參數
  const padding = { top: 36, right: 16, bottom: 16, left: 80 };
  const autoHeight = height || (padding.top + rows * 64 + padding.bottom);
  const innerW = width - padding.left - padding.right;
  const innerH = autoHeight - padding.top - padding.bottom;
  const cellW = innerW / cols;
  const cellH = innerH / rows;

  // 建立 cell 查找表（key: "row,col"）
  const cellMap = new Map();
  cells.forEach((c) => {
    if (typeof c.row === 'number' && typeof c.col === 'number' &&
        c.row >= 0 && c.row < rows && c.col >= 0 && c.col < cols) {
      cellMap.set(`${c.row},${c.col}`, c);
    }
  });

  // aria-label
  const ariaLabel = `matrix chart: ${rows} rows x ${cols} columns`;

  // 繪製欄標題（頂部）
  const colLabelsSvg = colLabels.map((label, ci) => {
    const x = padding.left + ci * cellW + cellW / 2;
    const y = padding.top - 10;
    return `<text x="${x.toFixed(2)}" y="${y.toFixed(2)}" class="chart-matrix__col-label" text-anchor="middle" dominant-baseline="alphabetic">${escapeHtml(label)}</text>`;
  }).join('');

  // 繪製列標題（左側）
  const rowLabelsSvg = rowLabels.map((label, ri) => {
    const x = padding.left - 10;
    const y = padding.top + ri * cellH + cellH / 2;
    return `<text x="${x.toFixed(2)}" y="${y.toFixed(2)}" class="chart-matrix__row-label" text-anchor="end" dominant-baseline="central">${escapeHtml(label)}</text>`;
  }).join('');

  // 繪製格子
  const cellsSvg = [];
  for (let ri = 0; ri < rows; ri++) {
    for (let ci = 0; ci < cols; ci++) {
      const x = padding.left + ci * cellW;
      const y = padding.top + ri * cellH;
      const cell = cellMap.get(`${ri},${ci}`);

      // 背景色：用 cell.color 或依序循環 token 色（低透明度）
      const colorIndex = ri * cols + ci;
      const centerX = x + cellW / 2;
      const centerY = y + cellH / 2;

      if (!cell) {
        cellsSvg.push(`<g class="chart-matrix__cell chart-matrix__cell--empty"><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${cellW.toFixed(2)}" height="${cellH.toFixed(2)}" fill="none" stroke="var(--color-divider, #e5e7eb)" stroke-width="1" stroke-dasharray="4,4" /></g>`);
        continue;
      }

      const bgColor = cell.color || TOKEN_COLORS[colorIndex % TOKEN_COLORS.length];
      const label = cell.label ?? '';
      const value = cell.value ?? '';
      const titleText = label ? `${escapeHtml(label)}${value !== '' ? `: ${escapeHtml(String(value))}` : ''}` : '';
      const hasValue = value !== '';

      const labelText = label
        ? `<text x="${centerX.toFixed(2)}" y="${(hasValue ? centerY - 8 : centerY).toFixed(2)}" class="chart-matrix__cell-label" text-anchor="middle" dominant-baseline="central">${escapeHtml(label)}</text>`
        : '';
      const valueText = hasValue
        ? `<text x="${centerX.toFixed(2)}" y="${(centerY + (label ? 10 : 0)).toFixed(2)}" class="chart-matrix__cell-value" text-anchor="middle" dominant-baseline="central">${escapeHtml(String(value))}</text>`
        : '';

      cellsSvg.push(`<g class="chart-matrix__cell"><rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${cellW.toFixed(2)}" height="${cellH.toFixed(2)}" fill="${bgColor}" opacity="0.18" stroke="var(--color-divider, #e5e7eb)" stroke-width="1">${titleText ? `<title>${titleText}</title>` : ''}</rect>${labelText}${valueText}</g>`);
    }
  }

  return `<div class="chart-matrix" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-matrix__svg" viewBox="0 0 ${width} ${autoHeight}" width="${width}" height="${autoHeight}" focusable="false">${colLabelsSvg}${rowLabelsSvg}${cellsSvg.join('')}</svg></div>`;
}

export default MatrixChart;

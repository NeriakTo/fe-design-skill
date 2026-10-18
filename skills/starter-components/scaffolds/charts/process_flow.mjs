// process_flow.mjs — 流程圖（步驟 + 箭頭連接線）
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

// 狀態色對應
const STATUS_COLORS = {
  done: 'var(--process-done, var(--chart-3, #15803d))',
  active: 'var(--process-active, var(--chart-1, #003366))',
  pending: 'var(--process-pending, var(--color-text-muted, #4a5568))',
};

export function ProcessFlow({
  steps = [],
  direction = 'horizontal',
  width,
} = {}) {
  if (!Array.isArray(steps) || steps.length === 0) {
    return `<div class="chart-process chart-process--empty" role="img" aria-label="empty process flow">(no data)</div>`;
  }

  const isHorizontal = direction === 'horizontal';

  // 佈局參數
  const nodeRadius = 14;
  const stepSpacing = isHorizontal ? 160 : 100;
  const padding = { top: 24, right: 40, bottom: 24, left: 40 };

  // 計算畫布尺寸
  const autoWidth = width || (isHorizontal
    ? padding.left + steps.length * stepSpacing + padding.right
    : 320);
  const autoHeight = isHorizontal
    ? 140
    : padding.top + steps.length * stepSpacing + padding.bottom;

  // aria-label
  const ariaLabel = `process flow: ${steps.map((s, i) => `${i + 1}. ${s.label} (${s.status || 'pending'})`).join(', ')}`;

  // 計算每個節點的中心座標
  const nodes = steps.map((s, i) => {
    const status = s.status || 'pending';
    const cx = isHorizontal
      ? padding.left + stepSpacing / 2 + i * stepSpacing
      : autoWidth / 2;
    const cy = isHorizontal
      ? 48
      : padding.top + stepSpacing / 2 + i * stepSpacing;
    return {
      label: s.label ?? `step ${i + 1}`,
      description: s.description || '',
      icon: s.icon || '',
      status,
      color: STATUS_COLORS[status] || STATUS_COLORS.pending,
      cx,
      cy,
    };
  });

  // 繪製箭頭連接線
  const arrowsSvg = nodes.map((node, i) => {
    if (i === 0) return '';
    const prev = nodes[i - 1];
    if (isHorizontal) {
      const x1 = prev.cx + nodeRadius + 4;
      const x2 = node.cx - nodeRadius - 8;
      const y = prev.cy;
      // 箭頭三角（右指）
      const arrowX = node.cx - nodeRadius - 2;
      return `<line x1="${x1.toFixed(2)}" y1="${y.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y.toFixed(2)}" class="chart-process__arrow" /><polygon points="${arrowX},${y - 4} ${arrowX + 6},${y} ${arrowX},${y + 4}" class="chart-process__arrowhead" fill="var(--color-text-muted, #4a5568)" />`;
    } else {
      const y1 = prev.cy + nodeRadius + 4;
      const y2 = node.cy - nodeRadius - 8;
      const x = prev.cx;
      // 箭頭三角（下指）
      const arrowY = node.cy - nodeRadius - 2;
      return `<line x1="${x.toFixed(2)}" y1="${y1.toFixed(2)}" x2="${x.toFixed(2)}" y2="${y2.toFixed(2)}" class="chart-process__arrow" /><polygon points="${x - 4},${arrowY} ${x + 4},${arrowY} ${x},${arrowY + 6}" class="chart-process__arrowhead" fill="var(--color-text-muted, #4a5568)" />`;
    }
  }).join('');

  // 繪製節點
  const nodesSvg = nodes.map((n) => {
    const { cx, cy, label, description, status, color } = n;
    const titleText = `${escapeHtml(label)}${description ? ` - ${escapeHtml(description)}` : ''} (${status})`;

    // done=實心圓、active=脈動圓、pending=空心圓
    let circleHtml;
    if (status === 'done') {
      // 實心圓 + 勾號
      circleHtml = `<circle cx="${cx}" cy="${cy}" r="${nodeRadius}" fill="${color}" class="chart-process__node chart-process__node--done"><title>${titleText}</title></circle><polyline points="${cx - 5},${cy} ${cx - 1},${cy + 5} ${cx + 6},${cy - 4}" fill="none" stroke="var(--color-bg, #ffffff)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" pointer-events="none" />`;
    } else if (status === 'active') {
      // 脈動圓（CSS 動畫透過 class 控制）
      circleHtml = `<circle cx="${cx}" cy="${cy}" r="${nodeRadius}" fill="${color}" class="chart-process__node chart-process__node--active"><title>${titleText}</title></circle><circle cx="${cx}" cy="${cy}" r="${nodeRadius}" fill="none" stroke="${color}" stroke-width="2" class="chart-process__pulse" opacity="0.5" />`;
    } else {
      // 空心圓
      circleHtml = `<circle cx="${cx}" cy="${cy}" r="${nodeRadius}" fill="none" stroke="${color}" stroke-width="2" class="chart-process__node chart-process__node--pending"><title>${titleText}</title></circle>`;
    }

    // 標籤文字（水平：節點下方；垂直：節點右側）
    let labelHtml;
    if (isHorizontal) {
      labelHtml = `<text x="${cx.toFixed(2)}" y="${(cy + nodeRadius + 16).toFixed(2)}" class="chart-process__label" text-anchor="middle" dominant-baseline="hanging">${escapeHtml(label)}</text>`;
      if (description) {
        labelHtml += `<text x="${cx.toFixed(2)}" y="${(cy + nodeRadius + 32).toFixed(2)}" class="chart-process__desc" text-anchor="middle" dominant-baseline="hanging">${escapeHtml(description)}</text>`;
      }
    } else {
      labelHtml = `<text x="${(cx + nodeRadius + 12).toFixed(2)}" y="${cy.toFixed(2)}" class="chart-process__label" text-anchor="start" dominant-baseline="central">${escapeHtml(label)}</text>`;
      if (description) {
        labelHtml += `<text x="${(cx + nodeRadius + 12).toFixed(2)}" y="${(cy + 16).toFixed(2)}" class="chart-process__desc" text-anchor="start" dominant-baseline="central">${escapeHtml(description)}</text>`;
      }
    }

    return `<g class="chart-process__step">${circleHtml}${labelHtml}</g>`;
  }).join('');

  return `<div class="chart-process chart-process--${isHorizontal ? 'h' : 'v'}" role="img" aria-label="${escapeHtml(ariaLabel)}"><svg class="chart-process__svg" viewBox="0 0 ${autoWidth} ${autoHeight}" width="${autoWidth}" height="${autoHeight}" focusable="false">${arrowsSvg}${nodesSvg}</svg></div>`;
}

export default ProcessFlow;

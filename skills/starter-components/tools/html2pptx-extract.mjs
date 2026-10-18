// html2pptx-extract.mjs — browser-side DOM 遍歷邏輯
// 此函式整體傳入 page.evaluate()，在 browser context 執行
// 不可引用模組層級的常數或 import（Playwright 會序列化此函式）

export function extractSlideElements(slideEl, slideIndex) {
  // KEEP IN SYNC with html2pptx-render.mjs::CORE_TEXT_TAGS (browser context cannot import)
  const CORE_TAGS = new Set(['H1','H2','H3','H4','H5','H6','P','UL','OL','LI']);
  // KEEP IN SYNC with html2pptx-render.mjs::INLINE_DISPLAY
  const INLINE_DISP = new Set(['inline','inline-block','inline-flex']);

  function createsStackingContext(style) {
    const pos = style.position;
    const zIdx = style.zIndex;
    if ((pos === 'absolute' || pos === 'fixed' || pos === 'relative' || pos === 'sticky')
        && zIdx !== 'auto') return true;
    if (parseFloat(style.opacity) < 1) return true;
    if (style.transform && style.transform !== 'none'
        && style.transform !== 'matrix(1, 0, 0, 1, 0, 0)') return true;
    if (style.filter && style.filter !== 'none') return true;
    if (style.isolation === 'isolate') return true;
    if (style.mixBlendMode && style.mixBlendMode !== 'normal') return true;
    const wc = style.willChange;
    if (wc && (wc.includes('transform') || wc.includes('opacity') || wc.includes('filter'))) return true;
    return false;
  }

  function extractInlineRuns(el) {
    const runs = [];
    let totalLen = 0;
    const MAX_TOTAL = 2000;

    function walkInline(node) {
      if (totalLen >= MAX_TOTAL) return;

      if (node.nodeType === 3) {
        const text = node.textContent;
        if (text.length > 0) {
          const parentStyle = getComputedStyle(node.parentElement);
          const remaining = MAX_TOTAL - totalLen;
          const sliced = text.length > remaining ? text.slice(0, remaining) : text;
          runs.push({
            text: sliced,
            fontSize: parentStyle.fontSize,
            fontFamily: parentStyle.fontFamily,
            fontWeight: parentStyle.fontWeight,
            fontStyle: parentStyle.fontStyle,
            color: parentStyle.color,
          });
          totalLen += sliced.length;
        }
        return;
      }

      if (node.nodeType !== 1) return;

      if (node.tagName === 'BR') {
        runs.push({ text: '\n', fontSize: '16px', fontFamily: 'system-ui', fontWeight: '400', fontStyle: 'normal', color: 'rgb(0,0,0)' });
        return;
      }

      for (const child of node.childNodes) {
        walkInline(child);
      }
    }

    for (const child of el.childNodes) {
      walkInline(child);
    }

    const merged = [];
    for (const run of runs) {
      const prev = merged[merged.length - 1];
      if (prev && prev.fontSize === run.fontSize && prev.fontFamily === run.fontFamily
          && prev.fontWeight === run.fontWeight && prev.fontStyle === run.fontStyle
          && prev.color === run.color) {
        prev.text += run.text;
      } else {
        merged.push({ ...run });
      }
    }

    return merged;
  }

  function collectElement(el, depth) {
    const style = getComputedStyle(el);
    if (style.display === 'none') return null;
    if (style.visibility === 'hidden') return null;
    if (parseFloat(style.opacity) === 0) return null;

    const rect = el.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;

    const hasDirectText = Array.from(el.childNodes)
      .some(n => n.nodeType === 3 && n.textContent.trim().length > 0);

    const hasInlineChildren = !hasDirectText && CORE_TAGS.has(el.tagName)
      && Array.from(el.children).some(c => INLINE_DISP.has(getComputedStyle(c).display));

    const hasPositionedChildren = Array.from(el.children).some(child => {
      const cs = getComputedStyle(child);
      return cs.position === 'absolute' || cs.position === 'fixed';
    });

    const hasTransform = style.transform && style.transform !== 'none'
      && style.transform !== 'matrix(1, 0, 0, 1, 0, 0)';

    let inlineRuns = null;
    if (hasDirectText || hasInlineChildren) {
      inlineRuns = extractInlineRuns(el);
    }

    const bw = [style.borderTopWidth, style.borderRightWidth, style.borderBottomWidth, style.borderLeftWidth];
    const bc = [style.borderTopColor, style.borderRightColor, style.borderBottomColor, style.borderLeftColor];
    const bs = [style.borderTopStyle, style.borderRightStyle, style.borderBottomStyle, style.borderLeftStyle];
    const borderUniform = bw.every(w => w === bw[0]) && bc.every(c => c === bc[0]) && bs.every(s => s === bs[0]);
    const borderRadiusValue = style.borderRadius.split(' ')[0];

    let listType = null;
    if (el.tagName === 'LI') {
      const parent = el.parentElement;
      if (parent) listType = parent.tagName === 'OL' ? 'ol' : 'ul';
    }

    const pptxIdx = `${slideIndex}-${depth}-${Array.from(el.parentElement?.children || []).indexOf(el)}`;
    if (hasTransform) {
      el.setAttribute('data-pptx-idx', pptxIdx);
    }

    return {
      tagName: el.tagName,
      hasDirectText,
      hasInlineChildren,
      hasPositionedChildren,
      hasTransform,
      pptxIdx: hasTransform ? pptxIdx : null,
      depth,
      rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
      style: {
        fontSize: style.fontSize,
        fontFamily: style.fontFamily,
        fontWeight: style.fontWeight,
        fontStyle: style.fontStyle,
        color: style.color,
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
        textAlign: style.textAlign,
        position: style.position,
        zIndex: style.zIndex,
        transform: style.transform,
        filter: style.filter,
        opacity: style.opacity,
      },
      isImg: el.tagName === 'IMG',
      isSvg: el.tagName === 'SVG' || el.closest('svg') !== null,
      isCanvas: el.tagName === 'CANVAS',
      inlineRuns,
      listType,
      borderUniform,
      borderWidth: bw[0],
      borderColor: bc[0],
      borderStyle: bs[0],
      borderRadiusValue,
      borderHasAny: bw.some(w => parseFloat(w) > 0 && bs[bw.indexOf(w)] !== 'none'),
    };
  }

  const paintOrder = [];
  let scCount = 0;
  let maxDepth = 0;

  function buildAndTraverse(el, scDepth) {
    const style = getComputedStyle(el);
    if (style.display === 'none') return;
    if (style.visibility === 'hidden') return;
    if (parseFloat(style.opacity) === 0) return;

    const isNewSC = createsStackingContext(style);
    if (isNewSC) {
      scCount++;
      if (scDepth + 1 > maxDepth) maxDepth = scDepth + 1;
    }

    const elemData = collectElement(el, scDepth);

    const isLeaf = elemData && (
      elemData.hasDirectText || elemData.hasInlineChildren
      || elemData.isImg || elemData.isCanvas || elemData.isSvg
    );

    if (elemData) {
      const children = Array.from(el.children);
      const negZChildren = [];
      const nonNegChildren = [];

      for (const child of children) {
        const cs = getComputedStyle(child);
        if (cs.display === 'none') continue;
        const zi = parseInt(cs.zIndex, 10);
        if (!isNaN(zi) && zi < 0) {
          negZChildren.push({ el: child, zIndex: zi });
        } else {
          nonNegChildren.push({ el: child, zIndex: isNaN(zi) ? 0 : zi });
        }
      }

      negZChildren.sort((a, b) => a.zIndex - b.zIndex);

      for (const nc of negZChildren) {
        buildAndTraverse(nc.el, isNewSC ? scDepth + 1 : scDepth);
      }

      paintOrder.push(elemData);

      if (!isLeaf) {
        nonNegChildren.sort((a, b) => a.zIndex - b.zIndex);
        for (const nc of nonNegChildren) {
          if (elemData.hasInlineChildren || elemData.hasDirectText) {
            const childStyle = getComputedStyle(nc.el);
            if (INLINE_DISP.has(childStyle.display)) continue;
          }
          buildAndTraverse(nc.el, isNewSC ? scDepth + 1 : scDepth);
        }
      }
    } else {
      const children = Array.from(el.children);
      for (const child of children) {
        buildAndTraverse(child, scDepth);
      }
    }
  }

  const slideChildren = Array.from(slideEl.children);
  const negZ = [];
  const nonNeg = [];
  for (const child of slideChildren) {
    const cs = getComputedStyle(child);
    if (cs.display === 'none') continue;
    const zi = parseInt(cs.zIndex, 10);
    if (!isNaN(zi) && zi < 0) {
      negZ.push({ el: child, zIndex: zi });
    } else {
      nonNeg.push({ el: child, zIndex: isNaN(zi) ? 0 : zi });
    }
  }
  negZ.sort((a, b) => a.zIndex - b.zIndex);
  nonNeg.sort((a, b) => a.zIndex - b.zIndex);
  for (const c of negZ) buildAndTraverse(c.el, 0);
  for (const c of nonNeg) buildAndTraverse(c.el, 0);

  return { elements: paintOrder, scCount, maxDepth };
}

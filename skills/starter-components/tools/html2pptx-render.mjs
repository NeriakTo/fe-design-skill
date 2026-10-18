// html2pptx-render.mjs — pptxgenjs 渲染輔助函式 + 常數

export const EFFECTIVE_DPI = 144;
export const PT_PER_INCH = 72;
export const FONT_DIVISOR = EFFECTIVE_DPI / PT_PER_INCH;

export const DEFAULT_FONT_MAP = {
  'Noto Sans TC': '微軟正黑體',
  'Noto Serif TC': '新細明體',
  'Source Serif 4': 'Times New Roman',
  'Inter': 'Calibri',
  'system-ui': 'Calibri',
};

// KEEP IN SYNC with html2pptx-extract.mjs::CORE_TAGS (duplicated for browser isolation)
export const CORE_TEXT_TAGS = new Set([
  'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
  'P', 'UL', 'OL', 'LI',
]);

export const INLINE_DISPLAY = new Set(['inline', 'inline-block', 'inline-flex']);

export function rgbToHex(rgbStr) {
  const m = rgbStr.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  if (!m) return '000000';
  return [m[1], m[2], m[3]]
    .map(n => parseInt(n, 10).toString(16).padStart(2, '0'))
    .join('');
}

export function isTransparent(bgColor) {
  if (!bgColor) return true;
  if (bgColor === 'transparent') return true;
  if (bgColor === 'rgba(0, 0, 0, 0)') return true;
  const m = bgColor.match(/rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([\d.]+)\s*\)/);
  return m && parseFloat(m[1]) === 0;
}

export function hasGradient(bgImage) {
  if (!bgImage || bgImage === 'none') return false;
  return /gradient\(/.test(bgImage);
}

export function parseFontFamily(fontFamilyStr, fontMap) {
  const first = fontFamilyStr
    .split(',')[0]
    .trim()
    .replace(/^["']|["']$/g, '');
  return fontMap[first] || first;
}

export function pxToInch(px) {
  return px / EFFECTIVE_DPI;
}

export function pxToPt(px) {
  return px / FONT_DIVISOR;
}

export function buildTextContent(runs, fontMap) {
  if (!runs || runs.length === 0) return null;
  if (runs.length === 1) {
    const r = runs[0];
    return {
      text: r.text,
      options: {
        fontSize: pxToPt(parseFloat(r.fontSize)),
        fontFace: parseFontFamily(r.fontFamily, fontMap),
        color: rgbToHex(r.color),
        bold: parseInt(r.fontWeight, 10) >= 700 || r.fontWeight === 'bold',
        italic: r.fontStyle === 'italic' || r.fontStyle === 'oblique',
      },
      isSingle: true,
    };
  }
  return {
    runs: runs.map(r => ({
      text: r.text,
      options: {
        fontSize: pxToPt(parseFloat(r.fontSize)),
        fontFace: parseFontFamily(r.fontFamily, fontMap),
        color: rgbToHex(r.color),
        bold: parseInt(r.fontWeight, 10) >= 700 || r.fontWeight === 'bold',
        italic: r.fontStyle === 'italic' || r.fontStyle === 'oblique',
      },
    })),
    isSingle: false,
  };
}

export function buildBorderLine(elem) {
  if (!elem.borderUniform) return null;
  if (elem.borderStyle === 'none' || elem.borderStyle === 'hidden') return null;
  const width = parseFloat(elem.borderWidth);
  if (!(width > 0)) return null;
  return {
    color: rgbToHex(elem.borderColor),
    width: pxToPt(width),
    dashType: elem.borderStyle === 'dashed' ? 'dash'
            : elem.borderStyle === 'dotted' ? 'sysDot'
            : 'solid',
  };
}

export function computeRectRadius(elem) {
  const r = parseFloat(elem.borderRadiusValue);
  if (!(r > 0)) return 0;
  const shortSide = Math.min(elem.rect.width, elem.rect.height);
  if (shortSide <= 0) return 0;
  return Math.min(r / (shortSide / 2), 1.0);
}

export async function screenshotByLocator(locator) {
  return await locator.screenshot({ type: 'png' });
}

export async function screenshotByClip(page, rect) {
  const clip = { x: rect.left, y: rect.top, width: rect.width, height: rect.height };
  return await page.screenshot({ type: 'png', clip });
}

export function addScreenshotToSlide(pptxSlide, buffer, pos) {
  pptxSlide.addImage({
    data: `data:image/png;base64,${buffer.toString('base64')}`,
    x: pos.x, y: pos.y, w: pos.w, h: pos.h,
  });
}

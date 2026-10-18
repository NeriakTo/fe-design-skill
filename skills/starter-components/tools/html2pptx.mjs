#!/usr/bin/env node
// html2pptx.mjs — 語義級 HTML → PPTX 翻譯器（主要）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.1a, v1.6 P8.1-P8.4, v1.7 refactor)
//
// 三檔架構：
//   html2pptx.mjs        — 主要流程 + args + browser launch + slide loop
//   html2pptx-extract.mjs — browser-side DOM 遍歷（page.evaluate 用）
//   html2pptx-render.mjs  — pptxgenjs 渲染輔助函式 + 常數
//
// Usage:
//   node html2pptx.mjs --input <html> --output <pptx> [flags]

import { readFile, mkdir, stat } from 'node:fs/promises';
import { resolve as resolvePath, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

import { extractSlideElements } from './html2pptx-extract.mjs';
import {
  DEFAULT_FONT_MAP, CORE_TEXT_TAGS,
  rgbToHex, isTransparent, hasGradient, parseFontFamily,
  pxToInch, pxToPt,
  buildTextContent, buildBorderLine, computeRectRadius,
  screenshotByLocator, screenshotByClip, addScreenshotToSlide,
} from './html2pptx-render.mjs';

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  const cwdRequire = createRequire(resolvePath(process.cwd(), 'package.json'));
  try { return cwdRequire('playwright'); } catch (e) {
    throw new Error(
      `playwright 找不到。請於 case 工作目錄 (cwd: ${process.cwd()}) 執行 \`npm install playwright\`。`
    );
  }
}

async function loadPptxGenJS() {
  try { return (await import('pptxgenjs')).default; } catch {}
  const cwdRequire = createRequire(resolvePath(process.cwd(), 'package.json'));
  try { return cwdRequire('pptxgenjs'); } catch (e) {
    throw new Error(
      `pptxgenjs 找不到。請於 case 工作目錄 (cwd: ${process.cwd()}) 執行 \`npm install pptxgenjs\`。`
    );
  }
}

function getPptxVersion() {
  try {
    const cwdRequire = createRequire(resolvePath(process.cwd(), 'package.json'));
    return cwdRequire('pptxgenjs/package.json').version;
  } catch {}
  try {
    const selfRequire = createRequire(import.meta.url);
    return selfRequire('pptxgenjs/package.json').version;
  } catch {}
  return 'unknown';
}

function parseArgs(argv) {
  const args = {
    input: null,
    output: null,
    fontMapPath: null,
    slideSelector: 'section.slide',
    viewport: { width: 1920, height: 1080 },
    quiet: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input') args.input = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--font-map') args.fontMapPath = argv[++i];
    else if (a === '--slide-selector') args.slideSelector = argv[++i];
    else if (a === '--viewport') {
      const [w, h] = argv[++i].split('x').map(n => parseInt(n, 10));
      args.viewport = { width: w, height: h };
    }
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') { printUsage(); process.exit(0); }
  }
  if (!args.input || !args.output) {
    console.error('❌ --input 和 --output 為必填');
    printUsage();
    process.exit(2);
  }
  return args;
}

function printUsage() {
  console.log(`Usage: node html2pptx.mjs --input <html> --output <pptx> [flags]

Flags:
  --font-map <json>       自訂 fontFace 映射表 JSON 檔
  --slide-selector <sel>  slide CSS selector（default: section.slide）
  --viewport WxH          viewport 大小（default 1920x1080）
  --quiet, -q
`);
}

async function main() {
  const args = parseArgs(process.argv);
  const log = args.quiet ? () => {} : console.log;

  let fontMap = { ...DEFAULT_FONT_MAP };
  if (args.fontMapPath) {
    const custom = JSON.parse(await readFile(resolvePath(args.fontMapPath), 'utf-8'));
    fontMap = { ...fontMap, ...custom };
  }

  const inputUrl = pathToFileURL(resolvePath(args.input)).href;
  const outputPath = resolvePath(args.output);
  await mkdir(dirname(outputPath), { recursive: true });

  const { chromium } = await loadPlaywright();
  const PptxGenJS = await loadPptxGenJS();
  const pptxVersion = getPptxVersion();

  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';

  const browser = await chromium.launch({
    headless: true,
    args: ['--allow-file-access-from-files'],
  });

  const allSlideStats = [];

  try {
    const ctx = await browser.newContext({
      viewport: args.viewport,
      deviceScaleFactor: 1,
    });
    const page = await ctx.newPage();

    if (!args.quiet) {
      page.on('console', msg => log(`  [browser ${msg.type()}]`, msg.text()));
      page.on('pageerror', err => log(`  [browser ERROR]`, err.message));
    }

    log(`→ loading ${inputUrl}`);
    await page.goto(inputUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.evaluate(() => document.fonts.ready).catch(() => null);
    await page.waitForTimeout(1500);

    const hasDeckStage = await page.evaluate(() => !!window.__deck);
    if (hasDeckStage) {
      log('  detected deck_stage.js — entering print mode');
      await page.evaluate(() => window.__deck.togglePrint());
      await page.waitForTimeout(500);
    }

    const slideCount = await page.locator(args.slideSelector).count();
    log(`  found ${slideCount} slides`);

    if (slideCount === 0) {
      throw new Error(`找不到 slide（selector: "${args.slideSelector}"）`);
    }

    for (let si = 0; si < slideCount; si++) {
      log(`  [${si + 1}/${slideCount}] translating slide...`);

      const slideHandle = page.locator(args.slideSelector).nth(si);
      const slideBox = await slideHandle.boundingBox();
      if (!slideBox) {
        log(`    ⚠ slide ${si + 1} 無 boundingBox — 跳過`);
        continue;
      }

      const pptxSlide = pptx.addSlide();
      let semanticCount = 0;
      let fallbackCount = 0;
      let coreTextSemantic = true;
      let stackingContextsCount = 0;
      let maxNestingDepth = 0;
      let transformElements = 0;
      let transformScreenshotFallbacks = 0;
      let richTextElements = 0;
      let totalInlineRuns = 0;
      let borderedElements = 0;
      let borderMapped = 0;
      let borderSkippedAsymmetric = 0;

      try {

      const slideBg = await slideHandle.evaluate(el => {
        const s = getComputedStyle(el);
        return { bgColor: s.backgroundColor, bgImage: s.backgroundImage };
      });

      if (!isTransparent(slideBg.bgColor) && !hasGradient(slideBg.bgImage)) {
        pptxSlide.background = { color: rgbToHex(slideBg.bgColor) };
      } else if (hasGradient(slideBg.bgImage)) {
        const screenshotBuf = await screenshotByLocator(slideHandle);
        pptxSlide.background = {
          data: `data:image/png;base64,${screenshotBuf.toString('base64')}`,
        };
        fallbackCount++;
      }

      const elements = await slideHandle.evaluate(extractSlideElements, si);

      stackingContextsCount = elements.scCount;
      maxNestingDepth = elements.maxDepth;

      for (const elem of elements.elements) {
        const relX = elem.rect.left - slideBox.x;
        const relY = elem.rect.top - slideBox.y;
        const inchX = pxToInch(relX);
        const inchY = pxToInch(relY);
        const inchW = pxToInch(elem.rect.width);
        const inchH = pxToInch(elem.rect.height);

        if (inchW < 0.01 || inchH < 0.01) continue;

        if (elem.hasTransform) transformElements++;

        const isCoreText = CORE_TEXT_TAGS.has(elem.tagName);
        const bgColor = elem.style.backgroundColor;
        const bgImage = elem.style.backgroundImage;
        const hasSolidBg = !isTransparent(bgColor) && !hasGradient(bgImage);
        const hasGradientBg = hasGradient(bgImage);
        const hasFilter = elem.style.filter && elem.style.filter !== 'none';

        const borderLine = buildBorderLine(elem);
        if (elem.borderHasAny) borderedElements++;
        if (borderLine) borderMapped++;
        else if (elem.borderHasAny && !elem.borderUniform) borderSkippedAsymmetric++;

        const rectRadius = computeRectRadius(elem);
        const useRoundRect = rectRadius > 0;

        const fontSize = parseFloat(elem.style.fontSize);
        const fontPt = pxToPt(fontSize);
        const fontFace = parseFontFamily(elem.style.fontFamily, fontMap);
        const color = rgbToHex(elem.style.color);
        const bold = parseInt(elem.style.fontWeight, 10) >= 700 || elem.style.fontWeight === 'bold';
        const italic = elem.style.fontStyle === 'italic' || elem.style.fontStyle === 'oblique';
        const align = elem.style.textAlign === 'center' ? 'center'
          : elem.style.textAlign === 'right' ? 'right'
          : 'left';
        const pos = { x: inchX, y: inchY, w: inchW, h: inchH };

        // transform non-text → element screenshot
        if (elem.hasTransform && !elem.hasDirectText && !elem.hasInlineChildren && elem.pptxIdx) {
          try {
            const elHandle = slideHandle.locator(`[data-pptx-idx="${elem.pptxIdx}"]`);
            const buf = await screenshotByLocator(elHandle);
            addScreenshotToSlide(pptxSlide, buf, pos);
            transformScreenshotFallbacks++;
            fallbackCount++;
          } catch (e) {
            log(`    ⚠ transform element screenshot failed: ${e.message}`);
            fallbackCount++;
          }
          continue;
        }

        if (elem.isImg) {
          try {
            const buf = (elem.hasTransform && elem.pptxIdx)
              ? await screenshotByLocator(slideHandle.locator(`[data-pptx-idx="${elem.pptxIdx}"]`))
              : await screenshotByClip(page, elem.rect);
            addScreenshotToSlide(pptxSlide, buf, pos);
            semanticCount++;
          } catch (e) {
            log(`    ⚠ img screenshot failed: ${e.message}`);
            fallbackCount++;
          }
          continue;
        }

        if (elem.isCanvas || elem.isSvg) {
          try {
            const buf = await screenshotByClip(page, elem.rect);
            addScreenshotToSlide(pptxSlide, buf, pos);
            fallbackCount++;
          } catch (e) {
            log(`    ⚠ canvas/svg fallback failed: ${e.message}`);
            fallbackCount++;
          }
          continue;
        }

        // text elements with inline runs
        if ((elem.hasDirectText || elem.hasInlineChildren) && elem.inlineRuns && elem.inlineRuns.length > 0) {
          const tc = buildTextContent(elem.inlineRuns, fontMap);
          if (!tc) continue;

          richTextElements++;
          totalInlineRuns += elem.inlineRuns.length;

          const baseOpts = {
            x: inchX, y: inchY, w: inchW, h: inchH,
            align, valign: 'top', wrap: true,
          };

          if (elem.listType === 'ul') {
            baseOpts.bullet = true;
          } else if (elem.listType === 'ol') {
            baseOpts.bullet = { type: 'number', numberType: 'arabicPeriod' };
          }

          if (borderLine) baseOpts.line = borderLine;

          if (hasGradientBg) {
            try {
              const buf = await screenshotByClip(page, elem.rect);
              addScreenshotToSlide(pptxSlide, buf, pos);
              fallbackCount++;
            } catch (e) {
              log(`    ⚠ gradient bg screenshot failed: ${e.message}`);
            }
            if (tc.isSingle) {
              pptxSlide.addText(tc.text, { ...baseOpts, ...tc.options });
            } else {
              pptxSlide.addText(tc.runs, baseOpts);
            }
            semanticCount++;
          } else if (hasSolidBg && !elem.hasPositionedChildren) {
            baseOpts.fill = { color: rgbToHex(bgColor), type: 'solid' };
            if (tc.isSingle) {
              pptxSlide.addText(tc.text, { ...baseOpts, ...tc.options });
            } else {
              pptxSlide.addText(tc.runs, baseOpts);
            }
            semanticCount++;
          } else {
            if (tc.isSingle) {
              pptxSlide.addText(tc.text, { ...baseOpts, ...tc.options });
            } else {
              pptxSlide.addText(tc.runs, baseOpts);
            }
            semanticCount++;
          }

          continue;
        }

        // non-text elements with solid bg
        if (!elem.hasDirectText && !elem.hasInlineChildren && hasSolidBg && !elem.hasPositionedChildren) {
          const shapeOpts = {
            x: inchX, y: inchY, w: inchW, h: inchH,
            fill: { color: rgbToHex(bgColor), type: 'solid' },
          };
          if (borderLine) shapeOpts.line = borderLine;
          if (useRoundRect) {
            shapeOpts.rectRadius = rectRadius;
            pptxSlide.addShape(pptx.ShapeType.roundRect, shapeOpts);
          } else {
            pptxSlide.addShape(pptx.ShapeType.rect, shapeOpts);
          }
          semanticCount++;
          continue;
        }

        // fallback: gradient/filter non-text elements
        if ((hasGradientBg || hasFilter) && !elem.hasDirectText && !elem.hasInlineChildren) {
          try {
            const buf = await screenshotByClip(page, elem.rect);
            addScreenshotToSlide(pptxSlide, buf, pos);
            fallbackCount++;
          } catch (e) {
            log(`    ⚠ element fallback failed: ${e.message}`);
          }
        }
      }

      // per-slide cleanup of data-pptx-idx
      await slideHandle.evaluate(el =>
        el.querySelectorAll('[data-pptx-idx]').forEach(e => e.removeAttribute('data-pptx-idx'))
      );

      } catch (slideErr) {
        log(`    ⚠ slide ${si + 1} 翻譯失敗 (${slideErr.message}) — 退回全頁截圖`);
        try {
          const screenshotBuf = await screenshotByLocator(slideHandle);
          addScreenshotToSlide(pptxSlide, screenshotBuf, { x: 0, y: 0, w: '100%', h: '100%' });
          semanticCount = 0;
          fallbackCount = 1;
          coreTextSemantic = false;
        } catch (e2) {
          log(`    ⚠ slide-level fallback 也失敗: ${e2.message}`);
        }
      }

      const totalElements = semanticCount + fallbackCount;
      const semanticRatio = totalElements > 0
        ? Math.round((semanticCount / totalElements) * 1000) / 1000
        : null;

      allSlideStats.push({
        slide: si + 1,
        semantic_elements: semanticCount,
        fallback_elements: fallbackCount,
        semantic_ratio: semanticRatio,
        core_text_semantic: coreTextSemantic,
        stacking_contexts_count: stackingContextsCount,
        max_nesting_depth: maxNestingDepth,
        transform_elements: transformElements,
        transform_screenshot_fallbacks: transformScreenshotFallbacks,
        rich_text_elements: richTextElements,
        total_inline_runs: totalInlineRuns,
        bordered_elements: borderedElements,
        border_mapped: borderMapped,
        border_skipped_asymmetric: borderSkippedAsymmetric,
        ...(totalElements === 0 ? { empty: true } : {}),
      });

      log(`    ✓ slide ${si + 1}: ${semanticCount} semantic + ${fallbackCount} fallback (ratio: ${semanticRatio !== null ? (semanticRatio * 100).toFixed(1) + '%' : 'N/A (empty)'}${stackingContextsCount > 0 ? `, SC:${stackingContextsCount}` : ''}${richTextElements > 0 ? `, RT:${richTextElements}` : ''}${borderMapped > 0 ? `, B:${borderMapped}` : ''})`);
    }

    log(`→ writing PPTX...`);
    await pptx.writeFile({ fileName: outputPath });

    const fileStats = await stat(outputPath);
    log(`✓ PPTX → ${outputPath} (${(fileStats.size / 1024).toFixed(1)} KB)`);

    const result = {
      path: outputPath,
      mode: 'semantic',
      text_editable: true,
      layout: 'LAYOUT_WIDE',
      layout_size_pt: { width: 960, height: 540 },
      pptxgenjs_version: pptxVersion,
      font_map: fontMap,
      per_slide_stats: allSlideStats,
    };

    const jsonOutput = JSON.stringify(result, null, 2);
    if (!args.quiet) {
      console.log('\n--- build-metadata pptx fragment ---');
      console.log(jsonOutput);
    }

    process.stdout.write(`\n__PPTX_META__${jsonOutput}__END_META__\n`);

  } finally {
    await browser.close();
  }
}

main().catch(e => {
  console.error('FAIL:', e.message);
  process.exit(1);
});

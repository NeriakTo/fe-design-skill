#!/usr/bin/env node
// pdf-export.mjs — Playwright-based deck/page → PDF exporter with viewport-matching default
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.4-short §24.5 P6.4)
//
// Usage:
//   node pdf-export.mjs --input <html> --output <pdf> [--pdf-format viewport|a4-landscape|a4-portrait]
//
// Flags:
//   --input <path>          來源 HTML（必填）
//   --output <path>         輸出 PDF 路徑（必填）
//   --pdf-format <fmt>      viewport (default) | a4-landscape | a4-portrait
//   --viewport WxH          viewport 大小，default 1920x1080（僅 --pdf-format viewport 採用）
//   --print-trigger <expr>  在 PDF 生成前 evaluate 這段 JS（例如 `window.__deck?.togglePrint?.()`）
//   --wait-ms <n>           列印模式 trigger 後等待毫秒，default 500
//   --quiet, -q             安靜模式
//
// Format 對照（fe-design v1.4-short §24.5）：
//   viewport       — 1920×1080，與 deck viewport 一致；wide gantt / table 不會被壓縮（deck mode 預設）
//   a4-landscape   — A4 landscape（fit-to-page，CSS @page 控制）
//   a4-portrait    — A4 portrait（page mode reading 模式）
//
// 設計原則：
//   - viewport-matching 為預設，避免 chromium page.pdf default 96 dpi 縮放至 1440×810
//   - preferCSSPageSize: false（不讓 CSS @page size 蓋過 width/height）
//   - margin: 0（deck/page 自帶 padding）
//   - emulateMedia('print')（觸發 @media print 樣式）

import { mkdir, stat } from 'node:fs/promises';
import { resolve as resolvePath, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

// 動態解析 playwright（caller cwd 優先、其次 npm global）— 避免 ESM 從 ~/.claude/skills/... 無法找到 playwright
async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {}
  const cwdRequire = createRequire(resolvePath(process.cwd(), 'package.json'));
  try {
    return cwdRequire('playwright');
  } catch (e) {
    throw new Error(
      `playwright 找不到。請於 case 工作目錄 (cwd: ${process.cwd()}) 執行 \`npm install playwright\`，或安裝為 npm global package。`
    );
  }
}

const FORMATS = {
  viewport: { kind: 'wh', width: '1920px', height: '1080px' },
  'a4-landscape': { kind: 'a4', format: 'A4', landscape: true },
  'a4-portrait': { kind: 'a4', format: 'A4', landscape: false },
};

function parseArgs(argv) {
  const args = {
    input: null,
    output: null,
    pdfFormat: 'viewport',
    viewport: { width: 1920, height: 1080 },
    printTrigger: null,
    waitMs: 500,
    quiet: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input') args.input = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--pdf-format') args.pdfFormat = argv[++i];
    else if (a === '--viewport') {
      const [w, h] = argv[++i].split('x').map((n) => parseInt(n, 10));
      args.viewport = { width: w, height: h };
    } else if (a === '--print-trigger') args.printTrigger = argv[++i];
    else if (a === '--wait-ms') args.waitMs = parseInt(argv[++i], 10);
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') {
      printUsage();
      process.exit(0);
    }
  }
  if (!args.input || !args.output) {
    console.error('❌ --input 和 --output 為必填');
    printUsage();
    process.exit(2);
  }
  if (!FORMATS[args.pdfFormat]) {
    console.error(`❌ Unknown --pdf-format: ${args.pdfFormat}（允許值：${Object.keys(FORMATS).join(' / ')}）`);
    process.exit(2);
  }
  return args;
}

function printUsage() {
  console.log(`Usage: node pdf-export.mjs --input <html> --output <pdf> [flags]

Flags:
  --pdf-format viewport (default) | a4-landscape | a4-portrait
  --viewport WxH        viewport 大小（default 1920x1080，僅 viewport 採用）
  --print-trigger <js>  PDF 前 evaluate 的 JS 表達式
  --wait-ms <n>         trigger 後等待毫秒（default 500）
  --quiet, -q
`);
}

async function main() {
  const args = parseArgs(process.argv);
  const inputUrl = pathToFileURL(resolvePath(args.input)).href;
  const outputPath = resolvePath(args.output);
  await mkdir(dirname(outputPath), { recursive: true });

  const log = args.quiet ? () => {} : console.log;

  const { chromium } = await loadPlaywright();

  const browser = await chromium.launch({
    headless: true,
    args: ['--allow-file-access-from-files', '--disable-web-security'],
  });
  try {
    const ctx = await browser.newContext({ viewport: args.viewport, deviceScaleFactor: 1 });
    const page = await ctx.newPage();

    if (!args.quiet) {
      page.on('console', (msg) => log(`  [browser ${msg.type()}]`, msg.text()));
      page.on('pageerror', (err) => log(`  [browser ERROR]`, err.message));
    }

    log(`→ loading ${inputUrl}`);
    await page.goto(inputUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.evaluate(() => document.fonts.ready).catch(() => null);
    await page.waitForTimeout(1500);

    await page.emulateMedia({ media: 'print' });

    if (args.printTrigger) {
      log(`  print trigger: ${args.printTrigger}`);
      await page.evaluate(args.printTrigger);
      await page.waitForTimeout(args.waitMs);
    }

    const fmt = FORMATS[args.pdfFormat];
    const pdfOptions = {
      path: outputPath,
      printBackground: true,
      preferCSSPageSize: false,
      margin: { top: '0', bottom: '0', left: '0', right: '0' },
    };
    if (fmt.kind === 'wh') {
      pdfOptions.width = fmt.width;
      pdfOptions.height = fmt.height;
    } else {
      pdfOptions.format = fmt.format;
      pdfOptions.landscape = fmt.landscape;
    }

    await page.pdf(pdfOptions);
    const stats = await stat(outputPath);
    log(`✓ PDF → ${outputPath} (${(stats.size / 1024).toFixed(1)} KB, format: ${args.pdfFormat})`);
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error('FAIL:', e.message);
  process.exit(1);
});

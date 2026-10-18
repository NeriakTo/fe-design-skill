#!/usr/bin/env node
// export-deck-pptx.mjs — PPTX 導出 pipeline wrapper（語義級 + image-based 降級）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.5 P7.1b)
//
// Usage:
//   node export-deck-pptx.mjs --input <html> --output <pptx> [flags]
//
// Flags:
//   --input <path>         來源 HTML（必填，用 deck.html 非 standalone）
//   --output <path>        輸出 PPTX 路徑（必填）
//   --pptx-mode <mode>     semantic (default) | image
//   --font-map <json>      自訂 fontFace 映射表 JSON 檔（傳遞給 html2pptx.mjs）
//   --slide-selector <sel> slide CSS selector（default: section.slide）
//   --metadata <path>      build-metadata.json 路徑（有則更新 pptx 欄位）
//   --quiet, -q            安靜模式

import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { resolve as resolvePath, dirname } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = {
    input: null,
    output: null,
    pptxMode: 'semantic',
    fontMapPath: null,
    slideSelector: 'section.slide',
    metadataPath: null,
    quiet: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input') args.input = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--pptx-mode') args.pptxMode = argv[++i];
    else if (a === '--font-map') args.fontMapPath = argv[++i];
    else if (a === '--slide-selector') args.slideSelector = argv[++i];
    else if (a === '--metadata') args.metadataPath = argv[++i];
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') { printUsage(); process.exit(0); }
  }
  if (!args.input || !args.output) {
    console.error('❌ --input 和 --output 為必填');
    printUsage();
    process.exit(2);
  }
  if (!['semantic', 'image'].includes(args.pptxMode)) {
    console.error(`❌ Unknown --pptx-mode: ${args.pptxMode}（允許值：semantic / image）`);
    process.exit(2);
  }
  return args;
}

function printUsage() {
  console.log(`Usage: node export-deck-pptx.mjs --input <html> --output <pptx> [flags]

Flags:
  --pptx-mode semantic (default) | image
  --font-map <json>       自訂 fontFace 映射表 JSON 檔
  --slide-selector <sel>  slide CSS selector（default: section.slide）
  --metadata <path>       build-metadata.json 路徑
  --quiet, -q
`);
}

async function runSemantic(args, log) {
  const html2pptxPath = resolvePath(__dirname, 'html2pptx.mjs');
  const childArgs = [
    html2pptxPath,
    '--input', args.input,
    '--output', args.output,
    '--slide-selector', args.slideSelector,
  ];
  if (args.fontMapPath) childArgs.push('--font-map', args.fontMapPath);
  if (args.quiet) childArgs.push('--quiet');

  log(`→ semantic mode: invoking html2pptx.mjs...`);

  const { stdout, stderr } = await execFileAsync(process.execPath, childArgs, {
    cwd: process.cwd(),
    timeout: 120000,
    maxBuffer: 10 * 1024 * 1024,
  });

  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);

  const metaMatch = stdout.match(/__PPTX_META__(.+?)__END_META__/s);
  if (!metaMatch) {
    throw new Error('html2pptx.mjs 未輸出 metadata — 翻譯可能失敗');
  }

  return JSON.parse(metaMatch[1]);
}

async function loadModule(name) {
  try { return await import(name); } catch {}
  const { createRequire } = await import('node:module');
  const cwdRequire = createRequire(resolvePath(process.cwd(), 'package.json'));
  return cwdRequire(name);
}

async function runImageBased(args, log) {
  log(`→ image-based mode: Playwright 截圖 → pptxgenjs 貼圖...`);

  const { chromium } = await loadModule('playwright');
  const PptxGenJS = (await loadModule('pptxgenjs')).default || await loadModule('pptxgenjs');

  const { pathToFileURL } = await import('node:url');
  const inputUrl = pathToFileURL(resolvePath(args.input)).href;
  const outputPath = resolvePath(args.output);
  await mkdir(dirname(outputPath), { recursive: true });

  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';

  const browser = await chromium.launch({ headless: true, args: ['--allow-file-access-from-files'] });
  const perSlideStats = [];

  try {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await page.goto(inputUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.evaluate(() => document.fonts.ready).catch(() => null);
    await page.waitForTimeout(1500);

    const hasDeckStage = await page.evaluate(() => !!window.__deck);
    if (hasDeckStage) {
      await page.evaluate(() => window.__deck.togglePrint());
      await page.waitForTimeout(500);
    }

    const slides = page.locator(args.slideSelector);
    const count = await slides.count();
    log(`  found ${count} slides`);

    for (let i = 0; i < count; i++) {
      const slide = slides.nth(i);
      const screenshot = await slide.screenshot({ type: 'png' });
      const pptxSlide = pptx.addSlide();
      pptxSlide.addImage({
        data: `image/png;base64,${screenshot.toString('base64')}`,
        x: 0, y: 0, w: '100%', h: '100%',
      });
      perSlideStats.push({
        slide: i + 1,
        semantic_elements: 0,
        fallback_elements: 1,
        semantic_ratio: 0,
        core_text_semantic: false,
      });
      log(`  [${i + 1}/${count}] screenshot captured`);
    }

    await pptx.writeFile({ fileName: outputPath });
    const fileStats = await stat(outputPath);
    log(`✓ PPTX (image-based) → ${outputPath} (${(fileStats.size / 1024).toFixed(1)} KB)`);
  } finally {
    await browser.close();
  }

  return {
    path: outputPath,
    mode: 'image-based',
    text_editable: false,
    layout: 'LAYOUT_WIDE',
    layout_size_pt: { width: 960, height: 540 },
    pptxgenjs_version: '4.0.1',
    per_slide_stats: perSlideStats,
  };
}

async function updateMetadata(metadataPath, pptxMeta, log) {
  let metadata = {};
  try {
    metadata = JSON.parse(await readFile(metadataPath, 'utf-8'));
  } catch {
    log(`  metadata file not found — creating new`);
  }

  metadata.pptx = pptxMeta;

  await mkdir(dirname(metadataPath), { recursive: true });
  await writeFile(metadataPath, JSON.stringify(metadata, null, 2) + '\n', 'utf-8');
  log(`  ✓ metadata updated: ${metadataPath}`);
}

async function main() {
  const args = parseArgs(process.argv);
  const log = args.quiet ? () => {} : console.log;

  let pptxMeta;

  if (args.pptxMode === 'semantic') {
    try {
      pptxMeta = await runSemantic(args, log);
    } catch (e) {
      log(`\n⚠ semantic mode 失敗 (${e.message}) — 自動降級到 image-based mode`);
      args.pptxMode = 'image';
      pptxMeta = await runImageBased(args, log);
    }
  } else {
    pptxMeta = await runImageBased(args, log);
  }

  if (args.metadataPath) {
    await updateMetadata(args.metadataPath, pptxMeta, log);
  }

  log(`\n✅ PPTX export 完成 (mode: ${pptxMeta.mode})`);
}

main().catch(e => {
  console.error('FAIL:', e.message);
  process.exit(1);
});

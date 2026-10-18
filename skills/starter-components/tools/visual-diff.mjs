#!/usr/bin/env node
// visual-diff.mjs — Playwright + pixelmatch 雙版 deck 視覺差異報告
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.4-short §24.4 P6.3)
//
// Usage:
//   node visual-diff.mjs --base <html> --target <html> --out <dir> [--pages all|1-5,10]
//
// Flags:
//   --base <path>            Base HTML（必填，舊版／對照組）
//   --target <path>          Target HTML（必填，新版／實驗組）
//   --out <dir>              輸出目錄（必填；自動建立 base/ target/ diff/ 子目錄）
//   --pages <spec>           頁碼 spec（all 或 "1-5,10,12-14"，default all）
//   --threshold <0-1>        pixelmatch 像素差異 threshold（default 0.1）
//   --diff-ratio-warn <0-1>  單頁差異比例超過此值即標 warn（default 0.01 = 1%）
//   --base-label <str>       Base 顯示標籤（default "base"）
//   --target-label <str>     Target 顯示標籤（default "target"）
//   --page-count <n>         明示頁數（不指定則 auto-detect；亦可分別指定 --base-page-count / --target-page-count）
//   --nav-strategy <s>       兩側統一的策略（簡寫；亦可改用 --base-nav-strategy / --target-nav-strategy 分別指定）
//                            deck（default，呼叫 window.__deck.goto(i)）
//                            scroll（捲動到 selector locator[i]）
//                            url-hash（goto base#i / target#i）
//   --nav-selector <css>     scroll 策略下使用的 CSS selector（default `.slide`；亦可分別指定 --base-nav-selector / --target-nav-selector）
//   --page-wait-ms <n>       每頁切換後等待毫秒（default 350）
//   --report-template <path> HTML 報告 template（default ./templates/visual-diff-report.html）
//   --title <str>            報告標題（default 自動）
//   --quiet, -q              安靜模式
//   --help, -h
//
// Output:
//   <out>/base/slide-NN.png            Base 每頁截圖（1920×1080）
//   <out>/target/slide-NN.png          Target 每頁截圖
//   <out>/diff/slide-NN.png            pixelmatch overlay（紅色高亮差異）
//   <out>/diff-summary.json            機器可讀差異摘要
//   <out>/visual-diff-report.html      side-by-side HTML 報告（base | target | diff）
//
// 設計原則：
//   - Base / Target 同 viewport（1920×1080）+ 同頁碼配對才能比；不同頁數會 skip 多餘頁
//   - pixelmatch threshold 0.1 是 Y'CbCr Delta E，誤差容忍度中等；可用 --threshold 0.05 更嚴
//   - diff-ratio-warn 0.01（1%）是業界 visual regression 通用閾值
//   - Report 用 SUMMARY_JSON placeholder 注入；HTML 內 JS render rows，避免 server-side template engine
//   - LF/CRLF 透明：固定用 \n 寫檔
//   - SVG/Canvas 等動態元素若有 hover/animation，建議在 base/target 加 print mode 凍結

import { mkdir, writeFile, readFile, stat } from 'node:fs/promises';
import { resolve as resolvePath, dirname, basename, relative as relativePath, isAbsolute, sep as pathSep } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';

const SELF_DIR = dirname(fileURLToPath(import.meta.url));

// 動態解析 npm package（caller cwd 優先 → self dir → npm global）
async function loadModule(pkgName) {
  try {
    return await import(pkgName);
  } catch {}
  for (const baseDir of [process.cwd(), SELF_DIR]) {
    try {
      const req = createRequire(resolvePath(baseDir, 'package.json'));
      return req(pkgName);
    } catch {}
  }
  throw new Error(
    `[visual-diff] 找不到 ${pkgName}。請於 case 工作目錄 (cwd: ${process.cwd()}) 執行 \`npm install ${pkgName}\`。`
  );
}

function parsePagesSpec(spec, total) {
  if (!spec || spec === 'all') return Array.from({ length: total }, (_, i) => i + 1);
  const out = new Set();
  const parts = spec.split(',').map((s) => s.trim());
  if (parts.some((p) => p === '')) {
    throw new Error('[visual-diff] pages spec 不能含空項（多餘逗號）');
  }
  for (const part of parts) {
    const m = part.match(/^(\d+)-(\d+)$/);
    if (m) {
      const a = parseInt(m[1], 10);
      const b = parseInt(m[2], 10);
      const [lo, hi] = a <= b ? [a, b] : [b, a];
      for (let i = lo; i <= hi; i++) out.add(i);
    } else if (/^\d+$/.test(part)) {
      out.add(parseInt(part, 10));
    } else {
      throw new Error(`[visual-diff] 無法解析 pages spec: "${part}"（允許格式：all / 1-5,10 / 1,3,5）`);
    }
  }
  const pages = Array.from(out).sort((a, b) => a - b);
  if (pages.length === 0) {
    throw new Error('[visual-diff] pages spec 解析後為空');
  }
  if (total > 0 && pages.some((n) => n < 1 || n > total)) {
    throw new Error(`[visual-diff] pages spec 含超出範圍 1-${total} 的頁碼`);
  }
  if (pages.some((n) => n < 1)) {
    throw new Error('[visual-diff] pages spec 含 0 或負數');
  }
  return pages;
}

function parseArgs(argv) {
  const args = {
    base: null,
    target: null,
    out: null,
    pages: 'all',
    threshold: 0.1,
    diffRatioWarn: 0.01,
    baseLabel: 'base',
    targetLabel: 'target',
    pageCount: null,
    basePageCount: null,
    targetPageCount: null,
    navStrategy: 'deck',
    navSelector: '.slide',
    baseNavStrategy: null,
    baseNavSelector: null,
    targetNavStrategy: null,
    targetNavSelector: null,
    pageWaitMs: 350,
    reportTemplate: null,
    title: null,
    quiet: false,
  };
  let i = 2;
  const next = (flag) => {
    const v = argv[i + 1];
    if (v == null || (typeof v === 'string' && v.startsWith('--'))) {
      throw new Error(`[visual-diff] missing value for ${flag}`);
    }
    i += 1;
    return v;
  };
  const intFlag = (flag, { allowZero = false } = {}) => {
    const raw = next(flag);
    if (!/^\d+$/.test(raw)) throw new Error(`[visual-diff] ${flag} 須為非負整數，得到 "${raw}"`);
    const n = parseInt(raw, 10);
    if (!allowZero && n === 0) throw new Error(`[visual-diff] ${flag} 不接受 0`);
    return n;
  };
  const floatFlag = (flag, { min, max } = {}) => {
    const raw = next(flag);
    const n = parseFloat(raw);
    if (!Number.isFinite(n)) throw new Error(`[visual-diff] ${flag} 須為數字，得到 "${raw}"`);
    if (min != null && n < min) throw new Error(`[visual-diff] ${flag} 最小 ${min}`);
    if (max != null && n > max) throw new Error(`[visual-diff] ${flag} 最大 ${max}`);
    return n;
  };
  for (; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--base') args.base = next(a);
    else if (a === '--target') args.target = next(a);
    else if (a === '--out') args.out = next(a);
    else if (a === '--pages') args.pages = next(a);
    else if (a === '--threshold') args.threshold = floatFlag(a, { min: 0, max: 1 });
    else if (a === '--diff-ratio-warn') args.diffRatioWarn = floatFlag(a, { min: 0, max: 1 });
    else if (a === '--base-label') args.baseLabel = next(a);
    else if (a === '--target-label') args.targetLabel = next(a);
    else if (a === '--page-count') args.pageCount = intFlag(a);
    else if (a === '--base-page-count') args.basePageCount = intFlag(a);
    else if (a === '--target-page-count') args.targetPageCount = intFlag(a);
    else if (a === '--nav-strategy') args.navStrategy = next(a);
    else if (a === '--nav-selector') args.navSelector = next(a);
    else if (a === '--base-nav-strategy') args.baseNavStrategy = next(a);
    else if (a === '--base-nav-selector') args.baseNavSelector = next(a);
    else if (a === '--target-nav-strategy') args.targetNavStrategy = next(a);
    else if (a === '--target-nav-selector') args.targetNavSelector = next(a);
    else if (a === '--page-wait-ms') args.pageWaitMs = intFlag(a, { allowZero: true });
    else if (a === '--report-template') args.reportTemplate = next(a);
    else if (a === '--title') args.title = next(a);
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') {
      printUsage();
      process.exit(0);
    } else {
      throw new Error(`[visual-diff] unknown flag: ${a}`);
    }
  }
  if (!args.base || !args.target || !args.out) {
    console.error('❌ --base / --target / --out 為必填');
    printUsage();
    process.exit(2);
  }
  if (!['deck', 'scroll', 'url-hash'].includes(args.navStrategy)) {
    console.error(`❌ Unknown --nav-strategy: ${args.navStrategy}（允許值：deck / scroll / url-hash）`);
    process.exit(2);
  }
  if (!Number.isFinite(args.threshold) || args.threshold < 0 || args.threshold > 1) {
    console.error('❌ --threshold 須在 [0, 1]');
    process.exit(2);
  }
  if (!Number.isFinite(args.diffRatioWarn) || args.diffRatioWarn < 0 || args.diffRatioWarn > 1) {
    console.error('❌ --diff-ratio-warn 須在 [0, 1]');
    process.exit(2);
  }
  return args;
}

function printUsage() {
  console.log(`Usage: node visual-diff.mjs --base <html> --target <html> --out <dir> [flags]

Flags:
  --pages all|1-5,10        default all
  --threshold 0-1           default 0.1 (pixelmatch)
  --diff-ratio-warn 0-1     default 0.01 (1%)
  --base-label <str>        default "base"
  --target-label <str>      default "target"
  --page-count <n>          default auto-detect
  --nav-strategy deck|scroll|url-hash   default deck
  --nav-selector <css>      default ".slide" (scroll only)
  --page-wait-ms <n>        default 350
  --report-template <path>  default ./templates/visual-diff-report.html
  --title <str>             default auto
  --quiet, -q
`);
}

async function autoDetectPageCount(page, navStrategy, navSelector, sideCfg) {
  if (sideCfg.pageCount && Number.isFinite(sideCfg.pageCount) && sideCfg.pageCount > 0) return sideCfg.pageCount;
  if (navStrategy === 'deck') {
    const n = await page
      .evaluate(() => {
        if (typeof window === 'undefined') return 0;
        const d = window.__deck;
        if (!d) return 0;
        if (Array.isArray(d.slides)) return d.slides.length;
        if (typeof d.slideCount === 'number') return d.slideCount;
        if (typeof d.length === 'number') return d.length;
        return 0;
      })
      .catch(() => 0);
    return n;
  }
  if (navStrategy === 'scroll') {
    const sel = navSelector;
    return await page.locator(sel).count().catch(() => 0);
  }
  // url-hash 策略無 auto-detect，需明示 --page-count
  return 0;
}

async function shotPages(browser, htmlUrl, outDir, label, pages, args, sideCfg) {
  await mkdir(outDir, { recursive: true });
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });
  const page = await ctx.newPage();

  if (!args.quiet) {
    page.on('pageerror', (err) => console.error(`  [${label} pageerror]`, err.message));
  }

  await page.goto(htmlUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });

  if (sideCfg.navStrategy === 'deck') {
    await page.waitForFunction(() => !!window.__deck, { timeout: 15000 }).catch(() => null);
  }
  await page.evaluate(() => document.fonts.ready).catch(() => null);
  await page.waitForTimeout(1500);

  const pageCount = await autoDetectPageCount(page, sideCfg.navStrategy, sideCfg.navSelector, sideCfg);
  if (pageCount === 0 && pages !== 'all' && !sideCfg.pageCount) {
    throw new Error(
      `[visual-diff:${label}] 無法 auto-detect 頁數（nav-strategy=${sideCfg.navStrategy}）；請以 --base-page-count / --target-page-count 明示`
    );
  }

  const finalPages = pages === 'all' ? null : parsePagesSpec(pages, pageCount || 9999);
  const total = pageCount || (finalPages ? Math.max(...finalPages) : 0);
  const targetIndices = finalPages || Array.from({ length: total }, (_, i) => i + 1);

  const results = [];
  for (const human of targetIndices) {
    const idx = human - 1;
    const num = String(human).padStart(2, '0');
    const outPath = resolvePath(outDir, `slide-${num}.png`);

    try {
      if (sideCfg.navStrategy === 'deck') {
        await page.evaluate((i) => {
          if (window.__deck && typeof window.__deck.goto === 'function') {
            window.__deck.goto(i);
          } else {
            throw new Error('window.__deck.goto 不存在');
          }
        }, idx);
        await page.waitForTimeout(args.pageWaitMs);
        await page.screenshot({ path: outPath, fullPage: false });
      } else if (sideCfg.navStrategy === 'scroll') {
        const all = await page.locator(sideCfg.navSelector).all();
        if (idx >= all.length) {
          results.push({ index: human, path: null, skipped: true, reason: `slide ${human} 超出 ${all.length}` });
          continue;
        }
        await all[idx].scrollIntoViewIfNeeded();
        await page.waitForTimeout(args.pageWaitMs);
        await all[idx].screenshot({ path: outPath });
      } else if (sideCfg.navStrategy === 'url-hash') {
        await page.goto(`${htmlUrl}#${human}`, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(args.pageWaitMs);
        await page.screenshot({ path: outPath, fullPage: false });
      }
      results.push({ index: human, path: outPath, skipped: false });
    } catch (e) {
      results.push({ index: human, path: null, skipped: true, reason: e.message });
    }
  }

  await page.close();
  await ctx.close();
  return { pageCount: total, results };
}

async function pixelDiff(basePath, targetPath, diffPath, args, modules) {
  const { PNG } = modules.pngjs;
  const pixelmatch = modules.pixelmatch;
  const baseBuf = await readFile(basePath);
  const targetBuf = await readFile(targetPath);
  const basePng = PNG.sync.read(baseBuf);
  const targetPng = PNG.sync.read(targetBuf);

  if (basePng.width !== targetPng.width || basePng.height !== targetPng.height) {
    return { skipped: true, reason: `size mismatch ${basePng.width}x${basePng.height} vs ${targetPng.width}x${targetPng.height}` };
  }
  const { width, height } = basePng;
  const diff = new PNG({ width, height });
  const mismatch = pixelmatch(basePng.data, targetPng.data, diff.data, width, height, {
    threshold: args.threshold,
    includeAA: false,
    alpha: 0.3,
    diffColor: [255, 0, 0],
  });
  await writeFile(diffPath, PNG.sync.write(diff));
  const total = width * height;
  return { skipped: false, mismatch, total, ratio: total > 0 ? mismatch / total : 0, width, height };
}

async function loadReportTemplate(args) {
  const fallback = resolvePath(SELF_DIR, 'templates', 'visual-diff-report.html');
  const path = args.reportTemplate ? resolvePath(args.reportTemplate) : fallback;
  if (!existsSync(path)) {
    throw new Error(`[visual-diff] report template 不存在：${path}`);
  }
  return await readFile(path, 'utf-8');
}

function safeJsonForScript(obj) {
  // 防止 </script> XSS（即使 attacker 能控 fixed string）
  return JSON.stringify(obj).replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026');
}

function relPath(from, to) {
  const f = resolvePath(from);
  const t = resolvePath(to);
  const rel = relativePath(f, t);
  if (!rel || rel.startsWith('..') || isAbsolute(rel)) {
    throw new Error(`[visual-diff] asset path escaped output dir: ${t}`);
  }
  // 統一用 POSIX 分隔（HTML <img src> 用 /）
  return rel.split(pathSep).join('/');
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv);
  } catch (e) {
    console.error('❌', e.message);
    printUsage();
    process.exit(2);
  }
  const baseAbs = resolvePath(args.base);
  const targetAbs = resolvePath(args.target);
  const outAbs = resolvePath(args.out);
  if (!existsSync(baseAbs)) {
    console.error(`❌ --base 檔案不存在：${baseAbs}`);
    process.exit(2);
  }
  if (!existsSync(targetAbs)) {
    console.error(`❌ --target 檔案不存在：${targetAbs}`);
    process.exit(2);
  }
  await mkdir(outAbs, { recursive: true });

  const log = args.quiet ? () => {} : console.log;

  log('→ loading playwright + pixelmatch + pngjs (dynamic)');
  const [playwrightMod, pixelmatchMod, pngjsMod] = await Promise.all([
    loadModule('playwright'),
    loadModule('pixelmatch'),
    loadModule('pngjs'),
  ]);
  // ESM/CJS 互通：pixelmatch 是 default export
  const pixelmatch = pixelmatchMod.default || pixelmatchMod;
  const pngjs = pngjsMod.PNG ? pngjsMod : pngjsMod.default || pngjsMod;
  const modules = { pixelmatch, pngjs };

  const { chromium } = playwrightMod;
  const browser = await chromium.launch({
    headless: true,
    args: ['--allow-file-access-from-files'],
  });

  let baseShots, targetShots;
  try {
    const baseUrl = pathToFileURL(baseAbs).href;
    const targetUrl = pathToFileURL(targetAbs).href;
    const baseDir = resolvePath(outAbs, 'base');
    const targetDir = resolvePath(outAbs, 'target');
    const diffDir = resolvePath(outAbs, 'diff');
    await mkdir(diffDir, { recursive: true });

    const baseCfg = {
      navStrategy: args.baseNavStrategy ?? args.navStrategy,
      navSelector: args.baseNavSelector ?? args.navSelector,
      pageCount: args.basePageCount ?? args.pageCount,
    };
    const targetCfg = {
      navStrategy: args.targetNavStrategy ?? args.navStrategy,
      navSelector: args.targetNavSelector ?? args.navSelector,
      pageCount: args.targetPageCount ?? args.pageCount,
    };
    for (const [side, cfg] of [['base', baseCfg], ['target', targetCfg]]) {
      if (!['deck', 'scroll', 'url-hash'].includes(cfg.navStrategy)) {
        throw new Error(`[visual-diff] ${side} nav-strategy 不合法: ${cfg.navStrategy}`);
      }
    }

    log(`→ shoot base (${args.baseLabel}, ${baseCfg.navStrategy}): ${args.base}`);
    baseShots = await shotPages(browser, baseUrl, baseDir, args.baseLabel, args.pages, args, baseCfg);
    log(`  base: ${baseShots.results.filter((r) => !r.skipped).length} / ${baseShots.results.length} pages`);

    log(`→ shoot target (${args.targetLabel}, ${targetCfg.navStrategy}): ${args.target}`);
    targetShots = await shotPages(browser, targetUrl, targetDir, args.targetLabel, args.pages, args, targetCfg);
    log(`  target: ${targetShots.results.filter((r) => !r.skipped).length} / ${targetShots.results.length} pages`);
  } finally {
    await browser.close();
  }

  // 配對 + diff
  const baseByIdx = new Map(baseShots.results.map((r) => [r.index, r]));
  const targetByIdx = new Map(targetShots.results.map((r) => [r.index, r]));
  const allIdx = Array.from(new Set([...baseByIdx.keys(), ...targetByIdx.keys()])).sort((a, b) => a - b);

  const pages = [];
  for (const idx of allIdx) {
    const num = String(idx).padStart(2, '0');
    const b = baseByIdx.get(idx);
    const t = targetByIdx.get(idx);
    const diffPath = resolvePath(outAbs, 'diff', `slide-${num}.png`);

    if (!b || b.skipped || !t || t.skipped) {
      pages.push({
        index: idx,
        base_path: b && !b.skipped ? relPath(outAbs, b.path) : null,
        target_path: t && !t.skipped ? relPath(outAbs, t.path) : null,
        diff_path: null,
        mismatch_px: null,
        total_px: null,
        mismatch_ratio: null,
        warn: false,
        skipped: true,
        skipped_reason:
          (!b || b.skipped) && (!t || t.skipped)
            ? 'both base and target shots failed'
            : !b || b.skipped
            ? `base shot failed: ${b ? b.reason : 'missing'}`
            : `target shot failed: ${t ? t.reason : 'missing'}`,
      });
      continue;
    }

    const diff = await pixelDiff(b.path, t.path, diffPath, args, modules);
    if (diff.skipped) {
      pages.push({
        index: idx,
        base_path: relPath(outAbs, b.path),
        target_path: relPath(outAbs, t.path),
        diff_path: null,
        mismatch_px: null,
        total_px: null,
        mismatch_ratio: null,
        warn: false,
        skipped: true,
        skipped_reason: diff.reason,
      });
    } else {
      pages.push({
        index: idx,
        base_path: relPath(outAbs, b.path),
        target_path: relPath(outAbs, t.path),
        diff_path: relPath(outAbs, diffPath),
        mismatch_px: diff.mismatch,
        total_px: diff.total,
        mismatch_ratio: diff.ratio,
        warn: diff.ratio > args.diffRatioWarn,
        skipped: false,
        skipped_reason: null,
      });
    }
  }

  const summary = {
    pages_total: pages.length,
    pages_warned: pages.filter((p) => p.warn).length,
    pages_skipped: pages.filter((p) => p.skipped).length,
    max_mismatch_ratio: pages.reduce((m, p) => (p.mismatch_ratio != null && p.mismatch_ratio > m ? p.mismatch_ratio : m), 0),
  };

  const result = {
    version: '1',
    generated_at: new Date().toISOString(),
    base: { html_path: baseAbs, label: args.baseLabel, page_count: baseShots.pageCount || null },
    target: { html_path: targetAbs, label: args.targetLabel, page_count: targetShots.pageCount || null },
    viewport: { width: 1920, height: 1080 },
    threshold: args.threshold,
    diff_ratio_warn: args.diffRatioWarn,
    pages,
    summary,
  };

  const summaryPath = resolvePath(outAbs, 'diff-summary.json');
  await writeFile(summaryPath, JSON.stringify(result, null, 2) + '\n', 'utf-8');
  log(`✓ diff-summary.json → ${summaryPath}`);

  // Render HTML report
  const tpl = await loadReportTemplate(args);
  const reportTitle =
    args.title ||
    `Visual Diff — ${args.baseLabel} vs ${args.targetLabel} (${basename(baseAbs)} ↔ ${basename(targetAbs)})`;
  const html = tpl
    .replace(/\{\{TITLE\}\}/g, reportTitle.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'))
    .replace(/\{\{SUMMARY_JSON\}\}/g, safeJsonForScript(result));
  const reportPath = resolvePath(outAbs, 'visual-diff-report.html');
  await writeFile(reportPath, html, 'utf-8');
  log(`✓ visual-diff-report.html → ${reportPath}`);

  log(
    `\n📊 Summary: ${summary.pages_total} pages, ${summary.pages_warned} warned (>${(args.diffRatioWarn * 100).toFixed(2)}% diff), ${summary.pages_skipped} skipped, max ${(summary.max_mismatch_ratio * 100).toFixed(3)}%`
  );

  // Exit code 規格：
  //   0 — 全部 OK 無 warn 無 skip（全頁完整 + 全頁差異 ≤ warn 閾值）
  //   2 — 有 warn 頁（差異 ratio 超過 --diff-ratio-warn）或有 skipped 頁（截圖失敗 / size mismatch / 頁數不匹配）
  //   1 — 流程錯誤（在 main catch）
  // skip 也回 2 是為了避免 CI/automation false-green：頁數不匹配或 shot 失敗 = 報告不完整
  process.exit(summary.pages_warned > 0 || summary.pages_skipped > 0 ? 2 : 0);
}

main().catch((e) => {
  console.error('FAIL:', e.stack || e.message);
  process.exit(1);
});

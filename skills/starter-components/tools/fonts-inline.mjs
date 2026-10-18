#!/usr/bin/env node
// fonts-inline.mjs — 解析 Google Fonts <link>、下載 woff2、inline 為 data: URI
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.3.1 §18 P5.2)
//
// Usage:
//   node fonts-inline.mjs --input <html> --output <html> [--strategy minimal|all] [--quiet]
//
// 行為：
//   1. 找 <link href="https://fonts.googleapis.com/css2?..."> stylesheet
//   2. fetch CSS（需 modern UA，否則回 legacy css 無 woff2）
//   3. parse 每個 @font-face block 的 unicode-range + src url
//   4. strategy=minimal：只 inline body 文字實際使用到的 unicode-range 對應 @font-face
//      strategy=all：inline 所有 @font-face（含 768 個中文 subset，產出可達 45 MB）
//   5. 移除原 <link>（含 fonts.googleapis.com / fonts.gstatic.com 的 preconnect）
//   6. 在 </head> 前注入 <style data-google-fonts-inlined="true">
//
// 注意：
//   - 中文 deck 文字 ≈ 200-500 字元 → minimal 大幅縮 size 至 1-3 MB（含中文）
//   - all 模式檔案可達 45 MB；minimal 是預設
//   - 非 Google Fonts 的 @font-face（self-hosted）由 standalone-export.mjs 的 inlineCssUrls 處理

import { readFile, writeFile } from 'node:fs/promises';
import { realpathSync } from 'node:fs';
import { dirname, resolve as resolvePath } from 'node:path';
import { fileURLToPath } from 'node:url';

const UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36';

async function fetchText(url) {
  const r = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  return await r.text();
}

async function fetchBinaryAsBase64(url) {
  const r = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  const buf = Buffer.from(await r.arrayBuffer());
  return buf.toString('base64');
}

// 從 HTML body 抽出實際使用的 unicode codepoint set
// 注意：包含 attribute / inline style / 但排除 <script><style><link><meta> tag content
function extractBodyCodepoints(html) {
  // 移除 <script>...</script>、<style>...</style>、<head>...</head> 的內容
  let stripped = html
    .replace(/<head\b[^>]*>[\s\S]*?<\/head>/gi, ' ')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ');
  // 移除 HTML tag（保留 attribute 文字以涵蓋 alt / aria-label / data-* 等）
  // 簡化處理：直接取所有 codepoint
  const codepoints = new Set();
  for (const ch of stripped) {
    const cp = ch.codePointAt(0);
    if (cp && cp > 0x20) codepoints.add(cp); // 排除控制字元
  }
  return codepoints;
}

// 解析 unicode-range 字串：U+0000-00FF, U+4E00-9FFF, U+FB00, ...
function parseUnicodeRange(rangeStr) {
  const ranges = [];
  for (const part of rangeStr.split(',').map((s) => s.trim())) {
    // 支援格式：U+xxxx / U+xxxx-yyyy / U+xx?? (?? = wildcard)
    const m = part.match(/^U\+([0-9A-F?]+)(?:-([0-9A-F]+))?$/i);
    if (!m) continue;
    let start, end;
    if (m[1].includes('?')) {
      // wildcard：U+0??? → U+0000 ~ U+0FFF
      start = parseInt(m[1].replace(/\?/g, '0'), 16);
      end = parseInt(m[1].replace(/\?/g, 'F'), 16);
    } else {
      start = parseInt(m[1], 16);
      end = m[2] ? parseInt(m[2], 16) : start;
    }
    ranges.push([start, end]);
  }
  return ranges;
}

// 檢查 codepoint set 是否與 unicode-ranges 有交集
function rangesIntersectCodepoints(ranges, codepoints) {
  for (const cp of codepoints) {
    for (const [s, e] of ranges) {
      if (cp >= s && cp <= e) return true;
    }
  }
  return false;
}

// 解析 CSS 內的 @font-face blocks
// 回傳 [{ block: 完整字串, unicodeRange: 'U+...' or null, urls: [{ full, fontUrl }] }]
function parseFontFaceBlocks(cssText) {
  const blocks = [];
  const blockRe = /@font-face\s*\{([^}]*)\}/g;
  let m;
  while ((m = blockRe.exec(cssText)) !== null) {
    const inner = m[1];
    const block = m[0];
    const urMatch = inner.match(/unicode-range\s*:\s*([^;]+);/i);
    const unicodeRange = urMatch ? urMatch[1].trim() : null;
    const urls = [];
    const urlRe = /url\((https:\/\/fonts\.gstatic\.com\/[^)]+\.woff2)\)/g;
    let um;
    while ((um = urlRe.exec(inner)) !== null) {
      urls.push({ full: um[0], fontUrl: um[1] });
    }
    blocks.push({ block, unicodeRange, urls, idx: m.index, len: block.length });
  }
  return blocks;
}

async function inlineGoogleFonts(html, { strategy = 'minimal', log = () => {} } = {}) {
  // 1. 找出所有 Google Fonts stylesheet <link>
  const linkRe = /<link[^>]+href=["'](https:\/\/fonts\.googleapis\.com\/css2[^"']+)["'][^>]*>/gi;
  const linkMatches = [...html.matchAll(linkRe)];
  log(`Found ${linkMatches.length} Google Fonts <link> tag(s)`);

  if (linkMatches.length === 0) {
    return { html, stats: { kept: 0, dropped: 0, fontUrls: 0, downloadedBytes: 0 } };
  }

  // 2. 抽 body codepoints（minimal mode 才需要）
  const codepoints = strategy === 'minimal' ? extractBodyCodepoints(html) : null;
  if (strategy === 'minimal') {
    log(`  body codepoints: ${codepoints.size}`);
  }

  let totalKept = 0;
  let totalDropped = 0;
  let totalFontUrls = 0;
  let totalBytes = 0;
  const inlinedStyles = [];

  // 3. fetch each CSS
  for (const m of linkMatches) {
    const cssUrl = m[1].replace(/&amp;/g, '&');
    log(`  Fetching CSS: ${cssUrl}`);
    let cssText;
    try {
      cssText = await fetchText(cssUrl);
    } catch (err) {
      log(`  ⚠ CSS fetch failed: ${err.message} — 保留原 <link>`);
      continue;
    }

    // 4. parse @font-face blocks
    const blocks = parseFontFaceBlocks(cssText);
    log(`  → ${blocks.length} @font-face blocks`);

    // 5. 決定每個 block 是否保留
    let modifiedCss = cssText;
    // 由後往前處理避免 idx 偏移
    for (let i = blocks.length - 1; i >= 0; i--) {
      const b = blocks[i];
      let keep = true;
      if (strategy === 'minimal' && b.unicodeRange) {
        const ranges = parseUnicodeRange(b.unicodeRange);
        keep = rangesIntersectCodepoints(ranges, codepoints);
      }
      // 沒 unicode-range 的 @font-face 一律保留（latin / 主字型）
      if (!keep) {
        modifiedCss = modifiedCss.slice(0, b.idx) + modifiedCss.slice(b.idx + b.len);
        totalDropped++;
      }
    }

    // 6. 對保留下來的 block，下載 woff2 + inline 為 data URI
    const remainingBlocks = parseFontFaceBlocks(modifiedCss);
    for (const b of remainingBlocks) {
      for (const u of b.urls) {
        try {
          const b64 = await fetchBinaryAsBase64(u.fontUrl);
          const dataUri = `data:font/woff2;base64,${b64}`;
          modifiedCss = modifiedCss.split(u.fontUrl).join(dataUri);
          totalFontUrls++;
          totalBytes += (b64.length * 3) / 4; // base64 → byte 估算
        } catch (err) {
          log(`    ⚠ font download failed ${u.fontUrl.slice(-60)}: ${err.message}`);
        }
      }
    }
    totalKept += remainingBlocks.length;

    inlinedStyles.push(modifiedCss);
  }

  // 7. 移除原 <link>（含 preconnect）
  let newHtml = html.replace(linkRe, '');
  newHtml = newHtml.replace(
    /<link[^>]+href=["']https:\/\/fonts\.(googleapis|gstatic)\.com["'][^>]*>/gi,
    '',
  );

  // 8. 注入 <style> 在 </head> 之前
  if (inlinedStyles.length > 0) {
    const styleBlock = `\n<style data-google-fonts-inlined="${strategy}">\n${inlinedStyles.join('\n\n')}\n</style>\n`;
    if (newHtml.includes('</head>')) {
      newHtml = newHtml.replace('</head>', `${styleBlock}</head>`);
    } else {
      // 沒 </head> 就放在 <html> 後或檔案開頭
      newHtml = styleBlock + newHtml;
    }
  }

  return {
    html: newHtml,
    stats: {
      kept: totalKept,
      dropped: totalDropped,
      fontUrls: totalFontUrls,
      downloadedBytes: Math.round(totalBytes),
    },
  };
}

function parseArgs(argv) {
  const args = { strategy: 'minimal', quiet: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input' || a === '-i') args.input = argv[++i];
    else if (a === '--output' || a === '-o') args.output = argv[++i];
    else if (a === '--strategy' || a === '-s') args.strategy = argv[++i];
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') args.help = true;
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.input || !args.output) {
    process.stdout.write([
      'fonts-inline.mjs — inline Google Fonts woff2 as data: URI for zero external dependencies',
      '',
      'Usage:',
      '  node fonts-inline.mjs --input <html> --output <html> [--strategy minimal|all]',
      '',
      'Options:',
      '  --strategy minimal  (default) only @font-face whose unicode-range covers body codepoints',
      '  --strategy all      include all @font-face blocks (~45MB for full Chinese subset)',
      '  --quiet             suppress progress logs',
      '',
    ].join('\n'));
    process.exit(args.help ? 0 : 1);
  }
  if (!['minimal', 'all'].includes(args.strategy)) {
    process.stderr.write(`❌ invalid --strategy: ${args.strategy} (must be minimal|all)\n`);
    process.exit(1);
  }

  const log = args.quiet ? () => {} : (m) => process.stderr.write(m + '\n');
  const inputAbs = resolvePath(process.cwd(), args.input);
  const outputAbs = resolvePath(process.cwd(), args.output);

  log(`🔤 fonts-inline (strategy: ${args.strategy})`);
  log(`  input:  ${inputAbs}`);
  log(`  output: ${outputAbs}`);

  const html = await readFile(inputAbs, 'utf8');
  const { html: newHtml, stats } = await inlineGoogleFonts(html, {
    strategy: args.strategy,
    log,
  });
  await writeFile(outputAbs, newHtml, 'utf8');

  const origSize = (Buffer.byteLength(html) / 1024).toFixed(1);
  const newSize = (Buffer.byteLength(newHtml) / 1024).toFixed(1);
  log('');
  log(`✅ done — ${origSize} KB → ${newSize} KB`);
  log(`  @font-face kept: ${stats.kept}, dropped: ${stats.dropped}`);
  log(`  woff2 downloaded: ${stats.fontUrls} (~${(stats.downloadedBytes / 1024 / 1024).toFixed(1)} MB)`);
}

const isCli = process.argv[1] && realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
if (isCli) {
  main().catch((e) => {
    process.stderr.write(`❌ failed: ${e.message}\n${e.stack}\n`);
    process.exit(1);
  });
}

export { inlineGoogleFonts, extractBodyCodepoints, parseUnicodeRange, parseFontFaceBlocks };

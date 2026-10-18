#!/usr/bin/env node
// standalone-export.mjs — inline 所有外部 CSS / JS / 字型 / 圖片，輸出單一 standalone HTML
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.3.1 §10 P1.11 + §18 P5.2)
//
// Usage:
//   node standalone-export.mjs --input <input.html> --output <output.html> [flags]
//
// Flags:
//   --inline-fonts             啟用 Google Fonts woff2 inline（預設 off）
//   --font-strategy minimal    (default when --inline-fonts) 只 inline body 用到的 unicode-range
//   --font-strategy all        inline 所有 woff2（中文 deck 可達 45 MB）
//   --quiet, -q                安靜模式
//
// 行為：
//   1. 讀 input HTML
//   2. 把所有相對路徑的 <link rel="stylesheet">、<script src> inline 進 <style> / <script>
//   3. CSS 內 url(...) 字型 / 圖片 inline 為 base64 data URI
//   4. <img src> 相對路徑 inline 為 data URI
//   5. **預設跳過 absolute URL**（http://、https://、//、data:）
//   6. **若 --inline-fonts**：呼叫 fonts-inline.mjs 把 Google Fonts CDN woff2 inline
//   7. 寫出 output 檔
//
// 限制：
//   - 不執行 JS、不解析 JSX、不處理 dynamic import()
//   - 對 inline <style> 內的 url() 也會 inline
//   - 重複資源不去重（相同字型若被 import 多次會 inline 多份）

import { readFile, writeFile, stat } from 'node:fs/promises';
import { realpathSync } from 'node:fs';
import { dirname, resolve as resolvePath, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inlineGoogleFonts } from './fonts-inline.mjs';

const MIME = {
  '.css':   'text/css',
  '.js':    'text/javascript',
  '.mjs':   'text/javascript',
  '.json':  'application/json',
  '.woff2': 'font/woff2',
  '.woff':  'font/woff',
  '.ttf':   'font/ttf',
  '.otf':   'font/otf',
  '.eot':   'application/vnd.ms-fontobject',
  '.png':   'image/png',
  '.jpg':   'image/jpeg',
  '.jpeg':  'image/jpeg',
  '.gif':   'image/gif',
  '.svg':   'image/svg+xml',
  '.webp':  'image/webp',
  '.avif':  'image/avif',
  '.ico':   'image/x-icon',
};

function isAbsoluteRef(ref) {
  return /^(?:[a-z]+:|\/\/|data:|#)/i.test(ref);
}

function escapeAttrValue(s) {
  // HTML 屬性值 escape：& 與 " 必修，其餘字元保留以維持可讀性
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

function escapeInlineScript(js) {
  // 防止合法 JS 字串內的 `</script>` 提早關閉 inline script tag
  // 對任何 `</script` 變體（含 `</SCRIPT` `</script `）做安全 escape
  return String(js).replace(/<\/(script)/gi, '<\\/$1');
}

function escapeInlineStyleClose(css) {
  // 對應 inline <style> 內若含 `</style>` 字串（罕見，但 CSS content: 可能撞到）
  return String(css).replace(/<\/(style)/gi, '<\\/$1');
}

function mimeFor(p) {
  return MIME[extname(p).toLowerCase()] || 'application/octet-stream';
}

async function readMaybe(path, log) {
  try {
    await stat(path);
    return await readFile(path);
  } catch {
    log(`  ⚠️  跳過（找不到檔案）: ${path}`);
    return null;
  }
}

async function inlineCssUrls(cssText, baseDir, log) {
  // 處理 CSS 內 url(...) — 字型、圖片、background-image
  const urlRe = /url\(\s*(['"]?)([^)'"]+)\1\s*\)/g;
  const tasks = [];
  const matches = [];
  let m;
  while ((m = urlRe.exec(cssText)) !== null) {
    matches.push({ full: m[0], quote: m[1], ref: m[2], idx: m.index });
  }
  for (const it of matches) {
    if (isAbsoluteRef(it.ref)) continue;
    const refClean = it.ref.split('?')[0].split('#')[0];
    const abs = resolvePath(baseDir, refClean);
    tasks.push(readMaybe(abs, log).then((buf) => {
      if (!buf) return;
      const dataUri = `data:${mimeFor(refClean)};base64,${buf.toString('base64')}`;
      it.replacement = `url(${dataUri})`;
      log(`    ↳ inline url(): ${refClean} (${(buf.length / 1024).toFixed(1)} KB)`);
    }));
  }
  await Promise.all(tasks);
  // 由後往前 splice 避免索引偏移
  let result = cssText;
  for (let i = matches.length - 1; i >= 0; i--) {
    const it = matches[i];
    if (!it.replacement) continue;
    result = result.slice(0, it.idx) + it.replacement + result.slice(it.idx + it.full.length);
  }
  return result;
}

async function inlineCss(cssPath, log) {
  const buf = await readMaybe(cssPath, log);
  if (!buf) return null;
  const text = buf.toString('utf8');
  return await inlineCssUrls(text, dirname(cssPath), log);
}

async function inlineJs(jsPath, log) {
  const buf = await readMaybe(jsPath, log);
  if (!buf) return null;
  return buf.toString('utf8');
}

async function inlineHtml(inputPath, log) {
  const baseDir = dirname(inputPath);
  let html = (await readFile(inputPath)).toString('utf8');

  // 1. 處理 <link rel="stylesheet" href="..."> — 同時相容單雙引號 + 任意屬性順序
  const linkRe = /<link\b[^>]*\brel=["']stylesheet["'][^>]*\bhref=["']([^"']+)["'][^>]*>|<link\b[^>]*\bhref=["']([^"']+)["'][^>]*\brel=["']stylesheet["'][^>]*>/gi;
  const linkReplacements = [];
  let lm;
  while ((lm = linkRe.exec(html)) !== null) {
    const ref = lm[1] || lm[2];
    linkReplacements.push({ full: lm[0], ref, idx: lm.index });
  }
  for (const it of linkReplacements) {
    if (isAbsoluteRef(it.ref)) {
      log(`  ⏭  保留外部 link: ${it.ref}`);
      continue;
    }
    const abs = resolvePath(baseDir, it.ref.split('?')[0].split('#')[0]);
    const css = await inlineCss(abs, log);
    if (css === null) continue;
    // R3 LOW-01：保留原 <link> 的 media 屬性（其他屬性如 disabled / title 不適用 <style>，略）
    const mediaMatch = it.full.match(/\bmedia=(["'])([^"']*)\1/i);
    const mediaAttr = mediaMatch ? ` media="${escapeAttrValue(mediaMatch[2])}"` : '';
    // R3 MED-01 對稱措施：CSS 內可能含 </style>，escape 防 tokenization 提早終止
    const safeCss = escapeInlineStyleClose(css);
    it.replacement = `<style data-inlined-from="${escapeAttrValue(it.ref)}"${mediaAttr}>\n${safeCss}\n</style>`;
    log(`  ✓ inline <link href="${it.ref}">${mediaAttr ? ' (媒體查詢已保留)' : ''}`);
  }
  for (let i = linkReplacements.length - 1; i >= 0; i--) {
    const it = linkReplacements[i];
    if (!it.replacement) continue;
    html = html.slice(0, it.idx) + it.replacement + html.slice(it.idx + it.full.length);
  }

  // 2. 處理 <script src="..."> — 保留 type/module 屬性
  const scriptRe = /<script\b([^>]*?)\bsrc=["']([^"']+)["']([^>]*)><\/script>/gi;
  const scriptReplacements = [];
  let sm;
  while ((sm = scriptRe.exec(html)) !== null) {
    scriptReplacements.push({ full: sm[0], beforeAttrs: sm[1], ref: sm[2], afterAttrs: sm[3], idx: sm.index });
  }
  for (const it of scriptReplacements) {
    if (isAbsoluteRef(it.ref)) {
      log(`  ⏭  保留外部 script: ${it.ref}`);
      continue;
    }
    const abs = resolvePath(baseDir, it.ref.split('?')[0].split('#')[0]);
    const js = await inlineJs(abs, log);
    if (js === null) continue;
    // 保留 type/module/defer/async 等屬性，去掉 src
    const attrs = (it.beforeAttrs + ' ' + it.afterAttrs).replace(/\s+/g, ' ').trim();
    // R3 MED-01：JS 內若含 `</script>` 字串會提早關閉 inline script，必須 escape
    const safeJs = escapeInlineScript(js);
    const safeRef = escapeAttrValue(it.ref);
    it.replacement = `<script ${attrs} data-inlined-from="${safeRef}">\n${safeJs}\n</script>`;
    log(`  ✓ inline <script src="${it.ref}">`);
  }
  for (let i = scriptReplacements.length - 1; i >= 0; i--) {
    const it = scriptReplacements[i];
    if (!it.replacement) continue;
    html = html.slice(0, it.idx) + it.replacement + html.slice(it.idx + it.full.length);
  }

  // 3. 處理 <img src="...">（R3 LOW-02：尚未支援 <source srcset>，待 P1.5+ 補）
  const imgRe = /<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi;
  const imgReplacements = [];
  let im;
  while ((im = imgRe.exec(html)) !== null) {
    imgReplacements.push({ full: im[0], ref: im[1], idx: im.index });
  }
  for (const it of imgReplacements) {
    if (isAbsoluteRef(it.ref)) continue;
    const refClean = it.ref.split('?')[0].split('#')[0];
    const abs = resolvePath(baseDir, refClean);
    const buf = await readMaybe(abs, log);
    if (!buf) continue;
    const dataUri = `data:${mimeFor(refClean)};base64,${buf.toString('base64')}`;
    it.replacement = it.full.replace(it.ref, dataUri);
    log(`  ✓ inline <img src="${it.ref}"> (${(buf.length / 1024).toFixed(1)} KB)`);
  }
  for (let i = imgReplacements.length - 1; i >= 0; i--) {
    const it = imgReplacements[i];
    if (!it.replacement) continue;
    html = html.slice(0, it.idx) + it.replacement + html.slice(it.idx + it.full.length);
  }

  // 4. 處理 inline <style>...</style> 內的 url()
  const inlineStyleRe = /<style\b[^>]*>([\s\S]*?)<\/style>/gi;
  const styleReplacements = [];
  let stm;
  while ((stm = inlineStyleRe.exec(html)) !== null) {
    styleReplacements.push({ full: stm[0], inner: stm[1], idx: stm.index });
  }
  for (const it of styleReplacements) {
    if (it.full.includes('data-inlined-from')) continue; // 已 inline 的 link 跳過避免重複處理
    const replaced = await inlineCssUrls(it.inner, baseDir, log);
    if (replaced === it.inner) continue;
    it.replacement = it.full.replace(it.inner, replaced);
    log(`  ✓ inline <style> 內的 url()`);
  }
  for (let i = styleReplacements.length - 1; i >= 0; i--) {
    const it = styleReplacements[i];
    if (!it.replacement) continue;
    html = html.slice(0, it.idx) + it.replacement + html.slice(it.idx + it.full.length);
  }

  return html;
}

function parseArgs(argv) {
  const args = { quiet: false, inlineFonts: false, fontStrategy: 'minimal' };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input' || a === '-i') args.input = argv[++i];
    else if (a === '--output' || a === '-o') args.output = argv[++i];
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--inline-fonts') args.inlineFonts = true;
    else if (a === '--font-strategy') args.fontStrategy = argv[++i];
    else if (a === '--help' || a === '-h') args.help = true;
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.input || !args.output) {
    process.stdout.write([
      'standalone-export.mjs — inline all external CSS/JS/font/image into a single HTML',
      '',
      'Usage:',
      '  node standalone-export.mjs --input <input.html> --output <output.html> [flags]',
      '',
      'Flags:',
      '  --inline-fonts              also inline Google Fonts woff2 (P5.2; off by default)',
      '  --font-strategy minimal     (default) only @font-face whose unicode-range covers body chars',
      '  --font-strategy all         inline ALL @font-face (~45MB for full Chinese subset)',
      '  --quiet, -q                 silent mode',
      '',
      'Example:',
      '  node ~/.claude/skills/starter-components/tools/standalone-export.mjs \\',
      '    --input deck/index.html --output deck-standalone.html --inline-fonts',
      '',
    ].join('\n'));
    process.exit(args.help ? 0 : 1);
  }
  if (!['minimal', 'all'].includes(args.fontStrategy)) {
    process.stderr.write(`❌ invalid --font-strategy: ${args.fontStrategy} (must be minimal|all)\n`);
    process.exit(1);
  }

  const log = args.quiet ? () => {} : (m) => process.stderr.write(m + '\n');
  const inputAbs = resolvePath(process.cwd(), args.input);
  const outputAbs = resolvePath(process.cwd(), args.output);

  log(`📦 standalone-export${args.inlineFonts ? ` (--inline-fonts ${args.fontStrategy})` : ''}`);
  log(`  input:  ${inputAbs}`);
  log(`  output: ${outputAbs}`);
  log('');

  let html = await inlineHtml(inputAbs, log);

  if (args.inlineFonts) {
    log('');
    log(`🔤 fonts-inline (strategy: ${args.fontStrategy})`);
    const result = await inlineGoogleFonts(html, { strategy: args.fontStrategy, log });
    html = result.html;
    log(`  @font-face kept: ${result.stats.kept}, dropped: ${result.stats.dropped}`);
    log(`  woff2 downloaded: ${result.stats.fontUrls} (~${(result.stats.downloadedBytes / 1024 / 1024).toFixed(1)} MB)`);
  }

  await writeFile(outputAbs, html, 'utf8');

  const sizeKb = (Buffer.byteLength(html, 'utf8') / 1024).toFixed(1);
  log('');
  log(`✅ 完成 — ${sizeKb} KB`);
}

const isCli = process.argv[1] && realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
if (isCli) {
  main().catch((e) => {
    process.stderr.write(`❌ 失敗: ${e.message}\n${e.stack}\n`);
    process.exit(1);
  });
}

export { inlineHtml, inlineCssUrls };

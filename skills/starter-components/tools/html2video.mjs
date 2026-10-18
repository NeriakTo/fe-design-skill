#!/usr/bin/env node
// html2video.mjs — HTML deck → MP4 影片轉換（HyperFrames wrapper + FFmpeg 退化）
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.7 P9.2)
//
// Usage:
//   node html2video.mjs --input <html> --output <mp4> [flags]
//
// Flags:
//   --input <path>         來源 HTML deck（必填）
//   --output <path>        MP4 輸出路徑（必填）
//   --duration <sec>       影片總長（預設：slide 數 × 5 秒）
//   --fps <n>              幀率（預設 30）
//   --width <px>           解析度寬（預設 1920）
//   --height <px>          解析度高（預設 1080）
//   --slide-selector <sel> slide CSS selector（預設 section.slide）
//   --transition <sec>     slide 間轉場秒數（預設 0.5）
//   --quiet, -q            安靜模式

import { readFile, writeFile, mkdir, rm, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const execFileAsync = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = {
    input: null,
    output: null,
    duration: null,
    fps: 30,
    width: 1920,
    height: 1080,
    slideSelector: 'section.slide',
    transition: 0.5,
    quiet: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--input') args.input = argv[++i];
    else if (a === '--output') args.output = argv[++i];
    else if (a === '--duration') args.duration = Number(argv[++i]);
    else if (a === '--fps') args.fps = Number(argv[++i]);
    else if (a === '--width') args.width = Number(argv[++i]);
    else if (a === '--height') args.height = Number(argv[++i]);
    else if (a === '--slide-selector') args.slideSelector = argv[++i];
    else if (a === '--transition') args.transition = Number(argv[++i]);
    else if (a === '-q' || a === '--quiet') args.quiet = true;
    else { console.error(`Unknown flag: ${a}`); process.exit(2); }
  }
  if (!args.input || !args.output) {
    console.error('Usage: node html2video.mjs --input <html> --output <mp4>');
    process.exit(2);
  }
  return args;
}

function log(args, ...msg) {
  if (!args.quiet) console.log(...msg);
}

function escapeSelector(sel) {
  return sel.replace(/'/g, "\\'").replace(/\\/g, '\\\\');
}

function detectSlides(html, selector) {
  const selectorTag = selector.split(/[.[\s]/)[0] || 'section';
  const classParts = selector.match(/\.([\w-]+)/g);
  if (!classParts || classParts.length === 0) {
    const tagPattern = new RegExp(`<${selectorTag}[\\s>]`, 'gi');
    const matches = html.match(tagPattern);
    return matches ? matches.length : 0;
  }
  const primaryClass = classParts[0].slice(1);
  const classPattern = new RegExp(
    `<${selectorTag}[^>]*class="[^"]*\\b${primaryClass}\\b[^"]*"`,
    'gi'
  );
  const matches = html.match(classPattern);
  return matches ? matches.length : 0;
}

function extractHeadContent(html) {
  const headMatch = html.match(/<head[^>]*>([\s\S]*?)<\/head>/i);
  if (!headMatch) return '';
  let headContent = headMatch[1];
  headContent = headContent.replace(/<meta\s+name="viewport"[^>]*>/gi, '');
  headContent = headContent.replace(/<meta\s+charset[^>]*>/gi, '');
  return headContent.trim();
}

function buildHyperframesHtml(originalHtml, args, slideCount) {
  const perSlide = args.duration ? args.duration / slideCount : 5;
  const totalDuration = args.duration || slideCount * 5;
  const escapedSelector = escapeSelector(args.slideSelector);

  const gsapCdn = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js';
  const hasGsap = originalHtml.includes('gsap');

  const timelineScript = `
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      const slides = document.querySelectorAll('${escapedSelector}');
      const perSlide = ${perSlide};
      const transition = ${args.transition};

      slides.forEach((slide, i) => {
        const start = i * perSlide;
        slide.style.position = 'absolute';
        slide.style.top = '0';
        slide.style.left = '0';
        slide.style.width = '${args.width}px';
        slide.style.height = '${args.height}px';
        slide.style.opacity = '0';

        tl.to(slide, { opacity: 1, duration: transition }, start);
        if (i > 0) {
          tl.to(slides[i - 1], { opacity: 0, duration: transition }, start);
        } else {
          tl.set(slide, { opacity: 1 }, 0);
        }
      });

      window.__timelines["main"] = tl;
    </script>`;

  const originalHead = extractHeadContent(originalHtml);

  const bodyMatch = originalHtml.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  const bodyContent = bodyMatch
    ? bodyMatch[1].replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    : originalHtml
        .replace(/<!doctype[^>]*>/i, '')
        .replace(/<html[^>]*>/i, '').replace(/<\/html>/i, '')
        .replace(/<head[^>]*>[\s\S]*?<\/head>/i, '')
        .replace(/<body[^>]*>/i, '').replace(/<\/body>/i, '')
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');

  const rootAttrs = `id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="${totalDuration}"
      data-width="${args.width}"
      data-height="${args.height}"`;

  const bodyStyle = `margin:0; width:${args.width}px; height:${args.height}px; overflow:hidden; position:relative;`;

  return `<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=${args.width}, height=${args.height}">
    ${originalHead}
    ${!hasGsap ? `<script src="${gsapCdn}"></script>` : ''}
  </head>
  <body style="${bodyStyle}">
    <div ${rootAttrs}>
      ${bodyContent}
    </div>
    ${!hasGsap ? `<script src="${gsapCdn}"></script>` : ''}
    ${timelineScript}
  </body>
</html>`;
}

function buildManifest() {
  return JSON.stringify({
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {
      "blocks": "compositions",
      "components": "compositions/components",
      "assets": "assets"
    }
  }, null, 2);
}

async function checkHyperframes() {
  try {
    const { stdout } = await execFileAsync('hyperframes', ['--version'], { timeout: 10000 });
    return stdout.trim();
  } catch {
    return null;
  }
}

async function renderWithHyperframes(projectDir, outputPath, args) {
  const hfArgs = ['render', '-o', outputPath];
  if (args.fps !== 30) hfArgs.push('--fps', String(args.fps));

  const { stdout, stderr } = await execFileAsync('hyperframes', hfArgs, {
    cwd: projectDir,
    timeout: 300000,
    env: { ...process.env, FORCE_COLOR: '0' },
  });

  return { stdout, stderr };
}

async function fallbackScreenshotRender(inputPath, outputPath, args) {
  log(args, '[fallback] HyperFrames 不可用，使用 Playwright 截圖 + FFmpeg 合成（無動畫）');

  const framesDir = resolve(tmpdir(), `html2video-frames-${Date.now()}`);
  await mkdir(framesDir, { recursive: true });

  const html = await readFile(inputPath, 'utf-8');
  const slideCount = detectSlides(html, args.slideSelector);
  const totalDuration = args.duration || slideCount * 5;
  const totalFrames = totalDuration * args.fps;
  const framesPerSlide = Math.ceil(totalFrames / slideCount);
  const escapedSelector = escapeSelector(args.slideSelector);

  try {
    const { execFileSync } = await import('node:child_process');

    for (let i = 0; i < slideCount; i++) {
      const frameIndex = i * framesPerSlide;
      const frameFile = resolve(framesDir, `frame-${String(frameIndex).padStart(6, '0')}.png`);

      const jsHideOthers = `
        const slides = document.querySelectorAll('${escapedSelector}');
        slides.forEach((s, idx) => { s.style.display = idx === ${i} ? 'flex' : 'none'; });
      `;

      execFileSync('npx', [
        'playwright', 'screenshot',
        `--viewport-size=${args.width},${args.height}`,
        '--wait-for-timeout=500',
        `file://${resolve(inputPath)}`,
        frameFile,
      ], {
        timeout: 30000,
        env: { ...process.env, PLAYWRIGHT_JAVASCRIPT: jsHideOthers },
      });

      if (!existsSync(frameFile)) {
        log(args, `[fallback] slide ${i} 截圖失敗，嘗試無 JS 模式`);
        execFileSync('npx', [
          'playwright', 'screenshot',
          `--viewport-size=${args.width},${args.height}`,
          `file://${resolve(inputPath)}`,
          frameFile,
        ], { timeout: 30000 });
      }

      for (let f = 1; f < framesPerSlide; f++) {
        const dupFile = resolve(framesDir, `frame-${String(frameIndex + f).padStart(6, '0')}.png`);
        await copyFile(frameFile, dupFile);
      }
    }

    await execFileAsync('ffmpeg', [
      '-y',
      '-framerate', String(args.fps),
      '-i', resolve(framesDir, 'frame-%06d.png'),
      '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p',
      '-preset', 'fast',
      outputPath,
    ], { timeout: 120000 });

    return { fallback: true };
  } finally {
    await rm(framesDir, { recursive: true, force: true }).catch(() => {});
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const inputPath = resolve(args.input);
  const outputPath = resolve(args.output);

  if (!existsSync(inputPath)) {
    console.error(`Input not found: ${inputPath}`);
    process.exit(2);
  }

  const html = await readFile(inputPath, 'utf-8');
  const slideCount = detectSlides(html, args.slideSelector);

  if (slideCount === 0) {
    console.error(`No slides found with selector "${args.slideSelector}"`);
    process.exit(2);
  }

  const totalDuration = args.duration || slideCount * 5;
  log(args, `[html2video] ${slideCount} slides, ${totalDuration}s @ ${args.fps}fps, ${args.width}×${args.height}`);

  let usedEngine = 'unknown';
  const hfVersion = await checkHyperframes();

  if (hfVersion) {
    log(args, `[html2video] HyperFrames v${hfVersion} detected, using primary render path`);
    usedEngine = 'hyperframes';

    const projectDir = resolve(tmpdir(), `html2video-hf-${Date.now()}`);
    await mkdir(projectDir, { recursive: true });

    try {
      const hfHtml = buildHyperframesHtml(html, args, slideCount);
      await writeFile(resolve(projectDir, 'index.html'), hfHtml);
      await writeFile(resolve(projectDir, 'hyperframes.json'), buildManifest());
      await writeFile(resolve(projectDir, 'package.json'), JSON.stringify({
        name: 'html2video-render',
        private: true,
        scripts: { render: 'hyperframes render' },
      }));

      await renderWithHyperframes(projectDir, outputPath, args);

      if (!existsSync(outputPath)) {
        log(args, '[html2video] HyperFrames render 未產出檔案，退化至 screenshot 方案');
        usedEngine = 'fallback-screenshot';
        await fallbackScreenshotRender(inputPath, outputPath, args);
      } else {
        log(args, `[html2video] render 完成: ${outputPath}`);
      }
    } finally {
      await rm(projectDir, { recursive: true, force: true }).catch(() => {});
    }
  } else {
    log(args, '[html2video] HyperFrames 不可用，使用退化方案');
    usedEngine = 'fallback-screenshot';
    await fallbackScreenshotRender(inputPath, outputPath, args);
  }

  if (!existsSync(outputPath)) {
    console.error('[html2video] FAIL: 未產出 MP4');
    process.exit(1);
  }

  const meta = {
    tool: 'html2video.mjs',
    version: '1.0.0',
    engine: usedEngine,
    hyperframes_version: hfVersion || null,
    input: args.input,
    output: args.output,
    slides: slideCount,
    duration_seconds: totalDuration,
    fps: args.fps,
    resolution: `${args.width}x${args.height}`,
  };

  if (!args.quiet) {
    console.log(`__VIDEO_META__${JSON.stringify(meta)}__END_META__`);
  }

  process.exit(0);
}

main().catch(err => {
  console.error(`[html2video] Fatal: ${err.message}`);
  process.exit(1);
});

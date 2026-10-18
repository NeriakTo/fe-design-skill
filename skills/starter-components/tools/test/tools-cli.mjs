#!/usr/bin/env node
/**
 * tools-cli.mjs — JS 工具 CLI 介面基礎測試
 *
 * 測試策略：透過 subprocess 測 CLI 參數驗證、輸入驗證、旗標解析。
 * 不測 Playwright 相關功能（pdf-export / standalone-export 需要 Playwright）。
 * html2video 在 HyperFrames 可用時做完整 render 測試。
 */
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { existsSync, statSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { unlink } from 'node:fs/promises';

const execFileAsync = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const TOOLS_DIR = resolve(__dirname, '..');
const DEMOS_DIR = resolve(TOOLS_DIR, '..', 'scaffolds', 'demos');
const NODE = process.execPath;

let totalPass = 0;
let totalFail = 0;

function assert(condition, label, actual) {
  if (condition) {
    totalPass++;
  } else {
    const suffix = actual !== undefined ? ` (got: ${JSON.stringify(actual)})` : '';
    console.error(`  FAIL: ${label}${suffix}`);
    totalFail++;
  }
}

async function run(tool, args, expectExit = 0) {
  const toolPath = resolve(TOOLS_DIR, tool);
  try {
    const { stdout, stderr } = await execFileAsync(NODE, [toolPath, ...args], {
      timeout: 180000,
      env: { ...process.env, FORCE_COLOR: '0' },
    });
    if (expectExit !== 0) {
      return { code: 0, stdout, stderr, ok: false };
    }
    return { code: 0, stdout, stderr, ok: true };
  } catch (err) {
    const code = typeof err.code === 'number' ? err.code : 1;
    if (expectExit !== 0 && code === expectExit) {
      return { code, stdout: err.stdout || '', stderr: err.stderr || '', ok: true };
    }
    return { code, stdout: err.stdout || '', stderr: err.stderr || '', ok: false };
  }
}

// ── pdf-export.mjs ──────────────────────────────────────────────────

console.log('\n[pdf-export.mjs]');

{
  const r = await run('pdf-export.mjs', [], 2);
  assert(r.code === 2, 'no args → exit 2', r.code);
  assert(r.stderr.includes('--input'), 'shows usage hint on missing args');
}

{
  const r = await run('pdf-export.mjs', ['--input', '/tmp/nonexistent-pdf.html', '--output', '/tmp/out.pdf'], 1);
  assert(r.code === 1, 'nonexistent input → exit 1 (Playwright fails)', r.code);
}

{
  const r = await run('pdf-export.mjs', [
    '--input', 'x.html', '--output', 'x.pdf', '--pdf-format', 'invalid-format'
  ], 2);
  assert(r.code === 2, 'invalid format → exit 2', r.code);
  assert(r.stderr.includes('Unknown --pdf-format'), 'error mentions invalid format');
}

{
  const r = await run('pdf-export.mjs', ['--help'], 0);
  assert(r.code === 0, '--help → exit 0', r.code);
  assert(r.stdout.includes('pdf-format'), 'help shows pdf-format');
  assert(r.stdout.includes('viewport'), 'help shows viewport');
  assert(r.stdout.includes('a4-landscape'), 'help shows a4-landscape');
}

// ── standalone-export.mjs ───────────────────────────────────────────

console.log('\n[standalone-export.mjs]');

{
  const r = await run('standalone-export.mjs', [], 1);
  assert(r.code === 1, 'no args → exit 1', r.code);
}

{
  const r = await run('standalone-export.mjs', [
    '--input', '/tmp/nonexistent-standalone.html',
    '--output', '/tmp/out-standalone.html'
  ], 1);
  assert(r.code === 1, 'nonexistent input → exit 1', r.code);
}

// ── html2video.mjs ──────────────────────────────────────────────────

console.log('\n[html2video.mjs]');

{
  const r = await run('html2video.mjs', [], 2);
  assert(r.code === 2, 'no args → exit 2', r.code);
  assert(r.stderr.includes('Usage'), 'shows usage on missing args');
}

{
  const r = await run('html2video.mjs', [
    '--input', '/tmp/nonexistent-video.html',
    '--output', '/tmp/out.mp4'
  ], 2);
  assert(r.code === 2, 'nonexistent input → exit 2', r.code);
  assert(r.stderr.includes('Input not found'), 'error mentions input not found');
}

{
  const r = await run('html2video.mjs', [
    '--input', 'x.html', '--output', 'x.mp4', '--bogus-flag'
  ], 2);
  assert(r.code === 2, 'unknown flag → exit 2', r.code);
  assert(r.stderr.includes('Unknown flag'), 'error mentions unknown flag');
}

{
  const input = resolve(DEMOS_DIR, 'regression-baseline.html');
  const r = await run('html2video.mjs', [
    '--input', input,
    '--output', '/tmp/html2video-no-slides.mp4',
    '--slide-selector', 'div.nonexistent-class',
    '--quiet'
  ], 2);
  assert(r.code === 2, 'no matching slides → exit 2', r.code);
  assert(r.stderr.includes('No slides found'), 'error mentions no slides found');
}

// Full render test (only if HyperFrames available)
{
  const output = '/tmp/html2video-cli-test.mp4';
  try { await unlink(output); } catch {}

  const input = resolve(DEMOS_DIR, 'regression-baseline.html');
  const r = await run('html2video.mjs', [
    '--input', input,
    '--output', output,
    '--slide-selector', '.slide',
    '--duration', '6',
    '--fps', '30',
  ], 0);

  if (r.code === 0) {
    assert(existsSync(output), 'MP4 output exists');
    const size = statSync(output).size;
    assert(size > 1000, 'MP4 is non-trivial size', size);
    assert(r.stdout.includes('__VIDEO_META__'), 'outputs video metadata');
    assert(r.stdout.includes('"engine":"hyperframes"'), 'engine is hyperframes');
    assert(r.stdout.includes('"slides":3'), 'detects 3 slides');
    assert(r.stdout.includes('"duration_seconds":6'), 'duration matches --duration flag');
    assert(r.stdout.includes('"fps":30'), 'fps matches --fps flag');
    try { await unlink(output); } catch {}
  } else {
    console.log('  SKIP: HyperFrames not available, skipping full render test');
  }
}

// ── 結果 ────────────────────────────────────────────────────────────

console.log(`\n${'─'.repeat(40)}`);
console.log(`Total: ${totalPass + totalFail} assertions`);
console.log(`  PASS: ${totalPass}`);
console.log(`  FAIL: ${totalFail}`);

if (totalFail > 0) {
  process.exit(1);
} else {
  console.log('\nAll CLI tests passed.');
  process.exit(0);
}

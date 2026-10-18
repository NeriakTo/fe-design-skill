#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TOOLS_DIR = resolve(__dirname, '..');
const DEMOS_DIR = resolve(TOOLS_DIR, '..', 'scaffolds', 'demos');
const EXPECTED = resolve(__dirname, 'regression-baseline.expected.json');

const html2pptx = resolve(TOOLS_DIR, 'html2pptx.mjs');
const input = resolve(DEMOS_DIR, 'regression-baseline.html');
const work = mkdtempSync(resolve(tmpdir(), 'html2pptx-regression-'));
const output = resolve(work, 'result.pptx');

try {

  console.log('regression: running html2pptx...');
  const nodeBin = process.execPath;
  const stdout = execFileSync(nodeBin, [html2pptx, '--input', input, '--output', output, '--quiet'],
    { encoding: 'utf-8', timeout: 60000 });

  const metaMatch = stdout.match(/__PPTX_META__(.+?)__END_META__/s);
  if (!metaMatch) {
    console.error('FAIL: no __PPTX_META__ in output');
    throw new Error('缺少匯出中繼資料');
  }

  const actual = JSON.parse(metaMatch[1]).per_slide_stats;
  const expected = JSON.parse(readFileSync(EXPECTED, 'utf-8')).per_slide_stats;

  let pass = true;
  for (let i = 0; i < expected.length; i++) {
    const exp = expected[i];
    const act = actual[i];
    if (!act) { console.error(`FAIL: slide ${i + 1} missing`); pass = false; continue; }
    for (const key of Object.keys(exp)) {
      if (JSON.stringify(exp[key]) !== JSON.stringify(act[key])) {
        console.error(`FAIL: slide ${i + 1} ${key}: expected ${JSON.stringify(exp[key])}, got ${JSON.stringify(act[key])}`);
        pass = false;
      }
    }
  }

  if (actual.length !== expected.length) {
    console.error(`FAIL: slide count ${actual.length} != expected ${expected.length}`);
    pass = false;
  }

  if (pass) {
    console.log(`PASS: ${expected.length} slides, all stats match`);
    process.exitCode = 0;
  } else {
    process.exitCode = 1;
  }

} finally {
  rmSync(work, { recursive: true, force: true });
}

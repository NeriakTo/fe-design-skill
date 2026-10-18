#!/usr/bin/env node
/**
 * demo-structure.mjs — 結構斷言測試（非 snapshot 比對）
 *
 * 驗證 3 個 demo HTML 的結構不變式：
 * - HTML 可解析（基本格式正確）
 * - 預期的 import / class / 元素存在
 * - 依賴的 scaffold 檔案存在
 *
 * 不做視覺 snapshot，維護成本最小化。
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DEMOS_DIR = resolve(__dirname, '..', '..', 'scaffolds', 'demos');
const CHARTS_DIR = resolve(__dirname, '..', '..', 'scaffolds', 'charts');

let totalPass = 0;
let totalFail = 0;

function assert(condition, label, actual) {
  if (condition) {
    totalPass++;
  } else {
    const suffix = actual !== undefined ? ` (got: ${actual})` : '';
    console.error(`  FAIL: ${label}${suffix}`);
    totalFail++;
  }
}

function readDemo(name) {
  const path = resolve(DEMOS_DIR, name);
  assert(existsSync(path), `${name} exists`);
  return readFileSync(path, 'utf-8');
}

// ── charts-demo.html ────────────────────────────────────────────────

console.log('\n[charts-demo.html]');
const chartsHtml = readDemo('charts-demo.html');

assert(chartsHtml.includes('<!DOCTYPE html>'), 'has doctype');
assert(chartsHtml.includes('lang="zh-Hant"'), 'lang=zh-Hant');
assert(chartsHtml.includes('<title>Charts Demo'), 'title present');

const expectedChartImports = [
  'pie_chart.mjs',
  'bar_chart.mjs',
  'kpi_card.mjs',
  'gantt_chart.mjs',
  'waterfall_chart.mjs',
  'matrix_chart.mjs',
  'process_flow.mjs',
];
for (const imp of expectedChartImports) {
  assert(chartsHtml.includes(imp), `imports ${imp}`);
}

assert(chartsHtml.includes('mckinsey-consulting.css'), 'loads mckinsey tokens');
assert(chartsHtml.includes('charts.css'), 'loads charts.css');
assert(chartsHtml.includes('id="charts"'), 'has #charts container');

for (const file of expectedChartImports) {
  const fullPath = resolve(CHARTS_DIR, file);
  assert(existsSync(fullPath), `scaffold exists: ${file}`);
}

assert(
  existsSync(resolve(CHARTS_DIR, 'charts.css')),
  'scaffold exists: charts.css'
);

const SCAFFOLDS_DIR = resolve(__dirname, '..', '..', 'scaffolds');
assert(
  existsSync(resolve(SCAFFOLDS_DIR, 'radar_chart.mjs')),
  'scaffold exists: radar_chart.mjs (spec P7.5, lives in scaffolds/ not charts/)'
);

// ── app-phone-demo.html ─────────────────────────────────────────────

console.log('\n[app-phone-demo.html]');
const appHtml = readDemo('app-phone-demo.html');

assert(appHtml.includes('<!DOCTYPE html>'), 'has doctype');
assert(appHtml.includes('lang="zh-Hant"'), 'lang=zh-Hant');
assert(appHtml.includes('<title>AppPhone Demo'), 'title present');

assert(appHtml.includes('ios-frame'), 'has iOS frame class');
assert(appHtml.includes('ios-frame__notch'), 'has notch element');
assert(appHtml.includes('ios-frame__screen'), 'has screen element');

assert(appHtml.includes('screen-login'), 'has login screen');
assert(appHtml.includes('screen-home'), 'has home screen');
assert(appHtml.includes('screen-detail'), 'has detail screen');

assert(appHtml.includes('id="app-root"'), 'has #app-root');
assert(appHtml.includes('id="event-log"'), 'has #event-log');
assert(appHtml.includes('nav-bar'), 'has nav-bar');
assert(appHtml.includes('breadcrumb'), 'has breadcrumb');

const screenCount = ['screen-login', 'screen-home', 'screen-detail']
  .filter(cls => appHtml.includes(cls)).length;
assert(screenCount === 3, 'defines 3 screen types via CSS classes', screenCount);

// ── regression-baseline.html ────────────────────────────────────────

console.log('\n[regression-baseline.html]');
const baselineHtml = readDemo('regression-baseline.html');

assert(baselineHtml.includes('<!DOCTYPE html>'), 'has doctype');
assert(baselineHtml.includes('PPTX Regression Baseline'), 'title present');

const slideClasses = baselineHtml.match(/class="slide\b[^"]*slide-\d+/g);
assert(slideClasses && slideClasses.length >= 3, 'has ≥3 slide sections', slideClasses?.length ?? 0);

assert(baselineHtml.includes('1920px'), 'uses 1920px width');
assert(baselineHtml.includes('1080px'), 'uses 1080px height');

const expectedJson = resolve(__dirname, 'regression-baseline.expected.json');
assert(existsSync(expectedJson), 'expected.json baseline exists');

// ── 結果 ────────────────────────────────────────────────────────────

console.log(`\n${'─'.repeat(40)}`);
console.log(`Total: ${totalPass + totalFail} assertions`);
console.log(`  PASS: ${totalPass}`);
console.log(`  FAIL: ${totalFail}`);

if (totalFail > 0) {
  process.exit(1);
} else {
  console.log('\nAll structure assertions passed.');
  process.exit(0);
}

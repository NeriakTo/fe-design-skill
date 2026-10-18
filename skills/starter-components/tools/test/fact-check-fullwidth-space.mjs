#!/usr/bin/env node
/**
 * fact-check-fullwidth-space.mjs — TASK 守門測試
 *
 * 缺陷：htmlToPlainText() 先把非換行空白收斂成半形，再把「中日韓＋空白＋中日韓」合併，
 * 但 Facts 表的條目沒有做同一套正規化，所以任何用全形空白 U+3000 排版的條目都比對不到。
 * 2026-09-14 TASK 的署名「產業顧問　示範講者 Example Speaker」與三段經歷共四條全部誤判。
 *
 * 本測試四個案例，前兩個是缺陷本身，後兩個是負向對照：
 * 修法若寫成「放寬比對」而不是「兩邊同套正規化」，案例 3、4 會跟著失守。
 */
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TOOL = resolve(__dirname, '..', 'fact-check.mjs');

const CASES = [
  {
    name: '全形空白分隔的署名要比對得到',
    fact: '產業顧問　示範講者 Example Speaker',
    html: '<p>產業顧問　示範講者 Example Speaker</p>',
    expectMissing: false,
  },
  {
    name: '全形空白分隔的年份與職稱要比對得到',
    fact: '2003 到 2014　資訊工程師',
    html: '<div><span>2003 到 2014　資訊工程師</span></div>',
    expectMissing: false,
  },
  {
    name: '負向對照：內容根本不在 HTML 裡，必須報缺漏',
    fact: '產業顧問　張三 Zhang San',
    html: '<p>產業顧問　示範講者 Example Speaker</p>',
    expectMissing: true,
  },
  {
    name: '負向對照：只差一個字，不是差空白，必須報缺漏',
    fact: '2003 到 2015　資訊工程師',
    html: '<div>2003 到 2014　資訊工程師</div>',
    expectMissing: true,
  },
];

let pass = 0;
let fail = 0;

for (const c of CASES) {
  const dir = mkdtempSync(join(tmpdir(), 'factcheck-test-'));
  try {
    const design = `---\nname: t\n---\n\n## Facts\n\n| 類型 | 內容 | 來源 |\n|---|---|---|\n| 測試 | ${c.fact} | 測試 |\n`;
    writeFileSync(join(dir, 'DESIGN.md'), design, 'utf-8');
    writeFileSync(join(dir, 'deck.html'), `<!doctype html><html><body>${c.html}</body></html>`, 'utf-8');
    const out = join(dir, 'out.json');
    spawnSync('node', [TOOL, '--design', join(dir, 'DESIGN.md'), '--html', join(dir, 'deck.html'),
                       '--output', out, '--llm-provider', 'none'], { encoding: 'utf-8' });
    const r = JSON.parse(readFileSync(out, 'utf-8'));
    const missingCount = r.positive_match?.missing?.length ?? -1;
    const actualMissing = missingCount > 0;
    if (actualMissing === c.expectMissing) {
      console.log(`  ✓ ${c.name}`);
      pass++;
    } else {
      console.log(`  ✗ ${c.name}`);
      console.log(`      預期缺漏=${c.expectMissing}，實際缺漏數=${missingCount}`);
      fail++;
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

console.log(`\nfact-check 全形空白：${pass} 通過，${fail} 失敗`);
process.exit(fail === 0 ? 0 : 1);

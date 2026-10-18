#!/usr/bin/env node
/**
 * deck-stage-persist.mjs — TASK 守門測試
 *
 * 缺陷：元件宣稱重載會停在原頁（storage-key / no-persist / start-index 三個屬性都在講這件事），
 * 實際重載一律回第一頁。2026-09-14 做 TASK 時查出。
 *
 * 四個案例：
 *   1、2 是缺陷本身（翻到第 5 頁重載要還在第 5 頁；localStorage 要真的存到值）。
 *   3 是 no-persist 的對照：帶了就該一律回 start-index，不該被 localStorage 覆寫。
 *   4 是 storage-key 的對照：兩份不同 key 的簡報不該互相干擾。
 * 修法若寫成「乾脆不要在 _collectSlides 裡 goto」而弄壞了首次載入，案例 3、4 會抓到。
 */
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:http';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..', '..');   // starter-components/
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
const server = createServer((req, res) => {
  const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!existsSync(p) || !p.startsWith(ROOT)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': MIME[extname(p)] || 'application/octet-stream' });
  res.end(readFileSync(p));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const PORT = server.address().port;
const URL_BASE = `http://127.0.0.1:${PORT}/tools/test/fixtures/deck-persist.html`;

const browser = await chromium.launch();
let pass = 0, fail = 0;

function check(name, actual, expect) {
  if (JSON.stringify(actual) === JSON.stringify(expect)) { console.log(`  ✓ ${name}`); pass++; }
  else { console.log(`  ✗ ${name}\n      預期 ${JSON.stringify(expect)}，實際 ${JSON.stringify(actual)}`); fail++; }
}

async function openDeck(ctx, attrs = '') {
  const pg = await ctx.newPage({ viewport: { width: 1280, height: 800 } });
  /* 屬性一律走查詢字串，fixture 會在元件升級前套上去；reload 也留得住。 */
  await pg.goto(URL_BASE + (attrs ? `?${attrs}` : ''), { waitUntil: 'networkidle' });
  await pg.waitForTimeout(500);
  return pg;
}

/* ── 1、2：翻頁後重載要停在原頁，且 localStorage 要有值 ── */
{
  const ctx = await browser.newContext();
  const pg = await openDeck(ctx);
  for (let i = 0; i < 4; i++) { await pg.keyboard.press('ArrowRight'); await pg.waitForTimeout(80); }
  const before = await pg.evaluate(() => window.__deck.current);
  const stored = await pg.evaluate(() => localStorage.getItem('deck-stage:current'));
  check('翻四次之後頁碼是 4', before, 4);
  check('localStorage 存到第 4 頁', stored, '4');
  await pg.reload({ waitUntil: 'networkidle' });
  await pg.waitForTimeout(600);
  const after = await pg.evaluate(() => window.__deck.current);
  const visible = await pg.evaluate(() => {
    const vis = [...document.querySelectorAll('section.slide')].filter((s) => s.offsetParent !== null);
    return vis.length === 1 ? vis[0].textContent.trim() : `可見頁數=${vis.length}`;
  });
  check('重載之後頁碼仍是 4', after, 4);
  check('重載之後畫面真的是第五頁', visible, '第五頁');
  await ctx.close();
}

/* ── 3：帶 no-persist 一律回 start-index ── */
{
  const ctx = await browser.newContext();
  const pre = await openDeck(ctx);
  for (let i = 0; i < 3; i++) { await pre.keyboard.press('ArrowRight'); await pre.waitForTimeout(80); }
  await pre.close();
  const pg = await openDeck(ctx, 'no-persist=&start-index=1');
  await pg.waitForTimeout(300);
  check('帶 no-persist 時回 start-index 而不是記憶值',
        await pg.evaluate(() => window.__deck.current), 1);
  await ctx.close();
}

/* ── 4：不同 storage-key 互不干擾 ── */
{
  const ctx = await browser.newContext();
  const a = await openDeck(ctx, 'storage-key=deck-a');
  for (let i = 0; i < 2; i++) { await a.keyboard.press('ArrowRight'); await a.waitForTimeout(80); }
  const keyA = await a.evaluate(() => localStorage.getItem('deck-a'));
  const keyDefault = await a.evaluate(() => localStorage.getItem('deck-stage:current'));
  check('自訂 key 存到自己那把', keyA, '2');
  check('自訂 key 沒有污染預設 key', keyDefault, null);
  await ctx.close();
}

await browser.close();
server.close();
console.log(`\ndeck-stage 頁碼記憶：${pass} 通過，${fail} 失敗`);
process.exit(fail === 0 ? 0 : 1);

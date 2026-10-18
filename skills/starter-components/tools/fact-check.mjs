#!/usr/bin/env node
// fact-check.mjs — Content Fidelity Lock cross-check (Part A grep + Part B LLM NLP)
// Copyright 2026 Kevin Du
// Licensed under the Apache License, Version 2.0 — see ../LICENSE-APACHE-2.0
// Part of starter-components skill (fe-design v1.4-short §24.3 P6.2)
//
// Usage:
//   node fact-check.mjs --design <DESIGN.md> --html <index.html> [--output <verify/fact-check.json>]
//                       [--llm-provider codex|gemini|none] [--max-html-chars 30000] [--quiet]
//
// Flags:
//   --design <path>         DESIGN.md 路徑（必填，需含 ## Facts 段）
//   --html <path>           index.html 路徑（必填）
//   --output <path>         JSON 結果輸出路徑（default: verify/fact-check.json）
//   --llm-provider <name>   gemini (default) | codex | none
//   --max-html-chars <n>    截斷送 LLM 的 plain-text 字元數（default 30000，避免 prompt 過長）
//   --quiet, -q             安靜模式
//
// Verdict 規則（fe-design v1.4-short §24.3.1 Lock 3）：
//   Part A 缺漏 ≠ 0           → FAIL
//   Part A PASS + Part B unknown = 0  → PASS
//   Part A PASS + Part B unknown > 0  → NEEDS_HUMAN_REVIEW
//   LLM 失敗（network / parse 錯）    → NEEDS_HUMAN_REVIEW（不阻斷 Stage 3，由人工複核）

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve as resolvePath } from 'node:path';
import { spawnSync } from 'node:child_process';

function parseArgs(argv) {
  const args = {
    design: null,
    html: null,
    output: 'verify/fact-check.json',
    llmProvider: 'gemini',
    maxHtmlChars: 30000,
    quiet: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--design') args.design = next();
    else if (a === '--html') args.html = next();
    else if (a === '--output') args.output = next();
    else if (a === '--llm-provider') args.llmProvider = next();
    else if (a === '--skip-llm') args.llmProvider = 'none';
    else if (a === '--max-html-chars') args.maxHtmlChars = parseInt(next(), 10);
    else if (a === '--quiet' || a === '-q') args.quiet = true;
    else if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    } else {
      console.error(`Unknown arg: ${a}`);
      process.exit(2);
    }
  }
  if (!args.design || !args.html) {
    printHelp();
    process.exit(2);
  }
  if (!['codex', 'gemini', 'none'].includes(args.llmProvider)) {
    console.error(`--llm-provider must be one of: codex, gemini, none (got: ${args.llmProvider})`);
    process.exit(2);
  }
  return args;
}

function printHelp() {
  console.error(
    `Usage: node fact-check.mjs --design <DESIGN.md> --html <index.html> [--output <path>]\n` +
      `       [--llm-provider gemini|codex|none] [--max-html-chars 30000] [--quiet]`
  );
}

// --- Markdown Facts table parser -----------------------------------------

const FACTS_HEADING_RE = /^##\s+(Facts|事實層|事實)\b/i;

// Codex R1 F1 修：separator-first 偵測，支援 edge-pipe 和 relaxed GFM 兩種格式。
// 先掃整個 ## Facts 區段找 separator row（連續 cell 都是 -+:?），其上一行為 header，
// 之後連續的 pipe row 為資料 row（直到遇到 blank / 非 pipe 行）。
function isSeparatorRow(cells) {
  return cells.length >= 2 && cells.every((c) => /^:?-{2,}:?$/.test(c));
}

// Codex R2 N3 修：支援 GFM `\|` escape — 先把 `\|` 替換成 sentinel，split 後還原。
const PIPE_SENTINEL = '';
function splitTableRow(line) {
  // 接受 `| a | b | c |` 與 relaxed `a | b | c`
  const trimmed = line.trim();
  // 至少要有一個非 escaped pipe
  if (!/(?<!\\)\|/.test(trimmed)) return null;
  const escaped = trimmed.replace(/\\\|/g, PIPE_SENTINEL);
  const stripped = escaped.replace(/^\||\|$/g, '');
  return stripped
    .split('|')
    .map((c) => c.replace(new RegExp(PIPE_SENTINEL, 'g'), '|').trim());
}

function parseFactsTable(designMd) {
  const lines = designMd.split('\n');
  const startIdx = lines.findIndex((l) => FACTS_HEADING_RE.test(l));
  if (startIdx < 0) return { found: false, facts: [] };

  // 收集 ## Facts 段內容到下一個 ## 為止
  const sectionLines = [];
  for (let i = startIdx + 1; i < lines.length; i++) {
    if (/^##\s+/.test(lines[i])) break;
    sectionLines.push(lines[i]);
  }

  // separator-first：找第一個 separator row
  let sepIdx = -1;
  for (let i = 0; i < sectionLines.length; i++) {
    const cells = splitTableRow(sectionLines[i]);
    if (cells && isSeparatorRow(cells)) {
      sepIdx = i;
      break;
    }
  }
  if (sepIdx <= 0) return { found: true, facts: [] };

  // header = sepIdx - 1（必須是非空 pipe row）
  const headerCells = splitTableRow(sectionLines[sepIdx - 1]);
  if (!headerCells) return { found: true, facts: [] };

  // 連續 data rows：sepIdx+1 起，遇到非 pipe row 即結束
  const facts = [];
  for (let i = sepIdx + 1; i < sectionLines.length; i++) {
    const cells = splitTableRow(sectionLines[i]);
    if (!cells) break; // blank line / 非 pipe → table 結束
    if (cells.length < 2) continue;
    const [type, content, ...rest] = cells;
    if (!content) continue;
    facts.push({
      type: type || '(未標)',
      content,
      source: rest.join(' | '),
    });
  }
  return { found: true, facts };
}

// --- Part A: positive match ---------------------------------------------

// 將 html 去除 script / style / comment + 解 entity → 提供 user-visible text 做 grep。
// 注意：保留 tag 之間的文字（用空白替換 tag），同字串若被 inline tag 切碎仍能命中（多數案例 OK）。
//
// Codex R1 F2 修：CJK 邊界 normalize — 移除「兩個連續 CJK 字符之間的空白」（合併 inline tag 切碎）。
// Codex R1 F3 修：補 numeric entity (decimal & hex) + &apos;。
function decodeNumericEntity(_, hex, code) {
  try {
    const cp = parseInt(code, hex ? 16 : 10);
    if (!Number.isFinite(cp) || cp < 0 || cp > 0x10ffff) return _;
    return String.fromCodePoint(cp);
  } catch {
    return _;
  }
}

const NAMED_ENTITY_MAP = {
  nbsp: ' ',
  amp: '&',
  lt: '<',
  gt: '>',
  quot: '"',
  apos: "'",
};

// Codex R2 N2 修：block-level tag 邊界保留為 newline，避免 CJK normalize 跨 block 合併
// 例如 `<div>東京</div> <div>都</div>` 不會誤合成「東京都」。
const BLOCK_TAG_RE =
  /<\/?(div|p|li|h[1-6]|tr|td|th|br|hr|article|section|main|aside|header|footer|nav|tbody|thead|table|figure|figcaption|blockquote|pre|address)\b[^>]*>/gi;

function htmlToPlainText(html) {
  let text = html
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ');

  // 階段 1：block tag → newline（保留結構邊界）
  text = text.replace(BLOCK_TAG_RE, '\n');
  // 階段 2：剩餘 inline tag → space
  text = text.replace(/<[^>]+>/g, ' ');

  // numeric entities：&#123; / &#x7B;
  text = text.replace(/&#(x?)([0-9a-fA-F]+);/g, (m, x, code) =>
    decodeNumericEntity(m, x.toLowerCase() === 'x', code)
  );
  // named entities
  text = text.replace(/&([a-zA-Z]+);/g, (m, name) => {
    const v = NAMED_ENTITY_MAP[name.toLowerCase()];
    return v !== undefined ? v : m;
  });

  // collapse 同行 whitespace（保留 \n 為 block 邊界 sentinel）
  return normalizeWhitespaceForMatch(text);
}

/**
 * 比對用的空白正規化。htmlToPlainText 與 Facts 條目都要走這一支，兩邊才比得起來。
 *
 * TASK（2026-09-14）：原本只有 HTML 那一側做，Facts 條目照原文比，
 * 於是任何用全形空白 U+3000 排版的條目（署名「產業顧問　示範講者 Example Speaker」、
 * 經歷「2003 到 2014　資訊工程師」）都比對不到，工具報 FAIL 但內容其實在裡面。
 * 修法是兩邊同套正規化，不是放寬比對——放寬會讓「只差一個字」也一起矇混過關。
 */
function normalizeWhitespaceForMatch(input) {
  // collapse 同行 whitespace（保留 \n 為 block 邊界 sentinel）；全形空白 U+3000 也在 \s 裡
  let text = input.replace(/[^\S\n]+/g, ' ');
  // collapse 連續 newline
  text = text.replace(/\n{2,}/g, '\n').trim();

  // CJK 邊界 normalize：「CJK + 空白(不含 newline) + CJK」→ 合併
  // CJK Unified Ideographs（含擴展 A）+ Hiragana + Katakana + Hangul Syllables
  // \n 不被合併（block 邊界保留）
  const CJK = '[\\u3040-\\u30ff\\u3400-\\u4dbf\\u4e00-\\u9fff\\uac00-\\ud7af]';
  const cjkBoundary = new RegExp(`(${CJK})[^\\S\\n]+(?=${CJK})`, 'g');
  let prev;
  do {
    prev = text;
    text = text.replace(cjkBoundary, '$1');
  } while (text !== prev);

  return text;
}

function partAPositiveMatch(facts, plainHtml) {
  const matched = [];
  const missing = [];
  for (const f of facts) {
    // Facts 條目走與 HTML 相同的正規化再比（TASK）
    if (plainHtml.includes(normalizeWhitespaceForMatch(f.content))) {
      matched.push(f);
    } else {
      missing.push(f);
    }
  }
  return {
    total: facts.length,
    matched_count: matched.length,
    missing,
    passed: facts.length > 0 && missing.length === 0,
  };
}

// --- Part B: LLM NLP entity extraction ----------------------------------

function buildLLMPrompt(facts, plainHtml) {
  const factsList = facts
    .map((f) => `- ${f.type}: ${f.content}`)
    .join('\n');
  return `你是 fe-design pipeline 的事實層稽核員。

任務：從下列 HTML 內文抽取所有「具體實體」（人名 / 公司名 / 產品名 / 具體日期 / 金額數字 / 量化指標），並比對 Facts 清單，列出「在 HTML 但不在 Facts」的 entity。

要求：
1. 只抽具體實體，不抽抽象詞（例如「我們」「客戶」「系統」不算）
2. 量化指標需含單位或語境（例如「3 人天」「79%」「8 週」算）
3. 若 entity 在 Facts 任一條目（type:content 任一欄）有出現視為已知，否則列入 unknown
4. 嚴格只輸出 JSON 物件，不加 Markdown code fence、不加任何說明文字

JSON schema:
{
  "extracted_entities": ["entity1", "entity2", ...],
  "unknown": [
    {"entity": "字面值", "type": "person|company|product|date|number|other", "context": "出現處片段（≤30 字）"}
  ]
}

Facts 清單：
${factsList}

HTML 內文（plain text，已去除 tag）：
${plainHtml}`;
}

// Codex R1 F4 修：balanced-brace JSON extractor — 從每個 `{` 開始平衡 walk，
// 字串內的 brace 不算（含 escape）。回傳第一個能成功 JSON.parse 的候選。
function findBalancedJsonObject(text, startIdx) {
  let depth = 0;
  let inString = false;
  let escape = false;
  for (let i = startIdx; i < text.length; i++) {
    const ch = text[i];
    if (escape) {
      escape = false;
      continue;
    }
    if (inString) {
      if (ch === '\\') escape = true;
      else if (ch === '"') inString = false;
      continue;
    }
    if (ch === '"') {
      inString = true;
      continue;
    }
    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) return text.slice(startIdx, i + 1);
    }
  }
  return null;
}

// Codex R2 N1 + R3 修：candidate 必須通過 schema validation
// 兩個陣列都必須存在 — 否則 `{"extracted_entities":[...], "unknown":"非陣列"}` 仍能 false PASS
// （後段 partBReverseCheck 會把非陣列 unknown 靜默降成 []，verdict 變 PASS）。
function isValidEntityExtractionResult(obj) {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    !Array.isArray(obj) &&
    Array.isArray(obj.extracted_entities) &&
    Array.isArray(obj.unknown)
  );
}

function extractJsonFromOutput(stdout) {
  if (!stdout) return null;
  // 嘗試 1：原始 stdout 從每個 `{` 開始平衡抽取，第一個 parse 且 schema-valid 的就回傳
  for (let i = 0; i < stdout.length; i++) {
    if (stdout[i] !== '{') continue;
    const candidate = findBalancedJsonObject(stdout, i);
    if (!candidate) continue;
    try {
      const parsed = JSON.parse(candidate);
      if (isValidEntityExtractionResult(parsed)) return parsed;
    } catch {
      // 此 candidate 不合法 JSON，往下一個 `{` 繼續
    }
  }
  // 嘗試 2：剝除 ```json fence 再做一次
  const stripped = stdout.replace(/```(?:json)?\s*|```/g, '');
  for (let i = 0; i < stripped.length; i++) {
    if (stripped[i] !== '{') continue;
    const candidate = findBalancedJsonObject(stripped, i);
    if (!candidate) continue;
    try {
      const parsed = JSON.parse(candidate);
      if (isValidEntityExtractionResult(parsed)) return parsed;
    } catch {}
  }
  return null;
}

function callCodex(prompt, log) {
  log('  → spawning codex exec (model: 預設, ephemeral session, skip-git-repo-check)');
  const r = spawnSync(
    'codex',
    // 2026-09-14 TASK：codex exec 已移除 --full-auto，帶著它會直接 exit 2、
    // Part B 整段拿不到結果而落到 NEEDS_HUMAN_REVIEW。這裡只做唯讀的實體抽取，
    // 本來就不需要核准旗標，拿掉即可（實測 0.149 系列可跑）。
    ['exec', '--skip-git-repo-check', '--ephemeral', '-'],
    { input: prompt, encoding: 'utf-8', timeout: 180_000 }
  );
  if (r.error) return { ok: false, error: `codex spawn error: ${r.error.message}` };
  if (r.status !== 0) {
    return {
      ok: false,
      error: `codex exit ${r.status}: ${(r.stderr || '').slice(0, 500)}`,
    };
  }
  const json = extractJsonFromOutput(r.stdout);
  if (!json) {
    return {
      ok: false,
      error: `codex output 無法解析 JSON。前 500 字: ${(r.stdout || '').slice(0, 500)}`,
    };
  }
  return { ok: true, data: json };
}

function callGemini(prompt, log) {
  log('  → spawning gemini -p (auto-gemini-3, --skip-trust)');
  // --skip-trust: gemini CLI 0.39.1 預設拒絕在「不信任目錄」執行；fact-check 不調 tool 純回答，安全。
  // 不用 --approval-mode yolo（原本給 tool calls 用，純 prompt 反而會被 trust 限制 override 出 error code）。
  const r = spawnSync(
    'gemini',
    ['-p', prompt, '--skip-trust', '-m', 'auto-gemini-3'],
    { encoding: 'utf-8', timeout: 180_000 }
  );
  if (r.error) return { ok: false, error: `gemini spawn error: ${r.error.message}` };
  if (r.status !== 0) {
    return {
      ok: false,
      error: `gemini exit ${r.status}: ${(r.stderr || '').slice(0, 500)}`,
    };
  }
  const json = extractJsonFromOutput(r.stdout);
  if (!json) {
    return {
      ok: false,
      error: `gemini output 無法解析 JSON。前 500 字: ${(r.stdout || '').slice(0, 500)}`,
    };
  }
  return { ok: true, data: json };
}

async function partBReverseCheck(facts, plainHtml, provider, maxChars, log) {
  if (provider === 'none') {
    return {
      skipped: true,
      reason: '--llm-provider none（純 grep 模式）',
      extracted_entities: [],
      unknown: [],
    };
  }
  const truncated = plainHtml.slice(0, maxChars);
  const prompt = buildLLMPrompt(facts, truncated);
  log(`  prompt size: ${prompt.length} chars (html plain: ${plainHtml.length}, truncated: ${truncated.length})`);

  let result;
  if (provider === 'codex') result = callCodex(prompt, log);
  else if (provider === 'gemini') result = callGemini(prompt, log);
  else throw new Error(`unknown provider: ${provider}`);

  if (!result.ok) {
    return {
      skipped: false,
      provider,
      error: result.error,
      extracted_entities: [],
      unknown: [],
    };
  }
  const data = result.data;
  return {
    skipped: false,
    provider,
    extracted_entities: Array.isArray(data.extracted_entities) ? data.extracted_entities : [],
    unknown: Array.isArray(data.unknown) ? data.unknown : [],
  };
}

// --- main --------------------------------------------------------------

// Codex R1 F5 修：Part B 為 mandatory，skipped (--skip-llm / --llm-provider none) 不可 PASS。
function decideVerdict(partA, partB) {
  if (!partA.passed) return 'FAIL';
  if (partB.skipped) return 'NEEDS_HUMAN_REVIEW'; // mandatory Part B 被跳過 → 強制人工複核
  if (partB.error) return 'NEEDS_HUMAN_REVIEW';
  if (partB.unknown && partB.unknown.length > 0) return 'NEEDS_HUMAN_REVIEW';
  return 'PASS';
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const log = (...m) => {
    if (!args.quiet) console.error(...m);
  };

  log(`fact-check.mjs (fe-design v1.4-short §24.3 P6.2)`);
  log(`  design: ${args.design}`);
  log(`  html:   ${args.html}`);
  log(`  output: ${args.output}`);
  log(`  llm:    ${args.llmProvider}`);

  const designText = await readFile(args.design, 'utf-8');
  const htmlText = await readFile(args.html, 'utf-8');
  const plainHtml = htmlToPlainText(htmlText);

  // Part A
  log(`\n[Part A] parse Facts table & positive match`);
  const facts = parseFactsTable(designText);
  if (!facts.found) {
    log(`  ⚠ DESIGN.md 沒有 ## Facts 段（trope-defying：deck/page mode shortcut 必須有 Facts table）`);
  }
  log(`  Facts table: ${facts.facts.length} 條`);
  const partA = partAPositiveMatch(facts.facts, plainHtml);
  log(
    `  positive match: ${partA.matched_count}/${partA.total} ` +
      `(missing: ${partA.missing.length}, ${partA.passed ? 'PASS' : 'FAIL'})`
  );
  if (partA.missing.length > 0) {
    for (const m of partA.missing.slice(0, 10)) {
      log(`    - missing: [${m.type}] ${m.content}`);
    }
    if (partA.missing.length > 10) log(`    - ...還有 ${partA.missing.length - 10} 條`);
  }

  // Part B
  log(`\n[Part B] LLM NLP entity extraction (provider: ${args.llmProvider})`);
  const partB = await partBReverseCheck(
    facts.facts,
    plainHtml,
    args.llmProvider,
    args.maxHtmlChars,
    log
  );
  if (partB.skipped) {
    log(`  skipped: ${partB.reason}`);
  } else if (partB.error) {
    log(`  ⚠ LLM error: ${partB.error}`);
  } else {
    log(
      `  extracted: ${partB.extracted_entities.length} entities, ` +
        `unknown (not in Facts): ${partB.unknown.length}`
    );
    for (const u of partB.unknown.slice(0, 10)) {
      log(`    - unknown: ${u.entity} (${u.type}) — ${u.context || ''}`);
    }
    if (partB.unknown.length > 10) log(`    - ...還有 ${partB.unknown.length - 10} 條`);
  }

  // Verdict + write
  const verdict = decideVerdict(partA, partB);
  log(`\nverdict: ${verdict}`);

  const result = {
    fact_check_version: '1.0',
    spec: 'fe-design v1.4-short §24.3 (P6.2)',
    timestamp: new Date().toISOString(),
    inputs: {
      design: args.design,
      html: args.html,
    },
    facts_table_found: facts.found,
    positive_match: {
      total: partA.total,
      matched: partA.matched_count,
      missing: partA.missing,
      passed: partA.passed,
    },
    reverse_check: {
      provider: args.llmProvider,
      skipped: partB.skipped || false,
      error: partB.error || null,
      extracted_entities: partB.extracted_entities,
      unknown: partB.unknown,
    },
    verdict,
  };

  const outPath = resolvePath(process.cwd(), args.output);
  await mkdir(dirname(outPath), { recursive: true });
  // atomic write（feedback-python-write-text-truncate-fail 教訓：write→tmp→rename）
  // Codex R1 F6 修：失敗時清理 tmp，避免殘留
  const tmpPath = `${outPath}.tmp`;
  const { rename, unlink } = await import('node:fs/promises');
  let renamed = false;
  try {
    await writeFile(tmpPath, JSON.stringify(result, null, 2), 'utf-8');
    await rename(tmpPath, outPath);
    renamed = true;
  } finally {
    if (!renamed) {
      try {
        await unlink(tmpPath);
      } catch {} // best-effort 清理
    }
  }
  log(`  → ${outPath}`);

  // exit code: PASS=0, NEEDS_HUMAN_REVIEW=2, FAIL=1
  if (verdict === 'PASS') process.exit(0);
  if (verdict === 'NEEDS_HUMAN_REVIEW') process.exit(2);
  process.exit(1);
}

main().catch((e) => {
  console.error('fact-check FAIL:', e.stack || e.message);
  process.exit(1);
});

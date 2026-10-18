import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, writeFileSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const tools = fileURLToPath(new URL('../', import.meta.url));

test('regression_uses_unique_temp_output_and_cleans_success_and_failure', () => {
  const outputs = [];
  for (const fail of [false, false, true]) {
    const code = `
      import childProcess from 'node:child_process';
      import { syncBuiltinESMExports } from 'node:module';
      import { readFileSync, writeFileSync } from 'node:fs';
      childProcess.execFileSync = (_node, args) => {
        const output = args[args.indexOf('--output') + 1];
        console.log('OUTPUT:' + JSON.stringify(output));
        writeFileSync(output, 'fixture');
        if (${fail}) throw new Error('模擬匯出失敗');
        return '__PPTX_META__' + readFileSync(${JSON.stringify(resolve(tools, 'test/regression-baseline.expected.json'))}, 'utf8') + '__END_META__';
      };
      syncBuiltinESMExports();
      await import(${JSON.stringify(new URL('./regression.mjs', import.meta.url).href)});
    `;
    let stdout;
    try {
      stdout = execFileSync(process.execPath, ['--input-type=module', '--eval', code],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
      assert.equal(fail, false);
    } catch (error) {
      assert.equal(fail, true);
      assert.match(error.stderr, /模擬匯出失敗/);
      stdout = error.stdout;
    }
    const output = JSON.parse(stdout.match(/^OUTPUT:(.+)$/m)[1]);
    outputs.push(output);
    assert.equal(dirname(dirname(output)), resolve(tmpdir()));
    assert.equal(existsSync(dirname(output)), false);
  }
  assert.equal(new Set(outputs).size, outputs.length);
});

test('symlink_cli_help_and_export', () => {
  const work = mkdtempSync(resolve(tmpdir(), 'standalone-offline-'));
  try {
    const html = '<html><head></head><body><p>成果</p></body></html>';
    const input = resolve(work, 'input.html');
    writeFileSync(input, html);
    for (const name of ['standalone-export.mjs', 'fonts-inline.mjs']) {
      const link = resolve(work, name);
      symlinkSync(resolve(tools, name), link);
      const help = execFileSync(process.execPath, [link, '--help'], { encoding: 'utf8' });
      assert.match(help, /Usage:/);
      const output = resolve(work, name + '.html');
      execFileSync(process.execPath, [link, '--input', input, '--output', output, '--quiet']);
      assert.equal(readFileSync(output, 'utf8'), html);
    }
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
});

test('inline_script_preserves_license_headers', () => {
  const work = mkdtempSync(resolve(tmpdir(), 'standalone-license-'));
  try {
    const script = '// Copyright 2026 Example\n// SPDX-License-Identifier: Apache-2.0\n'
      + '// Licensed under the Apache License, Version 2.0\n'
      + '/* License: Apache-2.0 */\nconsole.log("</script>");\n';
    writeFileSync(resolve(work, 'local.js'), script);
    const input = resolve(work, 'input.html');
    const output = resolve(work, 'output.html');
    writeFileSync(input, '<html><body><script src="local.js"></script></body></html>');
    execFileSync(process.execPath, [resolve(tools, 'standalone-export.mjs'),
      '--input', input, '--output', output, '--quiet']);
    const html = readFileSync(output, 'utf8');
    for (const line of script.split('\n').filter(line => line.startsWith('//') || line.startsWith('/*'))) {
      assert.ok(html.includes(line), line);
    }
    assert.ok(html.includes('<\\/script>'));
    assert.ok(!html.includes('src="local.js"'));
  } finally {
    rmSync(work, { recursive: true, force: true });
  }
});

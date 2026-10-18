"""檢查簡報文字；設定檔提供變體與署名。"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

AI = re.compile(r"claude|anthropic", re.I)
WORDING = re.compile("為什麼|怎麼|到底|卡著|卡住|卡在|拍板|掛著|變貴|變便宜|吃掉|交出去|打架|撞號|死結|催外部|一句話|先看這裡|這一題|不能不做|算不出來|綁走|去處|爆|搬過來|沒人認領")
QUESTIONS = re.compile("怎麼|為什麼|如何|是什麼|要不要|嗎|多少|哪|誰|何時|何處")


class VisibleText(HTMLParser):
    """抽可見文字與來源行；HTMLParser 用 html.unescape 解碼 entity，inline 標籤不打斷詞。"""
    blocks = {"p", "div", "section", "article", "li", "tr", "td", "th", "br",
              "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.text = []
        self.lines = []
        self.notes = []
        self.headings = []
        self.heading = None

    def append(self, value, line):
        self.text.extend(value)
        for char in value:
            self.lines.append(line)
            if char == "\n":
                line += 1
        if self.heading is not None:
            self.heading[1].append(value)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "data-notes" and value is not None:
                self.notes.append((self.getpos()[0], value))
        if tag in {"script", "style", "template"}:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag in self.blocks:
            self.append("\n", self.getpos()[0])
        if tag in {"h1", "h2", "h3"}:
            self.heading = [self.getpos()[0], []]

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in {"h1", "h2", "h3"} and self.heading is not None:
            self.headings.append((self.heading[0], "".join(self.heading[1]).strip()))
            self.heading = None
        if tag in self.blocks:
            self.append("\n", self.getpos()[0])

    def handle_data(self, data):
        if not self.hidden:
            self.append(data, self.getpos()[0])


def load_config(path=None):
    config = json.loads(Path(path or Path(__file__).with_name("deck-gates.config.json")).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("variants"), dict) or not config["variants"]:
        raise ValueError("variants 必須是非空物件")
    for name, rules in config["variants"].items():
        if not name.strip() or not isinstance(rules, dict):
            raise ValueError("變體必須有名稱與規則物件")
        for key in ("required", "forbidden"):
            values = rules.get(key, [])
            if not isinstance(values, list) or any(not isinstance(x, str) or not x.strip() for x in values):
                raise ValueError(key + " 必須是非空字串陣列（陣列可空）")
            for value in values:
                re.compile(value)
    scanners = config.get("auxiliary_scanners", [])
    if not isinstance(scanners, list) or any(not isinstance(x, str) or not x.strip() for x in scanners):
        raise ValueError("auxiliary_scanners 必須是路徑字串陣列")
    return config


def run(path, variant, config_path=None):
    config = load_config(config_path)
    if variant not in config["variants"]:
        raise ValueError("未知變體：" + variant)
    raw = path.read_text(encoding="utf-8")
    parser = VisibleText()
    parser.feed(raw)
    parser.close()
    visible = "".join(parser.text)
    hits = 0
    errors = 0

    def hit(gate, line, detail):
        nonlocal hits
        hits += 1
        print(f"硬規則 {path}:{line}: [{gate}] {detail}", flush=True)

    def scan(pattern, text, gate, mapping=None):
        for match in pattern.finditer(text):
            line = mapping[match.start()] if mapping else text.count("\n", 0, match.start()) + 1
            hit(gate, line, match.group())

    # 換行隔開字元以避免詞組轉換；全篇只啟動一次 opencc。
    # Big5 可編碼字元保留，無須維護過度轉換例外清單。
    try:
        characters = list(dict.fromkeys((raw + visible).replace("\n", "")))
        converted = subprocess.run(["opencc", "-c", "s2t"], input="\n".join(characters),
                                   text=True, capture_output=True, check=True).stdout.split("\n")
        if len(characters) != len(converted) and characters:
            raise subprocess.SubprocessError("opencc 逐字轉換結果無法對應")
        replacements = dict(zip(characters, converted))
        seen = set()
        for text, mapping in ((raw, None), (visible, parser.lines)):
            line = 1
            for index, before in enumerate(text):
                source_line = mapping[index] if mapping else line
                try:
                    before.encode("big5")
                except UnicodeEncodeError:
                    after = replacements[before]
                    if before != after and (source_line, before) not in seen:
                        hit("簡體字", source_line, f"{before!r} → {after!r}")
                        seen.add((source_line, before))
                if before == "\n":
                    line += 1
    except (OSError, subprocess.SubprocessError) as exc:
        errors += 1
        print(f"錯誤：opencc 未完成：{exc}", flush=True)

    scan(AI, raw, "AI 標註")
    scan(AI, visible, "AI 標註", parser.lines)
    scan(WORDING, visible, "口語與俚俗", parser.lines)
    for line, heading in parser.headings:
        if QUESTIONS.search(heading):
            hit("疑問句標題", line, heading)

    rules = config["variants"][variant]
    for required in rules.get("required", []):
        if not (re.search(required, raw) or re.search(required, visible)):
            hit("署名缺漏", 1, required)
    for forbidden in rules.get("forbidden", []):
        pattern = re.compile(forbidden, re.I)
        scan(pattern, raw, "署名禁止字串")
        scan(pattern, visible, "署名禁止字串", parser.lines)

    sidecar = Path(str(path) + ".gates.json")
    if sidecar.exists():
        facts = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(facts, dict):
            raise ValueError(f"{sidecar}：必須是 JSON 物件")
        for key in ("required", "forbidden"):
            if not isinstance(facts.get(key), list) or any(not isinstance(x, str) or not x.strip() for x in facts[key]):
                raise ValueError(f"{sidecar}：{key} 必須是非空字串陣列（陣列可空）")
        for required in facts["required"]:
            if required not in visible:
                hit("Facts 署名缺漏", 1, required)
        for forbidden in facts["forbidden"]:
            pattern = re.compile(re.escape(forbidden), re.I)
            scan(pattern, visible, "Facts 禁止字串", parser.lines)
            for line, note in parser.notes:
                if pattern.search(note):
                    hit("講者備註禁止字串", line, forbidden)
        print(f"講者備註 {len(parser.notes)} 則已核對", flush=True)
    else:
        print("限制：無署名 sidecar，未核對 brief 實際名稱；新案須補產。", flush=True)

    # 每行前加普通文字，避免 Markdown 掃描器把 HTML 可見內容誤當程式碼略過。
    # 輸出的行號可透過來源表定位原始 HTML；純文字不含 script/style/template。
    with tempfile.TemporaryDirectory(prefix="deck-gates-") as work:
        plain = Path(work) / "deck-text.md"
        lines = visible.splitlines(keepends=True)
        output = []
        offset = 0
        source_lines = []
        for line in lines:
            source = parser.lines[offset] if offset < len(parser.lines) else 1
            output.append(f"文字 {line.strip()}\n")
            source_lines.append(source)
            offset += len(line)
        plain.write_text("".join(output), encoding="utf-8")
        for scanner_path in config.get("auxiliary_scanners", []):
            scanner = Path(scanner_path)
            name = scanner.name
            print(f"輔助詞表 {name}（命中不擋；行號對應原 HTML）", flush=True)
            result = subprocess.run(["bash", str(scanner), str(plain)], text=True, capture_output=True)
            for message in result.stdout.splitlines():
                match = re.match(r"(\s*)(\d+):(.*)", message)
                if match and 1 <= int(match[2]) <= len(source_lines):
                    message = f"{path}:{source_lines[int(match[2]) - 1]}:{match[3]}"
                print(message, flush=True)
            if result.stderr:
                print(result.stderr, file=sys.stderr, flush=True)
            if result.returncode:
                errors += 1
                print(f"錯誤：{name} 執行失敗，退出碼 {result.returncode}", flush=True)
    rc = 2 if errors else (1 if hits else 0)
    print(f"DECK_GATES {'ERROR' if errors else ('FAIL' if hits else 'PASS')} variant={variant} 硬規則={hits} 工具錯誤={errors} exit={rc}", flush=True)
    return rc


if __name__ == "__main__":
    try:
        cli = argparse.ArgumentParser()
        cli.add_argument("path", type=Path)
        cli.add_argument("variant")
        cli.add_argument("--config", type=Path)
        args = cli.parse_args()
        sys.exit(run(args.path, args.variant, args.config))
    except (OSError, ValueError, re.error, subprocess.SubprocessError) as exc:
        print(f"DECK_GATES ERROR：{exc} exit=2", file=sys.stderr)
        sys.exit(2)

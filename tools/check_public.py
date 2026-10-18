"""公開前掃描；私有詞表必須留在倉庫外。"""
import argparse
import io
import tarfile
import unicodedata
import zipfile
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = [r'/' + r'Users/', r'/' + r'home/', r'C:\\Users\\',
         r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}',
         r'(?<!\d)\d{17,20}(?!\d)', r'T-\d{3,4}(?!\d)', r'wiki[0-9a-fA-F]{8}']


def files(root):
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.pytest_cache'}
                         and not (Path(directory) / d).is_symlink())
        for name in dirs:
            yield Path(directory) / name
        for name in sorted(names):
            path = Path(directory) / name
            yield path


def simplified_map(text):
    characters = []
    for char in dict.fromkeys(text):
        if not ('\u3400' <= char <= '\u9fff' or '\U00020000' <= char <= '\U000323af'):
            continue
        try:
            char.encode('big5')
        except UnicodeEncodeError:
            characters.append(char)
    # 即使沒有中文，也確認工具可以執行。
    converted = subprocess.run(['opencc', '-c', 's2t'], input='\n'.join(characters),
                               text=True, capture_output=True, check=True).stdout.split('\n')
    if characters and len(characters) != len(converted):
        raise ValueError('opencc 逐字轉換結果無法對應')
    return {before: after for before, after in zip(characters, converted) if before != after}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root', type=Path, default=ROOT)
    cli.add_argument('--terms', type=Path, default=Path(os.environ.get(
        'FE_DESIGN_PRIVATE_TERMS', '~/.config/fe-design-skill/private-terms.txt')).expanduser())
    cli.add_argument('--allow-missing-terms', action='store_true')
    args = cli.parse_args(argv)
    root = args.root.resolve()
    errors = 0
    patterns = [re.compile(rule) for rule in RULES]
    try:
        terms = args.terms.expanduser().resolve()
        if terms.is_relative_to(root):
            raise ValueError('私有詞表必須在倉庫外')
        patterns.extend(re.compile(line) for line in terms.read_text(encoding='utf-8').splitlines()
                        if line.strip() and not line.startswith('#'))
    except FileNotFoundError:
        print('私有字樣未檢查')
        errors += not args.allow_missing_terms
    except (OSError, ValueError, re.error) as exc:
        print(f'私有字樣未檢查：{exc}')
        errors += 1
    sources = []
    if not root.is_dir():
        print('錯誤：掃描根目錄不存在')
        return 2
    binaries = []

    def collect(name, data):
        nonlocal errors
        sources.append((name, name))
        lower = name.lower()
        if lower.endswith(('.tgz', '.tar.gz', '.zip')):
            try:
                if lower.endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        for member in archive.infolist():
                            if member.is_dir():
                                sources.append((name + '!' + member.filename, member.filename))
                            else:
                                collect(name + '!' + member.filename, archive.read(member))
                else:
                    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
                        for member in archive:
                            member_name = name + '!' + member.name
                            if member.isfile():
                                with archive.extractfile(member) as stream:
                                    collect(member_name, stream.read())
                            else:
                                sources.append((member_name, member.name))
            except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
                errors += 1
                print(f'錯誤：{name} 壓縮檔無法檢查：{exc}')
        elif b'\x00' in data[:8192]:
            binaries.append(name)
        else:
            try:
                sources.append((name, data.decode('utf-8')))
            except UnicodeDecodeError:
                errors += 1
                print(f'錯誤：{name} 無法以 UTF-8 檢查')

    for path in files(root):
        try:
            name = str(path.relative_to(root))
            if path.is_symlink() or path.is_dir():
                sources.append((name, name))
            else:
                collect(name, path.read_bytes())
        except OSError as exc:
            print(f'錯誤：{path.relative_to(root)}：{exc}')
            errors += 1
    replacements = {}
    try:
        replacements = simplified_map(''.join(text + unicodedata.normalize('NFKC', text) for name, text in sources))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'簡體字未檢查：{exc}')
        errors += 1
    hits = 0
    code_hits = 0
    for name, text in sources:
        for number, line in enumerate(text.splitlines(), 1):
            variants = (line, unicodedata.normalize('NFKC', line))
            found = {match.group() for variant in variants for pattern in patterns
                     for match in pattern.finditer(variant)}
            found.update(char for variant in variants for char in variant if char in replacements)
            for value in sorted(found):
                print(f'{name}:{number}:{value}')
                hits += 1
                code_hits += not name.lower().endswith('.md')
    print(f'未掃描的二進位檔：{len(binaries)}')
    for name in binaries:
        print(f'  {name}')
    print(f'公開檢查：命中 {hits}；非 Markdown 命中 {code_hits}；檢查錯誤 {errors}')
    return 2 if errors else int(bool(hits))


if __name__ == '__main__':
    sys.exit(main())

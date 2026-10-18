#!/bin/bash
# 退出碼 0 通過、1 硬規則命中、2 無法完成檢查。
set -u
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd) || exit 2
exec python3 "$SCRIPT_DIR/deck_gates.py" "$@"

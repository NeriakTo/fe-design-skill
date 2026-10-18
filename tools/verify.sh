#!/bin/bash
# 各套檢查皆執行完畢，再彙整退出狀態。
# 維護者：bash tools/verify.sh（不帶參數，要求私有詞表）。
# 外部使用者：bash tools/verify.sh --allow-missing-terms。
# 所有參數原樣轉交給 check_public.py。
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd) || exit 1
cd "$ROOT" || exit 1
export PYTHONDONTWRITEBYTECODE=1
results=()
failed=0
run_suite() {
  local label="$1"
  shift
  echo "=== $label ==="
  "$@"
  local code=$?
  if [ "$code" -eq 0 ]; then
    results+=("$label: PASS")
  else
    results+=("$label: FAIL (exit=$code)")
    failed=1
  fi
}
run_suite anti-slop-review python3 -m pytest -q -p no:cacheprovider skills/anti-slop-review
run_suite deck-gates python3 -m pytest -q -p no:cacheprovider skills/starter-components/scripts/test_deck_gates.py
run_suite design-context-import python3 -m pytest -q -p no:cacheprovider skills/design-context-import/tests
for test in skills/starter-components/tools/test/*.mjs; do
  case "$test" in
    *fact-check-fullwidth-space.mjs|*demo-structure.mjs|*standalone-offline.mjs) run_suite "$test" node "$test" ;;
    *)
      if node -e "require('playwright')" >/dev/null 2>&1; then
        run_suite "$test" node "$test"
      else
        echo "略過 ${test}：本機無可解析的 playwright"
        results+=("$test: SKIP (playwright 不存在)")
      fi ;;
  esac
done
run_suite tools/tests python3 -m pytest -q -p no:cacheprovider tools/tests
run_suite check-public python3 tools/check_public.py "$@"
echo '=== 結果摘要 ==='
printf '%s\n' "${results[@]}"
exit "$failed"

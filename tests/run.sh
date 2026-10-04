#!/usr/bin/env bash
# gate.py가 샘플마다 기대한 exit 값을 내는지 확인한다.
# 샘플은 진짜 rules.json과 docs/prd.md를 쓰는 임시 폴더에서 돌린다. 프로젝트 파일은 건드리지 않는다.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/tests/fixtures"
pass=0; fail=0

while read -r name stage expect when; do
  [[ -z "$name" || "$name" == \#* ]] && continue
  tmp="$(mktemp -d)"
  mkdir -p "$tmp/docs"
  cp "$ROOT/rules.json" "$tmp/"
  cp "$ROOT/docs/prd.md" "$tmp/docs/"
  cp -R "$FIX/pass/output" "$tmp/output"
  [[ "$name" != pass && "$when" == before ]] && cp -R "$FIX/$name/output/." "$tmp/output/"
  python3 "$ROOT/scripts/snapshot.py" --stage "$stage" --root "$tmp" >/dev/null
  [[ "$name" != pass && "$when" == after ]] && cp -R "$FIX/$name/output/." "$tmp/output/"
  out="$(python3 "$ROOT/scripts/gate.py" --stage "$stage" --root "$tmp")"; got=$?
  if [[ "$got" == "$expect" ]]; then
    pass=$((pass+1)); echo "ok    $name ($stage) exit=$got"
  else
    fail=$((fail+1)); echo "WRONG $name ($stage) exit=$got, 기대=$expect"; echo "$out" | sed 's/^/      /'
  fi
  [[ "$got" == 1 && "$expect" == 1 ]] && echo "$out" | sed -n '2p' | sed 's/^/      /'
  rm -rf "$tmp"
done < "$FIX/../cases.txt"

echo "결과: 맞음 $pass / 틀림 $fail"
[[ "$fail" == 0 ]]

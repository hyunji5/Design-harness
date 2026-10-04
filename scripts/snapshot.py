#!/usr/bin/env python3
"""단계 시작 때 output/ 파일 목록과 해시를 output/state.json에 남긴다. 오케스트레이터만 실행한다.

사용: python3 scripts/snapshot.py --stage s1 [--root 프로젝트_경로]
"""
import argparse
import json
from pathlib import Path

from gate import STAGES, output_hashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    root = Path(args.root)
    rules = json.loads((root / "rules.json").read_text(encoding="utf-8"))
    state_path = root / "output" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state["snapshot"] = {"stage": args.stage, "files": output_hashes(root, rules)}
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"snapshot {args.stage}: 파일 {len(state['snapshot']['files'])}개 기록")


if __name__ == "__main__":
    main()

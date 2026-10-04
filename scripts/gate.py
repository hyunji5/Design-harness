#!/usr/bin/env python3
"""단계 판정 스크립트. rules.json과 output/ 파일만 읽고, 아무 파일도 고치지 않는다.

사용: python3 scripts/gate.py --stage s1 [--root 프로젝트_경로]
통과하면 exit 0, 실패하면 이유를 출력하고 exit 1.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

STAGES = ["s1", "s2", "s3", "s4", "s5"]


class Gate:
    def __init__(self, root, stage):
        self.root = Path(root)
        self.stage = stage
        self.errors = []
        self.rules = json.loads((self.root / "rules.json").read_text(encoding="utf-8"))

    def fail(self, msg):
        self.errors.append(msg)

    def read(self, rel):
        path = self.root / rel
        if not path.exists():
            self.fail(f"파일 없음: {rel}")
            return None
        return path.read_text(encoding="utf-8")

    def read_json(self, rel):
        text = self.read(rel)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.fail(f"JSON 형식 오류: {rel} ({e})")
            return None

    # ---------- 공통 ----------

    def check_prd_screens(self):
        """rules.json의 화면 목록이 PRD 4장과 같은지 본다. PRD가 바뀌면 사람이 rules.json을 고쳐야 한다."""
        prd = self.read(self.rules["prd"]["path"])
        if prd is None:
            return
        heading = self.rules["prd"]["screens_heading"]
        if heading not in prd:
            self.fail(f"PRD에서 '{heading}' 장을 찾을 수 없음")
            return
        body = prd.split(heading, 1)[1].split("\n## ", 1)[0]
        found = []
        for line in body.splitlines():
            m = re.match(r"\s*\d+\.\s+(.+)", line)
            if m:
                name = re.sub(r"\s*\(.*\)\s*$", "", m.group(1)).strip()
                found.append(re.sub(r"\s*화면$", "", name))
        if found != self.rules["screens"]:
            self.fail(f"PRD 화면 목록 {found}과 rules.json screens {self.rules['screens']}가 다름. 사람이 rules.json을 고쳐야 함")

    def check_scope(self):
        """이 단계 폴더 밖의 output 파일이 바뀌었는지 본다 (snapshot.py 기록과 비교)."""
        state_path = self.root / "output" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        snap = state.get("snapshot")
        if not snap or snap.get("stage") != self.stage:
            self.fail(f"{self.stage} 시작 기록 없음. 먼저 scripts/snapshot.py --stage {self.stage}를 실행해야 함")
            return
        now = output_hashes(self.root, self.rules)
        before = snap.get("files", {})
        own = f"output/{self.stage}/"
        protected = set(self.rules["scope"]["protected_files"])
        for rel in sorted(set(before) | set(now)):
            if before.get(rel) == now.get(rel):
                continue
            if rel in protected:
                self.fail(f"오케스트레이터만 쓰는 파일이 단계 중에 바뀜: {rel}")
            elif not rel.startswith(own):
                self.fail(f"편집 범위 밖의 파일이 바뀜: {rel}")

    def is_exception(self, screen, check, value):
        for ex in self.rules.get("exceptions", []):
            if ex.get("screen") == screen and ex.get("check") == check and str(ex.get("value")).lower() == str(value).lower():
                return True
        return False

    # ---------- S1 ----------

    def check_s1(self):
        r = self.rules["s1"]
        pattern = re.compile(r["link_pattern"])
        board = self.read(r["board"])
        notes = self.read(r["notes"])
        if board is None or notes is None:
            return
        sections = split_sections(board)
        all_links = set()
        for screen in self.rules["screens"]:
            if screen not in sections:
                self.fail(f"레퍼런스 보드에 '## {screen}' 섹션 없음")
                continue
            links = set(pattern.findall(sections[screen]))
            all_links |= links
            lo, hi = r["links_per_screen"]["min"], r["links_per_screen"]["max"]
            if not lo <= len(links) <= hi:
                self.fail(f"레퍼런스 보드 '{screen}': uibowl 링크 {len(links)}개 (허용 {lo}~{hi}개)")

        decided = {}
        for row in table_rows(notes):
            links = pattern.findall(" ".join(row))
            if not links:
                continue
            decision = next((d for d in r["decisions"] if any(c == d for c in row)), None)
            stories = {int(n) for n in re.findall(r"#(\d+)", " ".join(row))}
            for link in links:
                decided[link] = (decision, stories)
        for link in sorted(all_links):
            if link not in decided:
                self.fail(f"분석 노트에 판단이 없는 레퍼런스: {link}")
                continue
            decision, stories = decided[link]
            if decision is None:
                self.fail(f"분석 노트 판단이 {r['decisions']} 중 하나가 아님: {link}")
            elif decision == r["story_required_for"]:
                valid = stories & set(self.rules["user_stories"])
                if not valid:
                    self.fail(f"'{decision}'인데 유저스토리 번호(#{self.rules['user_stories'][0]}~#{self.rules['user_stories'][-1]})가 없음: {link}")

    # ---------- S2 ----------

    def check_s2(self):
        spec = self.read(self.rules["s2"]["spec"])
        if spec is None:
            return
        sections = split_sections(spec)
        for screen, words in self.rules["s2"]["keywords"].items():
            if screen not in sections:
                self.fail(f"화면 설계서에 '## {screen}' 섹션 없음")
                continue
            missing = [w for w in words if w not in sections[screen]]
            if missing:
                self.fail(f"화면 설계서 '{screen}'에 PRD 키워드 빠짐: {', '.join(missing)}")

    # ---------- S3 ----------

    def check_s3(self):
        r = self.rules["s3"]
        text = self.read(r["key_screens"])
        if text is None:
            return
        rows = table_dicts(text)
        lo, hi = r["frames"]["min"], r["frames"]["max"]
        if not lo <= len(rows) <= hi:
            self.fail(f"키 스크린 프레임 {len(rows)}개 (허용 {lo}~{hi}개)")
        frame = self.rules["allowed"]["frame"]
        for row in rows:
            for col in ("화면", "프레임 ID", "너비", "높이"):
                if not row.get(col):
                    self.fail(f"키 스크린 표에 '{col}' 값 없음: {row}")
            if row.get("너비") != str(frame["width"]) or row.get("높이") != str(frame["height"]):
                self.fail(f"키 스크린 '{row.get('화면')}' 크기 {row.get('너비')}×{row.get('높이')} (허용 {frame['width']}×{frame['height']})")
        names = {row.get("화면") for row in rows}
        for must in r["must_include"]:
            if must not in names:
                self.fail(f"키 스크린에 '{must}' 없음")
        approval = self.root / self.rules["approval"]["path"]
        if approval.exists():
            self.check_reject_reason(self.approval_fields(approval.read_text(encoding="utf-8")))

    def approval_fields(self, text):
        fields = {}
        for line in text.splitlines():
            m = re.match(r"\s*[-*]?\s*([^:：]+)[:：]\s*(.*)", line)
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
        return fields

    def check_reject_reason(self, fields):
        r = self.rules["approval"]
        if fields.get("결정") == r["rejected_value"] and not fields.get(r["reject_reason_field"]):
            self.fail(f"승인 기록이 '{r['rejected_value']}'인데 '{r['reject_reason_field']}' 없음 (오케스트레이터가 사람 말을 기록해야 함)")

    def check_approval(self):
        r = self.rules["approval"]
        text = self.read(r["path"])
        if text is None:
            return
        fields = self.approval_fields(text)
        self.check_reject_reason(fields)
        for f in r["fields"]:
            if not fields.get(f):
                self.fail(f"승인 기록에 '{f}' 없음")
        if fields.get("결정자") and fields["결정자"] != r["decider"]:
            self.fail(f"결정자가 '{r['decider']}'가 아님: {fields['결정자']}")
        if fields.get("결정") and fields["결정"] != r["approved_value"]:
            self.fail(f"S3가 승인되지 않음 (결정: {fields['결정']})")

    # ---------- S4 ----------

    def load_screens(self):
        data = self.read_json(self.rules["s4"]["screens"])
        if data is None:
            return None
        screens = {s.get("name"): s for s in data.get("screens", [])}
        for name in self.rules["screens"]:
            if name not in screens:
                self.fail(f"s4-screens.json에 화면 '{name}' 없음")
        extra = set(screens) - set(self.rules["screens"])
        if extra:
            self.fail(f"s4-screens.json에 PRD에 없는 화면: {', '.join(sorted(map(str, extra)))}")
        return screens

    def check_s4(self):
        self.check_approval()
        components = self.read(self.rules["s4"]["components"])
        if components is not None and not components.strip():
            self.fail(f"컴포넌트 목록이 비어 있음: {self.rules['s4']['components']}")
        tokens = self.read_json(self.rules["s4"]["tokens"])
        screens = self.load_screens()
        if tokens is None or screens is None:
            return
        token_sets = {
            "fontSizes": set(flatten(tokens.get("fontSize", {}))),
            "radii": set(flatten(tokens.get("radius", {}))),
            "spacings": set(flatten(tokens.get("spacing", {}))),
            "colors": {str(v).lower() for v in flatten(tokens.get("color", {}))},
        }
        for name, s in screens.items():
            for key, allowed in token_sets.items():
                for v in s.get(key, []):
                    v = str(v).lower() if key == "colors" else v
                    if v not in allowed:
                        self.fail(f"'{name}'의 {key} 값 {v}가 s4-tokens.json에 없음")

    # ---------- S5 ----------

    def check_s5(self):
        screens = self.load_screens()
        if screens is None:
            return
        allowed = self.rules["allowed"]
        frame = allowed["frame"]
        colors = {c.lower() for c in allowed["colors"]}
        for name, s in screens.items():
            if (s.get("width"), s.get("height")) != (frame["width"], frame["height"]):
                if not self.is_exception(name, "frame", f"{s.get('width')}x{s.get('height')}"):
                    self.fail(f"[가이드] '{name}' 프레임 {s.get('width')}×{s.get('height')} (허용 {frame['width']}×{frame['height']})")
            for key in ("fontSizes", "radii", "spacings"):
                for v in s.get(key, []):
                    if v not in allowed[key] and not self.is_exception(name, key, v):
                        self.fail(f"[가이드] '{name}' {key} {v} 허용 목록 밖")
            for v in s.get("colors", []):
                if str(v).lower() not in colors and not self.is_exception(name, "colors", v):
                    self.fail(f"[가이드] '{name}' 색 {v} 허용 목록 밖")

        for rule in self.rules["must_not_break"]:
            tag = f"[{rule['id']}: {rule['name']}]"
            for screen, words in rule["exact_text"].items():
                texts = [t.strip() for t in screens.get(screen, {}).get("texts", [])]
                for w in words:
                    if w not in texts:
                        self.fail(f"{tag} '{screen}'에 '{w}' 텍스트 없음")
            for screen, words in rule["contains_text"].items():
                joined = "\n".join(screens.get(screen, {}).get("texts", []))
                for w in words:
                    if w not in joined:
                        self.fail(f"{tag} '{screen}'에 '{w}' 없음")
            for w in rule["forbidden_text"]:
                for name, s in screens.items():
                    if any(w in t for t in s.get("texts", [])):
                        self.fail(f"{tag} '{name}'에 금지 문구 '{w}' 있음")

    def run(self):
        self.check_prd_screens()
        self.check_scope()
        getattr(self, f"check_{self.stage}")()
        return self.errors


# ---------- 파싱 도우미 ----------

def split_sections(text):
    """'## 제목' 단위로 나눈다."""
    sections, current = {}, None
    for line in text.splitlines():
        m = re.match(r"##\s+(.+?)\s*$", line)
        if m and not line.startswith("###"):
            current = m.group(1)
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def table_rows(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def table_dicts(text):
    rows = table_rows(text)
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, r)) for r in rows[1:]]


def flatten(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from flatten(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from flatten(v)
    else:
        yield obj


def output_hashes(root, rules):
    """output/ 아래 파일의 해시. state.json은 snapshot이 들어가는 파일이라 뺀다."""
    out = Path(root) / "output"
    skip = {rules["scope"]["state_file"]}
    hashes = {}
    if out.exists():
        for p in sorted(out.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                if rel not in skip:
                    hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = ap.parse_args()
    errors = Gate(args.root, args.stage).run()
    if errors:
        print(f"FAIL {args.stage} ({len(errors)}건)")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print(f"PASS {args.stage}")
    sys.exit(0)


if __name__ == "__main__":
    main()

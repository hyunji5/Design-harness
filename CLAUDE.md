# 공간 행사 캘린더 디자인 하네스

이 파일을 읽은 Claude는 오케스트레이터다. 산출물을 직접 만들지 않고, 에이전트를 부르고 판정 결과를 따른다.

## 참고 문서
- 파이프라인: docs/r3-pipeline.md
- 역할과 편집 범위: docs/r6-roles.md
- 규칙 값(SSOT): rules.json — 통과 조건, 허용 목록, 키워드는 모두 여기에만 있다.
- 입력: docs/prd.md / 판정 기준: docs/story-service.md, docs/design.md

## 단계
| 단계 | 에이전트 | 출력 폴더 | 다음으로 가는 조건 |
|---|---|---|---|
| S1 레퍼런스 | s1-reference | output/s1/ | gate.py --stage s1 통과 |
| S2 화면 설계 | s2-spec | output/s2/ | gate.py --stage s2 통과 |
| S3 키 스크린 시안 | s3-keyscreen | output/s3/ | gate.py --stage s3 통과 + **사람 승인** |
| S4 디자인 시스템·화면 | s4-system | output/s4/ | gate.py --stage s4 통과 |
| S5 가이드 검토 | s5-reviewer | output/s5/ | gate.py --stage s5 통과 → 완료 |

## 한 단계 실행 순서
1. output/state.json에서 다음 단계를 확인한다.
2. `python3 scripts/snapshot.py --stage sN`으로 output/의 파일 목록과 해시를 남긴다.
3. 그 단계의 에이전트를 부른다.
4. `python3 scripts/gate.py --stage sN`을 실행한다.
5. exit 0 → state.json에 통과를 기록하고 다음 단계로 간다.
6. exit 1 → 그 단계의 실패 횟수를 1 올리고, 실패 이유를 그대로 넘겨 같은 에이전트를 다시 부른다 (2번부터 다시).
7. 같은 단계가 3번 실패하면 멈추고 사람에게 실패 이유를 보여주고 묻는다.
8. S3가 통과하면 멈추고 사람의 승인을 기다린다.

### S5가 실패했을 때
S5 실패 이유를 들고 S4로 돌아간다. 실패 횟수는 S4로 센다.
snapshot s4 → s4-system (S5 실패 이유 전달) → gate s4 → snapshot s5 → s5-reviewer → gate s5

### state.json 형식
```json
{ "passed": ["s1", "s2"], "attempts": { "s3": 1 }, "snapshot": { "stage": "s3", "files": {} } }
```
- `passed`, `attempts`는 오케스트레이터가 쓴다. `snapshot`은 snapshot.py만 쓴다.
- 단계가 통과하면 그 단계의 `attempts`를 지운다.
- "S3 다시"처럼 한 단계를 다시 하면, 그 단계와 뒤 단계를 `passed`에서 지운다.

## 사람 승인 (S3 끝, 한 곳)
- 최종 결정자는 디자이너다. 관계자 의견은 디자이너를 통해서만 들어온다.
- "승인: 시안 X" → output/s3/s3-approval.md에 결정자·승인·선택한 시안을 사람이 한 말 그대로 적고 S4로 간다.
- "반려: 이유" → 결정자·반려·반려 이유를 적고, 그 이유를 넘겨 S3를 다시 한다.

## 자연어 트리거
| 말 | 하는 일 |
|---|---|
| "하네스 시작" | S1부터 실행 |
| "이어서 해줘" | state.json을 보고 다음 단계부터 실행 |
| "S1 다시" ~ "S5 다시" | 그 단계만 다시 실행 |
| "승인: 시안 X" / "반려: 이유" | 위의 사람 승인 절차 |
| "검사만 해줘" | 현재 단계에 snapshot이 없으면 snapshot.py를 먼저 실행하고, gate.py만 실행해 결과를 보여줌. state.json의 `passed`·`attempts`는 바꾸지 않음 |

## 오케스트레이터가 쓰는 파일
- output/state.json
- output/s3/s3-approval.md
이 두 파일 말고는 아무것도 쓰거나 고치지 않는다.

## 금지
- rules.json을 고치지 않는다.
- 사람 승인 없이 S4로 넘어가지 않는다.
- gate.py가 실패했는데 통과로 기록하지 않는다. 판정을 직접 하지 않는다.
- 규칙 값을 이 파일이나 에이전트 지시문에 다시 적지 않는다. rules.json만 가리킨다.
- 산출물(레퍼런스, 설계서, Figma 화면)을 직접 만들거나 고치지 않는다.

## 범위 밖
- 개발팀 전달은 하네스가 하지 않는다. S5가 끝나면 전달 묶음 위치만 알려준다.

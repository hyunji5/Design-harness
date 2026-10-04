# R6 역할

## 에이전트와 편집 범위
| 에이전트 | 단계 | 편집 폴더 | Figma 편집 페이지 | 그 밖 |
|---|---|---|---|---|
| s1-reference | S1 | output/s1/ | – | 읽기만 |
| s2-spec | S2 | output/s2/ | – | 읽기만 |
| s3-keyscreen | S3 | output/s3/ (s3-approval.md 제외) | Key Screens | 읽기만 |
| s4-system | S4 | output/s4/ | Tokens, Components, Screens | 읽기만 |
| s5-reviewer | S5 | output/s5/ | – (읽기만) | 읽기만 |

- Figma는 파일 1개를 쓰고, 페이지 단위로 편집 범위를 나눈다.
- 오케스트레이터(CLAUDE.md)가 쓰는 파일: output/state.json, output/s3/s3-approval.md (내가 한 말 그대로 기록)

## 판정자 (읽기 전용)
- scripts/gate.py --stage s1~s5
  - rules.json과 output 파일만 읽는다. 아무 파일도 고치지 않는다.
  - 통과하면 exit 0, 실패하면 exit 1과 이유를 낸다.
- s5-reviewer는 gate.py를 실행해 결과를 output/s5/에만 쓴다. S4 산출물과 rules.json은 고칠 수 없다. (작성자 ≠ 검증자)
- rules.json은 사람만 고친다. 에이전트는 아무도 고칠 수 없다.

## 자연어 트리거
| 말 | 하는 일 |
|---|---|
| "하네스 시작" | S1부터 실행 |
| "이어서 해줘" | state.json을 보고 다음 단계부터 실행 |
| "S3 다시" (S1~S5) | 그 단계만 다시 실행 |
| "승인: 시안 B" / "반려: 이유" | s3-approval.md에 기록하고 S4로 진행 또는 S3 다시 |
| "검사만 해줘" | gate.py로 현재 단계만 판정 |

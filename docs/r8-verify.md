# R8 검증과 리뷰

## 1. 판정 스크립트 시험
- tests/fixtures/에 단계마다 통과 샘플 1개, 실패 샘플 1개를 둔다.
- ★ 규칙 위반 샘플을 따로 둔다.
  - rule1-violation: 가게 신청 심사 화면에 `자동 불합격` 문구가 있음
  - rule2-violation: 행사 상세 화면에 `돈 계산 마감일`이 없음
- tests/run.sh가 모든 샘플을 돌려 기대한 exit 0/1이 나오는지 확인한다.
- 파이썬 표준 라이브러리만 쓴다.

## 2. 편집 막기
- .claude/settings.json: rules.json과 scripts/ 편집 금지
- .claude/agents/*.md: 에이전트마다 쓸 수 있는 도구를 정한다. s5-reviewer는 Edit 도구가 없다.
- 폴더 범위 검사: 오케스트레이터가 단계 시작 때 scripts/snapshot.py로 output/ 파일 목록과 해시를 state.json에 남긴다. gate.py는 그 단계 폴더 밖의 파일이 바뀌었으면 실패로 낸다.
  (Claude Code 설정만으로는 폴더 단위 편집 제한을 완전히 강제하기 어려워서 이 검사를 둔다.)

## 3. 문서 대조 리뷰
CLAUDE.md, 에이전트 파일 5개, rules.json을 만든 뒤 대조표로 확인한다.
| 열 | 내용 |
|---|---|
| 항목 | r3~r7의 결정 하나 |
| 들어간 곳 | 파일과 줄 |
| 상태 | 반영 / 빠짐 / 어긋남 |

## 4. 리허설
- S1~S2만 실제로 돌린다. (uibowl → 레퍼런스 보드·노트 → 화면 설계서 → gate.py 통과 확인)
- S3(Figma)부터는 리허설 결과를 보고 진행 여부를 사람이 정한다.

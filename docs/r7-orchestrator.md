# R7 오케스트레이터

## 누가
CLAUDE.md를 읽은 메인 Claude가 오케스트레이터다.

## 하는 일 / 하지 않는 일
| 하는 일 | 하지 않는 일 |
|---|---|
| 단계 순서대로 에이전트를 부른다 | 산출물(레퍼런스, 설계서, Figma 화면)을 직접 만들거나 고친다 |
| gate.py를 실행하고 결과를 따른다 | 판정을 직접 한다 |
| output/state.json, output/s3/s3-approval.md를 쓴다 | 그 밖의 output 파일을 쓴다 |

## 한 단계 실행 순서
1. state.json에서 다음 단계를 확인한다.
2. 그 단계의 에이전트를 부른다.
3. gate.py --stage sN을 실행한다.
4. exit 0이면 state.json에 기록하고 다음 단계로 간다.
5. exit 1이면 실패 이유를 넘겨 같은 에이전트를 다시 부른다. S5 실패는 s4-system을 부른다. 3번 실패하면 멈추고 사람에게 물어본다.
6. S3가 통과하면 멈추고 사람 승인을 기다린다. 승인 없이 S4로 가지 않는다.

## 금지 사항
- rules.json을 고치지 않는다.
- 사람 승인 없이 S4로 넘어가지 않는다.
- gate.py가 실패했는데 통과로 기록하지 않는다.
- 규칙 값(허용 목록, 키워드)을 CLAUDE.md에 다시 적지 않는다. rules.json만 가리킨다.

## 문서 관리
- docs/r0~r7은 설계 기록으로 보관한다.
- CLAUDE.md는 docs/r3-pipeline.md와 docs/r6-roles.md만 가리킨다.
- rules.json이 만들어지면 r0-context.md와 r5-gates.md의 값 표는 "rules.json 참고"로 바꾼다.

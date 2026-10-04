# R4 산출물

## 단계별 파일 (output/ 아래 단계별 폴더)
| 단계 | 파일 | 내용 |
|---|---|---|
| S1 | s1/s1-reference-board.md | uibowl 화면 링크 목록 |
| S1 | s1/s1-reference-notes.md | 화면별로 가져올 패턴과 버릴 패턴 |
| S2 | s2/s2-screen-spec.md | 화면 5개의 설계서 |
| S3 | s3/s3-key-screens.md | 키 스크린 시안 2~3개의 Figma 링크·프레임 ID |
| S3 | s3/s3-approval.md | 사람 승인/반려 기록과 반려 이유 |
| S4 | s4/s4-tokens.json | 디자인 토큰 |
| S4 | s4/s4-components.md | 컴포넌트 목록 |
| S4 | s4/s4-screens.json | Figma에서 뽑은 화면별 프레임 크기·글자 크기·모서리·간격·색·텍스트 |
| S5 | s5/s5-guide-review.md | 가이드 검토 결과 |

## Figma 결과를 세는 방법
판정 스크립트는 Figma를 직접 열지 않는다. S4가 끝날 때 Figma에서 값을 뽑아 s4-screens.json에 저장하고, 판정 스크립트는 이 JSON만 읽는다.

## 규칙 SSOT
- 파일: rules.json (프로젝트 루트)
- 담는 것: r0-context.md의 390×844 허용 목록, story-service.md의 "어기면 안 되는 것" 2개, 단계별 통과 조건
- 다른 문서는 값을 다시 적지 않고 rules.json을 가리킨다.
- 단계별 통과 조건은 R5에서 정하므로, rules.json은 R5 승인 뒤에 만든다.

## 재개
- output/state.json에 통과한 마지막 단계를 적는다.
- 다시 실행하면 그다음 단계부터 한다.
- git은 쓰지 않는다.

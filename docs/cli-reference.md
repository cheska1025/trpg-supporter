# 명령 레퍼런스

> 모든 명령은 가상환경 내 실행을 가정합니다: `poetry run trpg ...`

## session
- `trpg session new "<title>"`
  새 세션 생성. (고유 session id가 생성되어 로그/내보내기와 매칭됩니다.)
- `trpg session close`
  세션 종료 상태로 표시.

## enc (Encounter)
- `trpg enc start`
  전투 시작(이니시 초기화: round=1, index=0).
- `trpg enc end`
  전투 종료(이니시 상태 파일 제거).

## init (Initiative)
- `trpg init add <name> <value>`
  참가자 추가(내림차순 정렬).
- `trpg init list`
  현재 순서/라운드 표시. `*`가 현재 턴.
- `trpg init next`
  다음 턴으로 진행(리스트를 순환하며 라운드 증가).
- `trpg init delay <name>`
  대상을 보류로 표시(현재 턴이면 즉시 다음으로 진행).
- `trpg init return <name>`
  보류된 대상을 같은 라운드 꼬리로 재진입.

## roll
- `trpg roll "<formula>" [--as <actor>]`
  주사위 굴림. 예: `"2d6+1"`, `"1d20+5"`.
  결과는 시스템 로그(dice 이벤트)로 기록됩니다.

## log
- `trpg log add "<text>" [--scene <name>]`
  내러티브 로그 추가(선택적으로 scene 태그 포함).

## export
- `trpg export <md|json>`
  세션 저널(jsonl)을 읽어 Markdown/JSON으로 내보냅니다.
  Markdown은 `## Rolls / ## Narrative / ## System` 섹션으로 자동 분류됩니다.

## 참고
- 환경 변수 `TRPG_HOME`가 로컬 상태/산출물 루트를 결정합니다.
```powershell
$env:TRPG_HOME = "$env:TEMP\trpg_demo"

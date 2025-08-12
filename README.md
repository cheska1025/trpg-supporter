# TRPG Supporter

TRPG 플레이를 위한 코어 엔진(주사위·이니시·로그), CLI 툴, FastAPI 백엔드, React(Vite) 프론트엔드를 포함한 모노리포 프로젝트입니다.

## 핵심 기능 (MVP)

- **주사위 엔진**: NdM±X 기본 롤, 상세 눈/합계 반환
- **이니시 추적**: 등록/정렬, 턴 진행, 라운드 증가
- **세션 로그**: Markdown 누적 기록 내보내기
- **CLI**: `trpg` 명령으로 롤·이니시·로그 조작
- **백엔드 스캐폴드**: FastAPI + Uvicorn
- **프론트엔드**: Vite + React + TypeScript (별도 `/frontend`)

---

## 저장소 구조

.
├─ backend/ # FastAPI 앱(점진 확장)
│ └─ app/
├─ core/ # 순수 파이썬 코어 모듈
│ ├─ dice/ # 주사위 엔진
│ ├─ initiative/ # 이니시 트래커
│ └─ log/ # 로그 유틸
├─ cli/ # Click 기반 CLI 진입점 (trpg)
├─ frontend/ # Vite + React + TypeScript 앱
├─ migrations/ # Alembic 마이그레이션
├─ tests/ # pytest 스위트
├─ docker-compose.yml # 로컬 통합 실행(선택)
├─ Dockerfile # 백엔드 컨테이너 빌드(선택)
├─ pyproject.toml # Poetry 의존성/스크립트/툴 설정
├─ .pre-commit-config.yaml # 린트/포맷 훅
└─ README.md # (현재 문서)

---

## 요구 사항

- Python 3.12+
- Poetry
- Node.js LTS (프론트엔드 작업 시)
- (선택) Docker / Docker Compose

---

## 빠른 시작

### 1) 의존성 설치

```bash
# Python
poetry install
poetry run pre-commit install

# (선택) 최초 한 번 전체 훅 검사
poetry run pre-commit run -a
---
## 테스트 실행
poetry run pytest -q

---
# 버전
poetry run trpg version

# 주사위
poetry run trpg roll "2d6+3"

# 이니시
poetry run trpg init add Rogue 17
poetry run trpg init next

# 로그
poetry run trpg log --msg "세션 시작"
type .\exports\session.md   # Windows
# 또는
cat ./exports/session.md
---
poetry run uvicorn backend.app.main:app --reload --port 8000
# http://localhost:8000/health
---
cd frontend
npm install
npm run dev
# http://localhost:5173 (기본)
---
# 브랜치 전략
main : 보호 브랜치(릴리스)
develop : 기본 개발 브랜치
feat/, chore/, fix/* : 기능/정리/버그 브랜치 → develop으로 PR
커밋 메시지: Conventional Commits 권장 (feat:, fix:, chore: 등)
---
# 품질 도구
Ruff (린트)
Black (포맷)
Mypy (타입체크)
→ pre-commit 훅으로 자동화
Pytest + pytest-cov (테스트 & 커버리지)
# 명령어 예시
poetry run ruff check .
poetry run black --check .
poetry run mypy .
poetry run pytest --cov
# Docker
docker compose up --build
# 백엔드: http://localhost:8000/health
---
로드맵 (요약)
W1: 코어 엔진 & CLI MVP (완료 진행 중)
W2: CLI 고도화, FastAPI REST/WS 스켈레톤
W3: WS 브로드캐스트, 권한/세션
W4: 프론트 1차(이니시/주사위/로그)
W5: Discord Bot 연동
W6: 안정화/배포(Docker Compose)
---
MIT © cheska1025
```

---
name: add-ext-skill
description: 외부 DMAP 플러그인을 ext-{플러그인명} 스킬로 추가하는 유틸리티
type: utility
user-invocable: true
---

# 외부호출 스킬 추가 유틸리티

[외부 플러그인 연동 추가 시작]

## 목표

외부 DMAP 플러그인(abra, github-release-manager 등)을 이 플러그인에서 호출할 수 있도록
ext-{플러그인명} External 스킬을 자동 생성하여 크로스-플러그인 워크플로우를 구현합니다.

## 활성화 조건

- 사용자가 "외부 플러그인 추가", "플러그인 연동", "/ai-news-digest:add-ext-skill" 요청
- 다른 DMAP 플러그인의 기능을 사용하고 싶을 때
- 에이전트 개발, GitHub 관리 등 전문 기능이 필요할 때

## 워크플로우

### Step 1: DMAP 마켓플레이스에서 플러그인 카탈로그 다운로드
`curl` 명령으로 공개 마켓플레이스에서 사용 가능한 플러그인 목록 다운로드:
```bash
curl -s https://raw.githubusercontent.com/unicorn-plugins/dmap-marketplace/main/catalog.yaml > .dmap/temp/catalog.yaml
```

### Step 2: 사용자에게 추가할 플러그인 선택 → Skill: /oh-my-claudecode:note
- **INTENT**: 다운로드한 카탈로그에서 추가할 플러그인 선택
- **ARGS**: AskUserQuestion으로 플러그인 목록 제시
- **RETURN**: 선택된 플러그인명 반환

카탈로그 파싱 후 선택 옵션 제시:
```
사용 가능한 DMAP 플러그인:
1. abra - AI Agent 자동 생성
2. github-release-manager - GitHub Release 관리
3. math-research - 수학 연구 논문 분석
4. document-processor - 문서 처리 자동화

추가할 플러그인 번호를 선택하세요: [1-4]
```

### Step 3: 선택된 플러그인의 명세서 다운로드
선택된 플러그인의 plugin.json과 README.md 다운로드:
```bash
curl -s https://raw.githubusercontent.com/unicorn-plugins/{플러그인명}/main/.claude-plugin/plugin.json > .dmap/temp/{플러그인명}-plugin.json
curl -s https://raw.githubusercontent.com/unicorn-plugins/{플러그인명}/main/README.md > .dmap/temp/{플러그인명}-README.md
```

### Step 4: 도메인 컨텍스트 수집
플러그인의 기능과 사용법 파악을 위한 컨텍스트 수집:
- plugin.json에서 description, keywords 추출
- README.md에서 주요 기능과 사용 예시 추출
- 사용 가능한 스킬 목록 확인

### Step 5: ext-{플러그인명} External 스킬 생성 → Skill: /oh-my-claudecode:ralph
- **INTENT**: External 유형 표준에 따른 외부호출 스킬 자동 생성
- **ARGS**: 수집된 컨텍스트와 플러그인 정보
- **RETURN**: ext-{플러그인명} 스킬 생성 완료

External 스킬 생성 과정:
1. `skills/ext-{플러그인명}/` 디렉토리 생성
2. External 유형 표준 골격으로 SKILL.md 작성
3. `commands/ext-{플러그인명}.md` 진입점 생성

### Step 6: help 스킬 업데이트 → Skill: /oh-my-claudecode:note
- **INTENT**: help 스킬의 명령어 테이블에 새 외부호출 스킬 추가
- **ARGS**: 생성된 ext-{플러그인명} 정보
- **RETURN**: help 스킬 업데이트 완료

### Step 7: 설치 완료 확인 및 사용법 안내
생성된 외부호출 스킬의 사용법 출력:
```
✅ ext-{플러그인명} 스킬이 추가되었습니다!

사용법:
- /{ai-news-digest}:ext-{플러그인명} [인자]

예시:
- /ai-news-digest:ext-abra "사용자 인증 API 에이전트 만들어줘"
```

## 참고사항

### External 유형 표준 골격

```markdown
---
name: ext-{플러그인명}
description: {플러그인명} 플러그인 외부 호출
type: external
user-invocable: true
---

# {플러그인명} 외부 호출

## 목표

{플러그인명} 플러그인의 워크플로우를 이 플러그인에서 호출하여
크로스-플러그인 기능 연동을 제공합니다.

## 활성화 조건

- {플러그인 주요 기능 설명}

## 워크플로우

### Step 1: 외부 플러그인 호출 → Skill: {플러그인명}:{메인스킬명}
- **INTENT**: {플러그인 목적}
- **ARGS**: 사용자 요청 및 인자 전달
- **RETURN**: {플러그인명} 워크플로우 완료

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| 외부 플러그인 위임 필수 | 모든 작업은 대상 플러그인이 수행 |
| 인자 전달 정확성 | 사용자 입력을 변형 없이 그대로 전달 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 직접 작업 수행 금지 | 외부 플러그인 전담 영역 침범 방지 |

## 검증 체크리스트

- [ ] 대상 플러그인이 정상 설치되어 있는지 확인
- [ ] 외부 호출이 성공적으로 실행되는지 확인
```

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| 마켓플레이스 카탈로그 다운로드 | DMAP 공식 마켓플레이스에서 최신 목록 확인 |
| 사용자 선택 필수 | AskUserQuestion으로 반드시 사용자가 선택 |
| External 유형 표준 준수 | 생성되는 스킬은 External 유형 표준 골격 사용 |
| 명령어 테이블 업데이트 | help 스킬에 새 명령어 정보 추가 |
| 진입점 생성 | commands/ 디렉토리에 슬래시 명령 진입점 생성 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 사용자 확인 없이 자동 추가 금지 | 불필요한 스킬 생성 방지 |
| 기존 ext- 스킬 덮어쓰기 금지 | 사용자 확인 후 업데이트만 허용 |
| 비공식 플러그인 추가 금지 | 공식 마켓플레이스에 등록된 것만 허용 |
| 코어 스킬 이름과 충돌 금지 | setup, help 등 기본 스킬명과 중복 방지 |

## 검증 체크리스트

- [ ] DMAP 마켓플레이스에서 카탈로그가 정상 다운로드되는지 확인
- [ ] AskUserQuestion이 올바른 선택 옵션을 제시하는지 확인
- [ ] 선택된 플러그인의 명세서가 정상 다운로드되는지 확인
- [ ] External 유형 표준에 맞는 스킬이 생성되는지 확인
- [ ] commands/ 진입점이 올바르게 생성되는지 확인
- [ ] help 스킬의 명령어 테이블이 업데이트되는지 확인
- [ ] 생성된 외부호출 스킬이 정상 호출되는지 테스트 확인
- [ ] 임시 파일(.dmap/temp/)이 정리되는지 확인
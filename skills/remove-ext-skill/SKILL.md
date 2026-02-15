---
name: remove-ext-skill
description: 기존 ext-{플러그인명} 외부호출 스킬을 안전하게 제거하는 유틸리티
type: utility
user-invocable: true
---

# 외부호출 스킬 제거 유틸리티

[외부 플러그인 연동 제거 시작]

## 목표

기존에 추가된 ext-{플러그인명} 외부호출 스킬을 안전하게 제거하여
불필요한 연동을 정리하고 플러그인을 경량화합니다.

## 활성화 조건

- 사용자가 "외부 플러그인 제거", "연동 삭제", "/ai-news-digest:remove-ext-skill" 요청
- 사용하지 않는 외부 플러그인 연동을 정리하고 싶을 때
- 플러그인 용량을 줄이거나 관리를 단순화하고 싶을 때

## 워크플로우

### Step 1: 기존 ext-* 스킬 목록 조회
`skills/` 디렉토리에서 ext- 접두사로 시작하는 스킬 디렉토리 탐색:
```bash
find skills/ -type d -name "ext-*" | sort
```

기존 외부호출 스킬이 없는 경우 안내 메시지 출력 후 종료

### Step 2: 제거할 스킬 선택 → Skill: /oh-my-claudecode:note
- **INTENT**: 발견된 외부호출 스킬 중에서 제거할 대상 선택
- **ARGS**: AskUserQuestion으로 스킬 목록 제시
- **RETURN**: 선택된 스킬명 반환

발견된 스킬 목록 제시:
```
발견된 외부호출 스킬:
1. ext-abra - AI Agent 자동 생성 (2024-01-10 추가)
2. ext-github-release-manager - GitHub Release 관리 (2024-01-08 추가)
3. ext-document-processor - 문서 처리 자동화 (2024-01-05 추가)

제거할 스킬 번호를 선택하세요 [1-3]:
(여러 개 선택 시 쉼표로 구분: 1,3)
```

### Step 3: 제거 대상 확인 및 최종 사용자 승인
선택된 스킬의 상세 정보 표시 후 최종 확인:
```bash
# 스킬 사용 내역 확인 (선택적)
grep -r "ext-{선택된플러그인}" skills/ commands/ || true
```

최종 확인 메시지:
```
⚠️ 다음 외부호출 스킬을 영구 제거합니다:
- ext-{플러그인명} (/ai-news-digest:ext-{플러그인명} 명령 포함)

제거된 스킬은 복구할 수 없습니다.
정말로 제거하시겠습니까? [y/N]:
```

### Step 4: ext-{플러그인명} 스킬 디렉토리 삭제 → Skill: /oh-my-claudecode:ralph
- **INTENT**: 선택된 외부호출 스킬 완전 제거
- **ARGS**: 확인된 제거 대상 스킬명
- **RETURN**: 스킬 디렉토리 삭제 완료

삭제 과정:
1. `skills/ext-{플러그인명}/` 디렉토리 전체 삭제
2. 삭제 전 백업 생성 (선택적): `.dmap/backup/ext-{플러그인명}-{날짜}.tar.gz`

### Step 5: commands/ 진입점 삭제
해당하는 슬래시 명령 진입점 제거:
```bash
rm -f commands/ext-{플러그인명}.md
```

### Step 6: help 스킬 업데이트 → Skill: /oh-my-claudecode:note
- **INTENT**: help 스킬의 명령어 테이블에서 제거된 스킬 정보 삭제
- **ARGS**: 제거된 ext-{플러그인명} 정보
- **RETURN**: help 스킬 업데이트 완료

help 스킬의 명령어 테이블에서 해당 행 제거:
```markdown
| `/ai-news-digest:ext-{플러그인명}` | {설명} | {사용예시} |  ← 이 행 삭제
```

### Step 7: 제거 완료 확인 및 정리 보고
제거 결과 요약 출력:
```
✅ ext-{플러그인명} 스킬 제거 완료!

제거된 항목:
- 스킬 디렉토리: skills/ext-{플러그인명}/
- 진입점: commands/ext-{플러그인명}.md
- 명령어: /ai-news-digest:ext-{플러그인명}

백업 파일: .dmap/backup/ext-{플러그인명}-{날짜}.tar.gz (필요시 복원 가능)
```

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| ext- 접두사 스킬만 제거 | setup, help 등 코어 스킬은 제거 대상에서 제외 |
| 사용자 최종 확인 필수 | 삭제 전 반드시 사용자 승인 받기 |
| 백업 생성 권장 | 삭제 전 .dmap/backup/에 아카이브 생성 |
| help 스킬 동기화 | 명령어 테이블에서 제거된 스킬 정보 삭제 |
| 진입점 함께 제거 | commands/ 디렉토리의 관련 파일도 삭제 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 코어 스킬 제거 금지 | setup, help, run-daily-digest 등은 플러그인 필수 기능 |
| 확인 없이 자동 삭제 금지 | 실수로 인한 데이터 손실 방지 |
| 백업 없이 완전 삭제 금지 | 복구 가능성 확보 |
| 시스템 파일 삭제 금지 | .claude-plugin/, runtime-mapping.yaml 등 보호 |
| 한 번에 모든 스킬 삭제 금지 | 사용자가 개별적으로 선택하도록 강제 |

## 검증 체크리스트

- [ ] skills/ 디렉토리에서 ext- 접두사 스킬만 탐색되는지 확인
- [ ] 코어 스킬(setup, help 등)이 제거 대상에 포함되지 않는지 확인
- [ ] AskUserQuestion이 올바른 스킬 목록을 제시하는지 확인
- [ ] 사용자 최종 확인 단계가 포함되어 있는지 확인
- [ ] 스킬 디렉토리가 완전히 삭제되는지 확인
- [ ] commands/ 진입점도 함께 제거되는지 확인
- [ ] help 스킬의 명령어 테이블이 업데이트되는지 확인
- [ ] 백업 파일이 .dmap/backup/에 생성되는지 확인
- [ ] 제거 완료 후 관련 파일이 모두 정리되는지 확인
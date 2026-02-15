---
name: setup
description: AI News Digest 환경 설정 - PostgreSQL 설치, DB 초기화, API 키 설정, cron job 등록
type: utility
user-invocable: true
---

# AI News Digest 환경 설정

[AI News Digest 초기 설정 시작]

## 목표

AI News Digest 플러그인이 정상 작동하도록 필요한 모든 환경을 설정합니다:
- PostgreSQL 데이터베이스 설치 및 초기화
- API 키 설정 (Groq, Gmail SMTP)
- 수신자 목록 설정
- 매일 오전 8시 자동 실행을 위한 cron job 등록

## 활성화 조건

- 사용자가 "AI News Digest 설정", "/ai-news-digest:setup" 요청
- 플러그인 최초 설치 후 초기 설정 필요 시
- 설정 파일이 누락되었거나 데이터베이스 연결 실패 시

## 워크플로우

### Step 1: PostgreSQL 설치 확인 및 자동 설치
`/oh-my-claudecode:ralph`을 활용하여 완료 보장:
- macOS: `brew install postgresql@14 && brew services start postgresql@14`
- Linux: `sudo apt-get update && sudo apt-get install postgresql postgresql-contrib && sudo systemctl start postgresql`
- 기존 설치 확인: `psql --version` 실행으로 설치 여부 검사
- PostgreSQL 서비스 시작 확인

### Step 2: 데이터베이스 생성 및 테이블 스키마 초기화
`/oh-my-claudecode:ralph`을 활용하여 DB 작업 완료 보장:
- 데이터베이스 `ai_news` 생성 (존재하지 않는 경우)
- 3개 테이블 스키마 생성: `news_items`, `newsletters`, `error_logs`
- 인덱스 생성: `news_items.url` (UNIQUE), `news_items.published_at`
- 권한 설정 확인

### Step 3: API 키 설정 → Skill: /oh-my-claudecode:note
- **INTENT**: Groq API 키를 안전하게 저장
- **ARGS**: 사용자로부터 Groq API 키 입력 받기
- **RETURN**: `.dmap/secrets/groq.yaml` 파일 생성 완료

사용자에게 안내 메시지:
```
Groq API 키를 입력해주세요 (https://console.groq.com/keys):
API 키: [사용자 입력]
모델: llama-3.1-8b-instant (기본값)
```

### Step 4: Gmail SMTP 설정 → Skill: /oh-my-claudecode:note
- **INTENT**: Gmail SMTP 설정을 안전하게 저장
- **ARGS**: 사용자로부터 Gmail 계정 및 앱 비밀번호 입력 받기
- **RETURN**: `.dmap/secrets/gmail.yaml` 파일 생성 완료

사용자에게 안내 메시지:
```
Gmail SMTP 설정을 입력해주세요:
이메일: [사용자 입력]
앱 비밀번호: [사용자 입력] (Gmail 2단계 인증 → 앱 비밀번호 생성)
```

### Step 5: 수신자 목록 설정 → Skill: /oh-my-claudecode:note
- **INTENT**: 뉴스레터 수신자와 관리자 정보 저장
- **ARGS**: 수신자 이메일 목록과 관리자 이메일 입력 받기
- **RETURN**: `.dmap/config/recipients.yaml` 파일 생성 완료

사용자에게 안내 메시지:
```
뉴스레터 수신자를 설정해주세요:
1. 수신자 이메일 (쉼표로 구분): user1@example.com, user2@example.com
2. 관리자 이메일 (에러 알림용): admin@example.com
```

### Step 6: cron job 등록 → Skill: /oh-my-claudecode:ralph
- **INTENT**: 매일 오전 8시 자동 실행 등록
- **ARGS**: crontab 등록 명령 실행
- **RETURN**: cron job 등록 완료 확인

cron 설정:
```bash
# AI News Digest 자동 실행 (매일 오전 8시)
0 8 * * * cd /Users/dreamondal/workspace/dmap && /ai-news-digest:run-daily-digest
```

### Step 7: 설정 완료 확인 및 테스트
- 모든 설정 파일 존재 확인
- PostgreSQL 연결 테스트
- Groq API 키 유효성 테스트 (간단한 요청)
- Gmail SMTP 인증 테스트
- 설정 완료 메시지 출력

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| PostgreSQL 설치 우선 확인 | 이미 설치되어 있으면 DB 생성만 수행, 설치 스킵 |
| 설정 파일 보안 저장 | API 키, SMTP 비밀번호는 `.dmap/secrets/` 디렉토리에 저장 |
| 디렉토리 자동 생성 | `.dmap/secrets/`, `.dmap/config/` 디렉토리가 없으면 생성 |
| 기존 설정 보존 | 기존 설정 파일이 있으면 덮어쓰기 전에 사용자 확인 |
| 테이블 스키마 정확성 | PostgreSQL 테이블 스키마는 requirements.md의 명세와 정확히 일치 |
| cron job 중복 방지 | 동일한 cron job이 이미 등록되어 있으면 업데이트만 수행 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 평문으로 비밀번호 저장 금지 | 보안상 민감 정보는 `.dmap/secrets/`에 YAML 형태로 저장 |
| 사용자 확인 없이 기존 DB 삭제 금지 | 데이터 손실 방지 |
| 설정 파일을 Git에 커밋 금지 | `.gitignore`에 `.dmap/secrets/` 추가되어 있음 |
| root 권한 없이 시스템 설정 변경 금지 | 일반 사용자 권한으로 해결 가능한 방법 사용 |
| 실패 시 중단하지 말고 계속 진행 | 한 단계 실패해도 다른 설정은 계속 진행 |

## 검증 체크리스트

- [ ] PostgreSQL이 정상 설치되고 서비스가 실행 중인지 확인
- [ ] `ai_news` 데이터베이스와 3개 테이블이 생성되었는지 확인
- [ ] `.dmap/secrets/groq.yaml` 파일이 올바른 형식으로 생성되었는지 확인
- [ ] `.dmap/secrets/gmail.yaml` 파일이 올바른 형식으로 생성되었는지 확인
- [ ] `.dmap/config/recipients.yaml` 파일이 올바른 형식으로 생성되었는지 확인
- [ ] cron job이 정상 등록되었는지 `crontab -l`로 확인
- [ ] PostgreSQL 연결 테스트가 성공했는지 확인
- [ ] Groq API 키로 간단한 요청이 성공했는지 확인
- [ ] Gmail SMTP 인증이 성공했는지 확인
- [ ] 모든 디렉토리가 올바른 권한으로 생성되었는지 확인
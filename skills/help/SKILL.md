---
name: help
description: AI News Digest 사용 안내 - 명령어 목록 및 설정 가이드
type: utility
user-invocable: true
---

# AI News Digest 사용 안내

## 목표

AI News Digest 플러그인의 사용법을 즉시 출력하여 사용자가 빠르게 기능을 파악할 수 있도록 합니다.

## 활성화 조건

- 사용자가 "도움말", "사용법", "/ai-news-digest:help" 요청
- 플러그인 명령어를 모를 때
- 설정 방법이나 트러블슈팅 정보가 필요할 때

## 워크플로우

즉시 출력 방식 (에이전트 위임 없음):

### 1. 사용 가능한 명령어 목록 출력

| 명령 | 설명 | 사용 예시 |
|------|------|-----------|
| `/ai-news-digest:setup` | 초기 환경 설정 (PostgreSQL, API 키, 수신자 등) | 플러그인 설치 후 최초 1회 실행 |
| `/ai-news-digest:run-daily-digest` | AI 뉴스레터 발행 (메인 기능) | 수동 실행 또는 cron으로 자동 실행 |
| `/ai-news-digest:help` | 사용 안내 (현재 명령) | 도움이 필요할 때 언제든지 |
| `/ai-news-digest:add-ext-skill` | 외부 플러그인 연동 추가 | 다른 DMAP 플러그인 연동 시 |
| `/ai-news-digest:remove-ext-skill` | 외부 플러그인 연동 제거 | 불필요한 연동 제거 시 |

### 2. 설정 파일 경로 안내

**비밀 정보 (직접 수정하지 마세요)**:
- `.dmap/secrets/groq.yaml` - Groq API 키 설정
- `.dmap/secrets/gmail.yaml` - Gmail SMTP 설정

**일반 설정 (필요시 수정 가능)**:
- `.dmap/config/recipients.yaml` - 뉴스레터 수신자 목록
- `.dmap/config/db.yaml` - PostgreSQL 연결 설정

**출력 파일**:
- `output/` 디렉토리 - 생성된 뉴스레터 HTML 파일

### 3. 빠른 시작 가이드

**처음 사용하는 경우**:
1. `/ai-news-digest:setup` - 초기 설정
2. `/ai-news-digest:run-daily-digest` - 뉴스레터 발행 테스트

**정기 사용**:
- cron job이 매일 오전 8시에 자동 실행
- 수동 실행: `/ai-news-digest:run-daily-digest`

### 4. 트러블슈팅 가이드

| 문제 | 해결 방법 |
|------|----------|
| PostgreSQL 연결 실패 | `brew services restart postgresql@14` (macOS) 또는 `sudo systemctl restart postgresql` (Linux) |
| Groq API 오류 | API 키 유효성 확인, 요청 한도 확인 |
| 이메일 발송 실패 | Gmail 앱 비밀번호 재생성, SMTP 설정 확인 |
| cron job 미실행 | `crontab -l`로 등록 확인, 절대 경로 확인 |
| 중복 뉴스 수집 | RSS 피드 응답 지연, 다음 실행에서 자동 해결 |

### 5. 데이터 소스 정보

**수집 중인 RSS 피드**:
- **연구 트렌드**: arxiv.org (cs.AI, cs.LG)
- **빅테크 트렌드**: Anthropic Blog, Google AI Blog, OpenAI Blog
- **산업 뉴스**: TechCrunch, VentureBeat, Hugging Face
- **개발 실무**: LangChain Blog, InfoQ

### 6. 지원 정보

**문의 및 버그 리포트**:
- GitHub: https://github.com/unicorn-plugins/ai-news-digest
- 개발사: 유니콘주식회사
- 라이선스: MIT

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| 즉시 출력 방식 | 에이전트에 위임하지 않고 바로 도움말 텍스트 출력 |
| 명령어 테이블 최신 유지 | 모든 스킬에 대응하는 명령어 포함 |
| 경로 정보 정확성 | 실제 파일 경로와 일치하는 정보 제공 |
| 트러블슈팅 실용성 | 실제 발생 가능한 문제와 검증된 해결책만 포함 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 에이전트 위임 금지 | 즉시 출력이 목적이므로 Agent 호출 불필요 |
| 설정 파일 내용 노출 금지 | API 키 등 민감 정보 보안상 표시하지 않음 |
| 과도한 기술적 세부사항 금지 | 사용자 친화적인 안내에 집중 |
| 구버전 정보 포함 금지 | 최신 버전의 명령어와 경로만 안내 |

## 검증 체크리스트

- [ ] 모든 스킬이 명령어 테이블에 포함되어 있는지 확인
- [ ] 파일 경로가 실제 디렉토리 구조와 일치하는지 확인
- [ ] 트러블슈팅 가이드의 해결책이 검증되었는지 확인
- [ ] RSS 피드 목록이 requirements.md와 일치하는지 확인
- [ ] 연락처 정보가 정확한지 확인
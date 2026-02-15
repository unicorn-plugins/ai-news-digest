---
name: run-daily-digest
description: AI 뉴스레터 발행 (메인 기능) - RSS 수집부터 이메일 발송까지 전체 워크플로우 실행
type: orchestrator
user-invocable: true
---

# AI 뉴스레터 발행

[AI News Digest 뉴스레터 발행 시작]

## 목표

9개 RSS 피드에서 AI 관련 최신 뉴스를 수집하여 중복 제거, 요약, 번역 후
HTML 뉴스레터를 생성하고 수신자에게 이메일로 발송하는 전체 워크플로우를 실행함.

## 활성화 조건

- 사용자가 "뉴스레터 발행", "AI 뉴스 다이제스트 실행", "/ai-news-digest:run-daily-digest" 요청
- cron job에 의한 매일 오전 8시 자동 실행
- 수동으로 뉴스레터 발행이 필요한 경우

## 워크플로우

`/oh-my-claudecode:ralph`을 활용하여 완료 보장.
각 Phase별 에러 발생 시 최대 3회 재시도(exponential backoff) 후 다음 Phase로 진행.

### Phase 1: RSS 뉴스 수집 → Agent: collector

- **TASK**: 9개 RSS 피드에서 24시간 이내 AI 관련 뉴스 수집
- **EXPECTED OUTCOME**: 수집된 뉴스 항목 목록 (제목, URL, 요약, 출처, 발행일)
- **MUST DO**: 모든 피드 순회, 24시간 필터링, 결과를 `output/collected-news.json`에 저장
- **MUST NOT DO**: 콘텐츠 요약이나 번역 수행
- **CONTEXT**: `.dmap/config/rss-feeds.yaml`에서 피드 목록 로드

### Phase 2: 콘텐츠 처리 → Agent: content-processor

- **TASK**: 수집된 뉴스에서 중복 제거 후 Groq API로 요약 및 한국어 번역
- **EXPECTED OUTCOME**: 중복 제거되고 요약·번역된 뉴스 항목 목록
- **MUST DO**: URL 기반 중복 제거, Groq API 요약, 한국어 번역, 결과를 `output/processed-news.json`에 저장
- **MUST NOT DO**: RSS 수집이나 DB 저장
- **CONTEXT**: `output/collected-news.json` 입력, `.dmap/secrets/groq.yaml`에서 API 키 로드

### Phase 3: 데이터 저장 → Agent: data-manager

- **TASK**: 처리된 뉴스 항목을 PostgreSQL에 저장
- **EXPECTED OUTCOME**: 모든 뉴스 항목이 DB `news_items` 테이블에 저장됨
- **MUST DO**: DB 연결, 중복 체크(URL 기준), INSERT 실행, 저장 건수 보고
- **MUST NOT DO**: 콘텐츠 수정이나 뉴스레터 생성
- **CONTEXT**: `output/processed-news.json` 입력, `.dmap/secrets/database.yaml`에서 연결 정보 로드

### Phase 4: 뉴스레터 생성 → Agent: newsletter-publisher

- **TASK**: 저장된 뉴스 데이터로 HTML 뉴스레터 생성
- **EXPECTED OUTCOME**: `output/newsletter.html` 파일 생성
- **MUST DO**: 카테고리별 그룹화, HTML 템플릿 적용, 반응형 이메일 포맷
- **MUST NOT DO**: 이메일 발송
- **CONTEXT**: `output/processed-news.json` 또는 DB에서 당일 뉴스 조회

### Phase 5: 이메일 발송 → Agent: newsletter-publisher

- **TASK**: 생성된 HTML 뉴스레터를 Gmail SMTP로 수신자에게 발송
- **EXPECTED OUTCOME**: 모든 수신자에게 이메일 발송 완료
- **MUST DO**: 수신자 목록 로드, SMTP 연결, 발송, 발송 결과 보고
- **MUST NOT DO**: 뉴스레터 내용 수정
- **CONTEXT**: `output/newsletter.html` 입력, `.dmap/secrets/gmail.yaml` 및 `.dmap/config/recipients.yaml` 로드

### Phase 6: 발행 기록 저장 → Agent: data-manager

- **TASK**: 뉴스레터 발행 기록을 PostgreSQL `newsletters` 테이블에 저장
- **EXPECTED OUTCOME**: 발행 일시, 뉴스 수, 수신자 수 등 메타데이터 저장 완료
- **MUST DO**: 발행 기록 INSERT, 성공/실패 상태 기록
- **MUST NOT DO**: 이메일 재발송
- **CONTEXT**: Phase 1~5 실행 결과 데이터

## 에이전트 호출 규칙

**에이전트 FQN 목록**:
- `ai-news-digest:collector:collector` (MEDIUM 티어)
- `ai-news-digest:content-processor:content-processor` (MEDIUM 티어)
- `ai-news-digest:data-manager:data-manager` (LOW 티어)
- `ai-news-digest:newsletter-publisher:newsletter-publisher` (LOW 티어)

**프롬프트 조립 절차**:
1. `agents/{agent-name}/` 에서 3파일 로드: AGENT.md + agentcard.yaml + tools.yaml
2. `runtime-mapping.yaml` 참조하여 구체화:
   - **모델 구체화**: agentcard.yaml의 `tier` → `tiers` 매핑에서 모델 결정
   - **툴 구체화**: tools.yaml의 추상 도구 → `tools` 매핑에서 실제 도구 결정
   - **금지액션 구체화**: agentcard.yaml의 `forbidden_actions` → `forbidden_actions` 매핑에서 제외할 도구 결정
   - **최종 도구** = (구체화된 도구) - (제외 도구)
3. 3파일을 합쳐 하나의 프롬프트로 조립
4. **프롬프트 구성 순서**: 공통 정적(runtime-mapping) → 에이전트별 정적(3파일) → 동적(작업 지시)
5. `Task(subagent_type=FQN, model=구체화된모델, prompt=조립된프롬프트)` 호출

**오케스트레이션 스킬 활용**:
- **전체 워크플로우**: `/oh-my-claudecode:ralph` (완료 보장 실행 워크플로우)
- **에러 처리**: 각 Phase별 최대 3회 재시도 (exponential backoff)
- **에러 알림**: 재시도 실패 시 data-manager로 에러 로그 저장 후 newsletter-publisher로 관리자 알림 발송

## 완료 조건

- 6개 Phase가 모두 성공적으로 실행됨
- 뉴스레터가 모든 수신자에게 발송됨
- 발행 기록이 DB에 저장됨

## 검증 프로토콜

스킬 완료 전 다음 항목 검증:
- `output/collected-news.json` 파일 존재 및 뉴스 항목 1개 이상
- `output/processed-news.json` 파일 존재 및 요약·번역 완료
- `output/newsletter.html` 파일 존재
- DB `news_items` 테이블에 당일 데이터 존재
- DB `newsletters` 테이블에 발행 기록 존재

## 상태 정리

완료 시 `.omc/state/ralph-state.json` 삭제.

## 취소

사용자가 취소 시 현재 Phase까지의 결과를 보고하고, 이후 Phase는 스킵.
부분 실행 결과는 `output/` 디렉토리에 보존됨.

## 재개

취소된 워크플로우 재개 시 `output/` 디렉토리의 중간 결과를 확인하여
완료된 Phase는 스킵하고 미완료 Phase부터 재개.

## 출력 형식

### 성공 시
```
AI 뉴스레터 발행 완료

수집 결과:
- 총 수집 뉴스: {수집된_뉴스_수}개
- 중복 제거 후: {중복_제거_후_수}개
- 카테고리별 분포: 연구 {연구_수}개, 빅테크 {빅테크_수}개, 산업 {산업_수}개, 개발 {개발_수}개

발송 결과:
- 수신자 수: {수신자_수}명
- 발송 시각: {발송_시각}
```

### 실패 시
```
AI 뉴스레터 발행 실패

실패 단계: Phase {N} - {단계명}
에러 메시지: {에러_메시지}
재시도 횟수: {재시도_횟수}/3

관리자에게 에러 알림 발송 완료
```

## MUST 규칙

| 규칙 | 설명 |
|------|------|
| 6단계 워크플로우 순차 실행 | 수집→처리→저장→생성→발송→기록 순서 엄격 준수 |
| 에러 발생 시 재시도 로직 적용 | DB 연결 실패, API 오류 시 최대 3회 재시도 |
| 에러 발생 시 관리자 알림 필수 | 재시도 실패 시 data-manager로 에러 로그 저장 후 알림 |
| 성공/실패 명확한 결과 보고 | 각 단계별 상태와 최종 결과를 구체적으로 출력 |
| 각 Phase에 적절한 에이전트 호출 | 에이전트 FQN과 프롬프트 조립 절차 준수 |

## MUST NOT 규칙

| 금지 사항 | 이유 |
|----------|------|
| 스킬이 직접 RSS 수집 금지 | collector 에이전트가 전담, 역할 분리 원칙 |
| 스킬이 직접 DB 조작 금지 | data-manager 에이전트가 전담 |
| 스킬이 직접 API 호출 금지 | content-processor 에이전트가 전담 |
| 에러 발생 시 워크플로우 중단 금지 | 가능한 단계까지 진행 후 결과 보고 |
| 설정 파일 직접 수정 금지 | 읽기 전용으로 설정 확인만 수행 |

## 검증 체크리스트

- [ ] 6단계 워크플로우가 순서대로 실행되는지 확인
- [ ] 각 에이전트가 올바른 FQN으로 호출되는지 확인
- [ ] 에러 발생 시 재시도 로직이 작동하는지 확인
- [ ] 에러 로그가 PostgreSQL에 저장되는지 확인
- [ ] 관리자에게 에러 알림 이메일이 발송되는지 확인
- [ ] 최종 결과가 명확하고 구체적으로 보고되는지 확인
- [ ] 뉴스레터 발행 기록이 데이터베이스에 저장되는지 확인
- [ ] 모든 에이전트가 runtime-mapping.yaml에 올바르게 매핑되는지 확인
